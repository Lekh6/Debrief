from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.projects import EmployeeRead
from app.schemas.projects import ExtractedTask, TaskConfidence


class MemberTaskGroup(BaseModel):
    employee_id: UUID | None = None
    employee_name: str
    team: str
    tasks: list[ExtractedTask] = Field(default_factory=list)


class TeamTaskGroup(BaseModel):
    team: str
    tasks: list[ExtractedTask] = Field(default_factory=list)
    members: list[MemberTaskGroup] = Field(default_factory=list)


class ExtractionResponse(BaseModel):
    meeting_id: UUID
    project_id: UUID
    project_name: str
    meeting_transcript: str
    closing_transcript: str
    meeting_summary: list[str] = Field(default_factory=list)
    tasks: list[ExtractedTask] = Field(default_factory=list)
    extraction_mode: str
    employees: list[EmployeeRead] = Field(default_factory=list)
    team_groups: list[TeamTaskGroup] = Field(default_factory=list)


class TaskConfirmInput(BaseModel):
    title: str
    description: str = ""
    assignee_id: UUID | None = None
    assignee_name: str | None = None
    deadline: date | None = None
    confidence: TaskConfidence = Field(default_factory=TaskConfidence)
    confidence_reasons: dict[str, str] = Field(default_factory=dict)


class MeetingConfirmRequest(BaseModel):
    tasks: list[TaskConfirmInput]


class DeliveryResult(BaseModel):
    jira_issue_id: str | None = None
    jira_status: str = "not_sent"
    slack_status: str = "not_sent"
    error: str | None = None


class ConfirmedTaskRead(BaseModel):
    task_id: UUID
    title: str
    description: str
    assignee_id: UUID | None = None
    deadline: date | None = None
    confidence: TaskConfidence = Field(default_factory=TaskConfidence)
    confidence_reasons: dict[str, str] = Field(default_factory=dict)
    jira_issue_id: str | None = None
    jira_status: str = "not_sent"
    jira_error: str | None = None
    google_calendar_event_id: str | None = None
    google_calendar_status: str = "not_sent"
    google_calendar_error: str | None = None
    status: str
    slack_delivery_status: str

    model_config = {"from_attributes": True}


class MeetingHistoryItem(BaseModel):
    meeting_id: UUID
    project_id: UUID
    date: datetime
    status: str
    closing_transcript: str
    tasks: list[ConfirmedTaskRead] = Field(default_factory=list)

    model_config = {"from_attributes": True}
