from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class EmployeeCreate(BaseModel):
    name: str
    team: str = "General"
    jira_account_id: str | None = None
    jira_email: str | None = None
    calendar_email: str | None = None
    slack_user_id: str | None = None


class EmployeeRead(EmployeeCreate):
    employee_id: UUID
    project_id: UUID

    model_config = {"from_attributes": True}


class ProjectCreate(BaseModel):
    name: str
    jira_project_key: str | None = None
    slack_channel_id: str | None = None
    employees: list[EmployeeCreate] = Field(default_factory=list)


class ProjectRead(BaseModel):
    project_id: UUID
    name: str
    jira_project_key: str | None = None
    slack_channel_id: str | None = None
    employees: list[EmployeeRead] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class TaskConfidence(BaseModel):
    title: str = "low"
    description: str = "low"
    assignee: str = "low"
    deadline: str = "low"


class ExtractedTask(BaseModel):
    title: str = ""
    description: str = ""
    assignee: str | None = None
    assignee_id: UUID | None = None
    deadline: date | None = None
    confidence: TaskConfidence = Field(default_factory=TaskConfidence)
    confidence_reasons: dict[str, str] = Field(default_factory=dict)


class MeetingRead(BaseModel):
    meeting_id: UUID
    project_id: UUID
    date: datetime
    meeting_transcript: str
    closing_transcript: str
    status: str
    tasks: list[ExtractedTask] = Field(default_factory=list)

    model_config = {"from_attributes": True}
