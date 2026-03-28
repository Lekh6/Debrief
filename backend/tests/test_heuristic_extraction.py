import asyncio
import uuid

from app.models.entities import Employee
from app.services.providers.extraction import ExtractionContext, ExtractionService


def test_heuristic_extraction_uses_closing_statement_and_matches_employees():
    employee = Employee(
        employee_id=uuid.uuid4(),
        name="John Carter",
        team="Design",
        jira_account_id="jira-123",
        slack_user_id="U123",
        project_id=uuid.uuid4(),
    )
    context = ExtractionContext(
        closing_transcript="John Carter will redesign the landing page by Friday. Priya should draft the launch email.",
        meeting_transcript="The team discussed the landing page hero, CTA buttons, and a coordinated launch email.",
        employees=[employee],
    )

    tasks, mode = asyncio.run(ExtractionService().extract(context))

    assert mode == "heuristic"
    assert tasks
    assert tasks[0].assignee == "John Carter"
    assert tasks[0].confidence.assignee == "high"
