import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.models.base import Base


def json_type():
    return JSON().with_variant(JSONB(astext_type=Text()), "postgresql")


class Project(Base):
    __tablename__ = "projects"

    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    jira_project_key: Mapped[str | None] = mapped_column(String(50), nullable=True)
    slack_channel_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    employees: Mapped[list["Employee"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    meetings: Mapped[list["Meeting"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    google_oauth_credential: Mapped["GoogleOAuthCredential | None"] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        uselist=False,
    )


class Employee(Base):
    __tablename__ = "employees"

    employee_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    team: Mapped[str] = mapped_column(String(120), nullable=False, default="General")
    jira_account_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    jira_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    calendar_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    slack_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.project_id"), nullable=False)

    project: Mapped[Project] = relationship(back_populates="employees")
    tasks: Mapped[list["Task"]] = relationship(back_populates="assignee")


class Meeting(Base):
    __tablename__ = "meetings"

    meeting_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.project_id"), nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, nullable=False)
    meeting_transcript: Mapped[str] = mapped_column(Text, nullable=False)
    closing_transcript: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)

    project: Mapped[Project] = relationship(back_populates="meetings")
    tasks: Mapped[list["Task"]] = relationship(back_populates="meeting", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    task_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meeting_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("meetings.meeting_id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("employees.employee_id"), nullable=True)
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    confidence: Mapped[dict] = mapped_column(json_type(), nullable=False, default=dict)
    confidence_reasons: Mapped[dict] = mapped_column(json_type(), nullable=False, default=dict)
    jira_issue_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    jira_status: Mapped[str] = mapped_column(String(64), default="not_sent", nullable=False)
    jira_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    google_calendar_event_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    google_calendar_status: Mapped[str] = mapped_column(String(64), default="not_sent", nullable=False)
    google_calendar_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(64), default="draft", nullable=False)
    slack_delivery_status: Mapped[str] = mapped_column(String(64), default="not_sent", nullable=False)

    meeting: Mapped[Meeting] = relationship(back_populates="tasks")
    assignee: Mapped[Employee | None] = relationship(back_populates="tasks")


class GoogleOAuthCredential(Base):
    __tablename__ = "google_oauth_credentials"

    credential_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.project_id"),
        nullable=False,
        unique=True,
    )
    google_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_uri: Mapped[str] = mapped_column(String(255), default="https://oauth2.googleapis.com/token", nullable=False)
    scope: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)

    project: Mapped[Project] = relationship(back_populates="google_oauth_credential")
