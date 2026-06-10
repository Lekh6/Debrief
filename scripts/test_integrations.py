import asyncio

from app.db.session import SessionLocal
from app.models.entities import Project
from app.services.integrations.google_calendar import GoogleCalendarService
from app.services.integrations.jira import JiraService


async def main() -> None:
    jira = JiraService()
    jira_result = await jira.create_issue(
        project_key="WRD",
        title="Integration smoke test",
        description="Testing Jira connectivity from Debrief.",
        assignee_account_id="jira-john-carter",
        assignee_email="john.carter@example.com",
        due_date="2026-04-02",
    )
    print("jira:", jira_result)

    calendar = GoogleCalendarService()
    with SessionLocal() as db:
        first_project = db.query(Project).order_by(Project.name.asc()).first()
        if not first_project:
            print("calendar: skipped (no project found in database)")
            return
        calendar_result = await calendar.create_event(
            db=db,
            project_id=first_project.project_id,
            title="Integration smoke test",
            description="Testing Google Calendar connectivity from Debrief.",
            due_date="2026-04-02",
            assignee_name="John Carter",
            assignee_email="john.carter@example.com",
        )
    print("calendar:", calendar_result)


if __name__ == "__main__":
    asyncio.run(main())
