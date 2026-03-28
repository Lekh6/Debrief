import json

import requests


def main() -> None:
    url = "http://127.0.0.1:8001/api/v1/meetings/extract"
    payload = {
        "project_id": "168d62d7-e74a-49e7-b81d-a8b83be46ea2",
        "meeting_transcript": (
            "John Carter will finalize the new landing page layout by 2026-04-02. "
            "Maya Lee should update the hero visuals and CTA variants by 2026-04-03. "
            "Priya Nair will draft the launch email copy before Friday. "
            "We agreed the website refresh stays on track for the early April preview."
        ),
        "closing_transcript": (
            "John Carter will finalize the new landing page layout by 2026-04-02. "
            "Maya Lee should update the hero visuals and CTA variants by 2026-04-03. "
            "Priya Nair will draft the launch email copy before Friday. "
            "We agreed the website refresh stays on track for the early April preview."
        ),
    }
    response = requests.post(url, data=payload, timeout=60)
    print("status:", response.status_code)
    print(json.dumps(response.json(), indent=2)[:5000])


if __name__ == "__main__":
    main()
