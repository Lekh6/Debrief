import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta

import httpx

from app.core.config import get_settings
from app.models.entities import Employee
from app.schemas.projects import ExtractedTask, TaskConfidence


@dataclass
class ExtractionContext:
    closing_transcript: str
    meeting_transcript: str
    employees: list[Employee]


class ExtractionService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def extract(self, context: ExtractionContext) -> tuple[list[str], list[ExtractedTask], str]:
        if self.settings.gemini_api_key and not self.settings.use_heuristic_extractor:
            summary, tasks = await self._extract_with_gemini(context)
            return summary, tasks, "gemini"

        return self._build_heuristic_summary(context), self._extract_heuristically(context), "heuristic"

    async def _extract_with_gemini(self, context: ExtractionContext) -> tuple[list[str], list[ExtractedTask]]:
        employee_lines = [
            f"- {employee.name} | team={employee.team} | jira_account={employee.jira_account_id or 'unknown'}"
            for employee in context.employees
        ]
        current_date = datetime.utcnow().date().isoformat()
        prompt = f"""
System instructions:
You extract post-meeting action items and a host-facing meeting summary into JSON.
The current meeting date is {current_date}.
Use the closing transcript as the source of truth.
Use the meeting transcript only to fill missing details.
Only include actionable tasks that should become work items.
Meeting summary rules:
- Return n concise bullet-style lines in a top-level "meeting_summary" array.
- Choose n based on meeting complexity. Around 5 lines is generous for a 150-word meeting.
- Include only explicit work points and final decisions taken by the host or agreed in the meeting.
- Do not include dilemmas, open questions, or half-made decisions.
- Prefer lines like "Rahul Mehta to finish the landing page by Monday" or "No clear owner for database work".
- If a person's name appears with a task, usually treat that person as the assignee.
- If assignment is implied but not fully clear, still connect the task to that person but mark the assignee confidence as medium.
- Convert common talk such as "next Monday" or "this Friday" into exact ISO dates using the current meeting date.
Return valid JSON matching the provided schema.

Project employees:
{chr(10).join(employee_lines) or "- none supplied"}

Closing transcript:
{context.closing_transcript}

Meeting transcript:
{context.meeting_transcript}

Return JSON in this shape:
{{
  "meeting_summary": ["string"],
  "tasks": [
    {{
      "title": "string",
      "description": "string",
      "assignee": "employee name or null",
      "deadline": "YYYY-MM-DD or null",
      "confidence": {{
        "title": "high|medium|low",
        "description": "high|medium|low",
        "assignee": "high|medium|low",
        "deadline": "high|medium|low"
      }},
      "confidence_reasons": {{
        "title": "optional reason",
        "description": "optional reason",
        "assignee": "optional reason",
        "deadline": "optional reason"
      }}
    }}
  ]
}}
""".strip()

        parsed = None
        last_error: Exception | None = None
        repair_instruction = ""

        for _attempt in range(3):
            try:
                content = await self._call_gemini_api(prompt, repair_instruction)
                parsed = self._parse_json_response(content)
                break
            except (json.JSONDecodeError, KeyError, TypeError, httpx.HTTPError) as exc:
                last_error = exc
                repair_instruction = (
                    "Your previous response was not valid for the required schema. "
                    "Return only valid JSON matching the requested shape with no prose and no markdown fences."
                )

        if parsed is None:
            raise RuntimeError(f"Gemini extraction failed after retries: {last_error}")

        summary = [str(item).strip() for item in parsed.get("meeting_summary", []) if str(item).strip()]
        tasks = [self._to_task(item, context.employees) for item in parsed.get("tasks", [])]
        return summary[:5], tasks

    async def _call_gemini_api(self, prompt: str, repair_instruction: str) -> str:
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": f"{prompt}\n\n{repair_instruction}".strip(),
                        }
                    ],
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseJsonSchema": {
                    "type": "object",
                    "properties": {
                        "meeting_summary": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "tasks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "description": {"type": "string"},
                                    "assignee": {"type": ["string", "null"]},
                                    "deadline": {"type": ["string", "null"]},
                                    "confidence": {
                                        "type": "object",
                                        "properties": {
                                            "title": {"type": "string"},
                                            "description": {"type": "string"},
                                            "assignee": {"type": "string"},
                                            "deadline": {"type": "string"},
                                        },
                                        "required": ["title", "description", "assignee", "deadline"],
                                    },
                                    "confidence_reasons": {
                                        "type": "object",
                                        "additionalProperties": {"type": "string"},
                                    },
                                },
                                "required": [
                                    "title",
                                    "description",
                                    "assignee",
                                    "deadline",
                                    "confidence",
                                    "confidence_reasons",
                                ],
                            },
                        }
                    },
                    "required": ["meeting_summary", "tasks"],
                },
            },
        }
        endpoint = (
            f"{self.settings.gemini_base_url.rstrip('/')}/models/"
            f"{self.settings.gemini_model}:generateContent?key={self.settings.gemini_api_key}"
        )
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(endpoint, headers={"Content-Type": "application/json"}, json=payload)
            response.raise_for_status()
            data = response.json()

        return data["candidates"][0]["content"]["parts"][0]["text"]

    def _parse_json_response(self, content: str) -> dict:
        stripped = content.strip()
        if stripped.startswith("```"):
            stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
            stripped = re.sub(r"\s*```$", "", stripped)
        return json.loads(stripped)

    def _extract_heuristically(self, context: ExtractionContext) -> list[ExtractedTask]:
        segments = self._split_action_segments(context.closing_transcript)
        if not segments:
            segments = self._split_action_segments(context.meeting_transcript)

        tasks: list[ExtractedTask] = []
        for segment in segments:
            assignee = self._match_employee(segment, context.employees)
            title = self._derive_title(segment, assignee.name if assignee else None)
            if not title:
                continue

            due_date, due_confidence, due_reason = self._parse_deadline(segment)
            description = self._derive_description(segment, context.meeting_transcript)
            confidence = TaskConfidence(
                title="high" if len(segment.split()) > 2 else "medium",
                description="medium" if description else "low",
                assignee="high" if assignee else "low",
                deadline=due_confidence,
            )
            reasons: dict[str, str] = {}
            if not assignee:
                reasons["assignee"] = "No employee matched confidently from the provided directory."
            if due_reason:
                reasons["deadline"] = due_reason
            if description and description != segment.strip():
                reasons["description"] = "Description condensed from the extracted action statement."

            tasks.append(
                ExtractedTask(
                    title=title,
                    description=description or segment.strip(),
                    assignee=assignee.name if assignee else None,
                    assignee_id=assignee.employee_id if assignee else None,
                    deadline=due_date,
                    confidence=confidence,
                    confidence_reasons=reasons,
                )
            )

        return tasks

    def _build_heuristic_summary(self, context: ExtractionContext) -> list[str]:
        segments = self._split_action_segments(context.closing_transcript or context.meeting_transcript)
        summary: list[str] = []
        for segment in segments:
            assignee = self._match_employee(segment, context.employees)
            deadline, _, _ = self._parse_deadline(segment)
            cleaned = " ".join(segment.strip().split())
            if assignee and assignee.name.lower() not in cleaned.lower():
                cleaned = f"{assignee.name} to {cleaned[0].lower() + cleaned[1:]}"
            if deadline and deadline.isoformat() not in cleaned:
                cleaned = f"{cleaned} ({deadline.isoformat()})"
            summary.append(cleaned)
            if len(summary) == 5:
                break
        return summary

    def _to_task(self, item: dict, employees: list[Employee]) -> ExtractedTask:
        assignee_name = item.get("assignee")
        assignee = self._match_employee(assignee_name or "", employees) if assignee_name else None
        deadline_value = item.get("deadline")
        parsed_deadline = None
        if deadline_value:
            try:
                parsed_deadline = date.fromisoformat(deadline_value)
            except ValueError:
                parsed_deadline = None

        return ExtractedTask(
            title=item.get("title", ""),
            description=item.get("description", ""),
            assignee=assignee.name if assignee else assignee_name,
            assignee_id=assignee.employee_id if assignee else None,
            deadline=parsed_deadline,
            confidence=TaskConfidence(**item.get("confidence", {})),
            confidence_reasons=item.get("confidence_reasons", {}),
        )

    def _split_action_segments(self, transcript: str) -> list[str]:
        cleaned = transcript.replace("\r", "\n")
        parts = re.split(r"[\n\.]+", cleaned)
        keywords = ("will", "needs to", "should", "by ", "before ", "action", "follow up", "owner")
        return [part.strip(" -•\t") for part in parts if any(word in part.lower() for word in keywords) and part.strip()]

    def _match_employee(self, text: str, employees: list[Employee]) -> Employee | None:
        lowered = text.lower()
        matches = [employee for employee in employees if employee.name.lower() in lowered]
        if len(matches) == 1:
            return matches[0]

        first_name_matches = [
            employee
            for employee in employees
            if employee.name.split()[0].lower() in lowered
        ]
        if len(first_name_matches) == 1:
            return first_name_matches[0]
        return None

    def _derive_title(self, segment: str, assignee_name: str | None) -> str:
        title = segment.strip()
        if assignee_name:
            title = re.sub(re.escape(assignee_name), "", title, flags=re.IGNORECASE).strip(" ,:-")
        title = re.sub(r"\b(will|should|needs to|owner)\b", "", title, flags=re.IGNORECASE)
        title = re.sub(r"\b(by|before)\b.+$", "", title, flags=re.IGNORECASE).strip(" ,:-")
        return title[:120].strip().capitalize()

    def _derive_description(self, segment: str, meeting_transcript: str) -> str:
        sentence = segment.strip()
        if len(sentence) >= 24:
            return sentence

        for line in re.split(r"[\n\.]+", meeting_transcript):
            if sentence and sentence.lower() in line.lower():
                return line.strip()
        return sentence

    def _parse_deadline(self, segment: str) -> tuple[date | None, str, str | None]:
        today = datetime.utcnow().date()
        lowered = segment.lower()
        weekdays = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6,
        }
        for label, weekday in weekdays.items():
            if f"next {label}" in lowered:
                return self._next_weekday(today + timedelta(days=7), weekday), "medium", f"Derived from relative reference 'next {label}'."
            if f"this {label}" in lowered:
                return self._next_weekday(today, weekday), "medium", f"Derived from relative reference 'this {label}'."
            if label in lowered:
                return self._next_weekday(today, weekday), "medium", f"Derived from weekday reference '{label}'."

        if "tomorrow" in lowered:
            return today + timedelta(days=1), "medium", "Derived from relative reference 'tomorrow'."
        if "next week" in lowered:
            return today + timedelta(days=7), "low", "Derived from broad reference 'next week'."

        explicit_date = re.search(r"(20\d{2}-\d{2}-\d{2})", segment)
        if explicit_date:
            return date.fromisoformat(explicit_date.group(1)), "high", "Explicit ISO date stated in the transcript."

        return None, "low", None

    def _next_weekday(self, current: date, target_weekday: int) -> date:
        delta = (target_weekday - current.weekday()) % 7
        return current if delta == 0 else current + timedelta(days=delta)
