from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.db.session import get_db
from app.models.entities import Employee, Meeting, Project, Task
from app.schemas.meetings import ConfirmedTaskRead, ExtractionResponse, MeetingConfirmRequest, MeetingHistoryItem
from app.services.integrations.google_calendar import GoogleCalendarService
from app.services.integrations.jira import JiraService
from app.services.integrations.slack import SlackService
from app.services.meeting_pipeline import MeetingPipeline


router = APIRouter(prefix="/meetings", tags=["meetings"])


@router.post("/extract", response_model=ExtractionResponse)
async def extract_meeting_tasks(
    project_id: UUID = Form(...),
    meeting_transcript: str | None = Form(default=None),
    closing_transcript: str | None = Form(default=None),
    meeting_audio: UploadFile | None = File(default=None),
    closing_audio: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
) -> ExtractionResponse:
    project = (
        db.query(Project)
        .options(selectinload(Project.employees))
        .filter(Project.project_id == project_id)
        .one_or_none()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    pipeline = MeetingPipeline()
    try:
        return await pipeline.extract_tasks(
            db=db,
            project=project,
            meeting_transcript=meeting_transcript,
            closing_transcript=closing_transcript,
            meeting_audio=meeting_audio,
            closing_audio=closing_audio,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Extraction pipeline failed: {exc}") from exc


@router.post("/{meeting_id}/confirm", response_model=list[ConfirmedTaskRead])
async def confirm_meeting_tasks(
    meeting_id: UUID,
    payload: MeetingConfirmRequest,
    db: Session = Depends(get_db),
) -> list[Task]:
    meeting = (
        db.query(Meeting)
        .options(selectinload(Meeting.project), selectinload(Meeting.tasks))
        .filter(Meeting.meeting_id == meeting_id)
        .one_or_none()
    )
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found.")

    if meeting.tasks:
        for task in meeting.tasks:
            db.delete(task)
        db.flush()

    employees = {
        str(employee.employee_id): employee
        for employee in db.query(Employee).filter(Employee.project_id == meeting.project_id).all()
    }

    jira_service = JiraService()
    google_calendar_service = GoogleCalendarService()
    slack_service = SlackService()
    settings = get_settings()
    confirmed_tasks: list[Task] = []

    for item in payload.tasks:
        assignee = None
        if item.assignee_id:
            assignee = employees.get(str(item.assignee_id))
        elif item.assignee_name:
            normalized_name = item.assignee_name.strip().lower()
            assignee = next(
                (
                    employee
                    for employee in employees.values()
                    if employee.name.lower() == normalized_name
                    or employee.name.split()[0].lower() == normalized_name
                ),
                None,
            )
        new_task = Task(
            meeting_id=meeting.meeting_id,
            title=item.title,
            description=item.description,
            assignee_id=assignee.employee_id if assignee else item.assignee_id,
            deadline=item.deadline,
            confidence=item.confidence.model_dump(),
            confidence_reasons=item.confidence_reasons,
            status="confirmed",
        )
        db.add(new_task)
        db.flush()

        if settings.auto_create_jira_on_confirm:
            try:
                jira_result = await jira_service.create_issue(
                    project_key=meeting.project.jira_project_key,
                    title=item.title,
                    description=item.description,
                    assignee_account_id=assignee.jira_account_id if assignee else None,
                    assignee_email=assignee.jira_email if assignee else None,
                    due_date=item.deadline.isoformat() if item.deadline else None,
                    meeting_transcript=meeting.meeting_transcript,
                    closing_transcript=meeting.closing_transcript,
                    assignee_name=assignee.name if assignee else item.assignee_name,
                    team_name=assignee.team if assignee else None,
                )
                new_task.jira_issue_id = jira_result.issue_id
                new_task.jira_status = jira_result.status
                new_task.jira_error = jira_result.error
            except Exception as exc:
                new_task.jira_status = "failed"
                new_task.jira_error = str(exc)

        if settings.auto_create_google_calendar_on_confirm:
            try:
                calendar_result = await google_calendar_service.create_event(
                    db=db,
                    project_id=meeting.project_id,
                    title=item.title,
                    description=item.description,
                    due_date=item.deadline.isoformat() if item.deadline else None,
                    assignee_name=assignee.name if assignee else item.assignee_name,
                    assignee_email=assignee.calendar_email if assignee else None,
                )
                new_task.google_calendar_event_id = calendar_result.event_id
                new_task.google_calendar_status = calendar_result.status
                new_task.google_calendar_error = calendar_result.error
            except Exception as exc:
                new_task.google_calendar_status = "failed"
                new_task.google_calendar_error = str(exc)

        if settings.auto_notify_slack_on_confirm:
            try:
                slack_result = await slack_service.send_task_dm(
                    slack_user_id=assignee.slack_user_id if assignee else None,
                    title=item.title,
                    jira_link=new_task.jira_issue_id,
                )
                new_task.slack_delivery_status = slack_result.status
            except Exception:
                new_task.slack_delivery_status = "failed"

        confirmed_tasks.append(new_task)

    meeting.status = "confirmed"
    for task in confirmed_tasks:
        if task.jira_status == "created" or task.google_calendar_status == "created":
            task.status = "pushed"
    meeting.status = "confirmed"
    db.commit()

    return confirmed_tasks


@router.get("", response_model=list[MeetingHistoryItem])
def list_meetings(project_id: UUID, db: Session = Depends(get_db)) -> list[Meeting]:
    meetings = (
        db.query(Meeting)
        .options(selectinload(Meeting.tasks))
        .filter(Meeting.project_id == project_id)
        .order_by(Meeting.date.desc())
        .all()
    )
    return meetings
