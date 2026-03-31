from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.models.base import Base


settings = get_settings()

engine = create_engine(settings.database_url, echo=settings.sql_echo, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    import app.models.entities  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _apply_bootstrap_migrations()


def _apply_bootstrap_migrations() -> None:
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    if "employees" in existing_tables:
        employee_columns = {column["name"] for column in inspector.get_columns("employees")}
        with engine.begin() as connection:
            if "jira_email" not in employee_columns:
                connection.execute(text("ALTER TABLE employees ADD COLUMN jira_email VARCHAR(255)"))
            if "calendar_email" not in employee_columns:
                connection.execute(text("ALTER TABLE employees ADD COLUMN calendar_email VARCHAR(255)"))

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    if "tasks" in existing_tables:
        task_columns = {column["name"] for column in inspector.get_columns("tasks")}
        with engine.begin() as connection:
            if "jira_status" not in task_columns:
                connection.execute(text("ALTER TABLE tasks ADD COLUMN jira_status VARCHAR(64) DEFAULT 'not_sent'"))
            if "jira_error" not in task_columns:
                connection.execute(text("ALTER TABLE tasks ADD COLUMN jira_error TEXT"))
            if "google_calendar_status" not in task_columns:
                connection.execute(text("ALTER TABLE tasks ADD COLUMN google_calendar_status VARCHAR(64) DEFAULT 'not_sent'"))
            if "google_calendar_error" not in task_columns:
                connection.execute(text("ALTER TABLE tasks ADD COLUMN google_calendar_error TEXT"))
