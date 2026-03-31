from collections import defaultdict

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.entities import Employee, Meeting, Project, Task
from app.schemas.meetings import ExtractionResponse, MemberTaskGroup, TeamTaskGroup
from app.schemas.projects import EmployeeRead
from app.services.providers.extraction import ExtractionContext, ExtractionService
from app.services.providers.transcription import TranscriptionService


class MeetingPipeline:
    def __init__(self) -> None:
        self.transcription_service = TranscriptionService()
        self.extraction_service = ExtractionService()

    async def extract_tasks(
        self,
        db: Session,
        project: Project,
        meeting_transcript: str | None,
        closing_transcript: str | None,
        meeting_audio: UploadFile | None,
        closing_audio: UploadFile | None,
    ) -> ExtractionResponse:
        resolved_meeting_transcript = await self._resolve_transcript(meeting_transcript, meeting_audio)
        resolved_closing_transcript = await self._resolve_transcript(closing_transcript, closing_audio)

        meeting_summary, extracted_tasks, extraction_mode = await self.extraction_service.extract(
            ExtractionContext(
                closing_transcript=resolved_closing_transcript,
                meeting_transcript=resolved_meeting_transcript,
                employees=project.employees,
            )
        )

        meeting = Meeting(
            project_id=project.project_id,
            meeting_transcript=resolved_meeting_transcript,
            closing_transcript=resolved_closing_transcript,
            status="pending",
        )
        db.add(meeting)
        db.flush()

        for task in extracted_tasks:
            db.add(
                Task(
                    meeting_id=meeting.meeting_id,
                    title=task.title or "Untitled task",
                    description=task.description or "",
                    assignee_id=task.assignee_id,
                    deadline=task.deadline,
                    confidence=task.confidence.model_dump(),
                    confidence_reasons=task.confidence_reasons,
                    status="draft",
                )
            )

        db.commit()
        db.refresh(meeting)

        return ExtractionResponse(
            meeting_id=meeting.meeting_id,
            project_id=project.project_id,
            project_name=project.name,
            meeting_transcript=resolved_meeting_transcript,
            closing_transcript=resolved_closing_transcript,
            meeting_summary=meeting_summary or self._build_meeting_summary(resolved_closing_transcript, resolved_meeting_transcript),
            tasks=extracted_tasks,
            extraction_mode=extraction_mode,
            employees=[EmployeeRead.model_validate(employee) for employee in project.employees],
            team_groups=self._build_team_groups(extracted_tasks, project.employees),
        )

    async def _resolve_transcript(self, transcript: str | None, audio: UploadFile | None) -> str:
        if transcript and transcript.strip():
            return transcript.strip()

        if audio is None:
            raise ValueError("A transcript or an audio file is required for both meeting and closing inputs.")

        result = await self.transcription_service.transcribe_upload(audio)
        return result.transcript

    def _build_meeting_summary(self, closing_transcript: str, meeting_transcript: str) -> list[str]:
        preferred_source = closing_transcript if closing_transcript.strip() else meeting_transcript
        parts = [
            segment.strip(" -•\t")
            for segment in preferred_source.replace("\r", "\n").split(".")
            if segment.strip()
        ]

        summary: list[str] = []
        for part in parts:
            normalized = " ".join(part.split())
            if normalized and normalized not in summary:
                summary.append(normalized)
            if len(summary) == 4:
                break

        if len(summary) < 4:
            for part in meeting_transcript.replace("\r", "\n").split("."):
                normalized = " ".join(part.strip().split())
                if normalized and normalized not in summary:
                    summary.append(normalized)
                if len(summary) == 4:
                    break

        return summary[:4]

    def _build_team_groups(self, tasks, employees: list[Employee]) -> list[TeamTaskGroup]:
        employee_map = {employee.employee_id: employee for employee in employees}
        team_task_map: dict[str, list] = defaultdict(list)
        member_task_map: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
        member_meta: dict[str, tuple] = {}

        for task in tasks:
            employee = employee_map.get(task.assignee_id) if task.assignee_id else None
            team = employee.team if employee else "Unassigned"
            member_name = employee.name if employee else (task.assignee or "Unassigned")
            member_key = str(employee.employee_id) if employee else member_name

            team_task_map[team].append(task)
            member_task_map[team][member_key].append(task)
            member_meta[member_key] = (
                employee.employee_id if employee else None,
                member_name,
                team,
            )

        groups: list[TeamTaskGroup] = []
        for team, team_tasks in team_task_map.items():
            members = []
            for member_key, member_tasks in member_task_map[team].items():
                employee_id, employee_name, member_team = member_meta[member_key]
                members.append(
                    MemberTaskGroup(
                        employee_id=employee_id,
                        employee_name=employee_name,
                        team=member_team,
                        tasks=member_tasks,
                    )
                )

            groups.append(
                TeamTaskGroup(
                    team=team,
                    tasks=team_tasks,
                    members=sorted(members, key=lambda item: item.employee_name.lower()),
                )
            )

        return sorted(groups, key=lambda item: item.team.lower())
