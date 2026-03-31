import json

import requests


PROJECT_ID = "168d62d7-e74a-49e7-b81d-a8b83be46ea2"
BASE_URL = "http://127.0.0.1:8004/api/v1"


def main() -> None:
    extract_response = requests.post(
        f"{BASE_URL}/meetings/extract",
        data={
            "project_id": PROJECT_ID,
            "meeting_transcript": (
                "John Carter will finalize the new landing page layout by 2026-04-02. "
                "Maya Lee should update the hero visuals and CTA variants by 2026-04-03. "
                "Priya Nair will draft the launch email copy before Friday."
            ),
            "closing_transcript": (
                "John Carter will finalize the new landing page layout by 2026-04-02. "
                "Maya Lee should update the hero visuals and CTA variants by 2026-04-03. "
                "Priya Nair will draft the launch email copy before Friday."
            ),
        },
        timeout=60,
    )
    extract_response.raise_for_status()
    extracted = extract_response.json()
    print("extract status:", extract_response.status_code)

    confirm_payload = {
        "tasks": [
            {
                "title": task["title"],
                "description": task["description"],
                "assignee_id": task["assignee_id"],
                "assignee_name": task["assignee"],
                "deadline": task["deadline"],
                "confidence": task["confidence"],
                "confidence_reasons": task["confidence_reasons"],
            }
            for task in extracted["tasks"]
        ]
    }
    confirm_response = requests.post(
        f"{BASE_URL}/meetings/{extracted['meeting_id']}/confirm",
        json=confirm_payload,
        timeout=60,
    )
    print("confirm status:", confirm_response.status_code)
    print(json.dumps(confirm_response.json(), indent=2)[:5000])


if __name__ == "__main__":
    main()
