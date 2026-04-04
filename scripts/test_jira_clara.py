import asyncio

from app.services.integrations.jira import JiraService


async def main() -> None:
    jira = JiraService()
    result = await jira.create_issue(
        project_key="KAN",
        title="Debrief Jira smoke test for Clara",
        description="Prepare the analytics handoff and validate the reporting field mappings for the rollout.",
        assignee_account_id="712020:7a900cde-636a-4f29-8b18-c82e6b78634a",
        assignee_email="sashreek.addanki@gmail.com",
        due_date="2026-04-07",
        meeting_transcript=(
            "We need Clara to validate the analytics mapping, confirm the downstream fields, "
            "and send the reporting handoff before Tuesday."
        ),
        closing_transcript=(
            "Clara will own the analytics handoff and finish the field mapping validation by Tuesday."
        ),
        assignee_name="Clara Zhou",
        team_name="Analytics",
    )
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
