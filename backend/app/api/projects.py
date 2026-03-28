from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models.entities import Employee, Project
from app.schemas.projects import ProjectCreate, ProjectRead


router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectRead])
def list_projects(db: Session = Depends(get_db)) -> list[Project]:
    return db.query(Project).options(selectinload(Project.employees)).order_by(Project.name.asc()).all()


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)) -> Project:
    project = Project(
        name=payload.name,
        jira_project_key=payload.jira_project_key,
        slack_channel_id=payload.slack_channel_id,
    )
    db.add(project)
    db.flush()

    for employee in payload.employees:
        db.add(
            Employee(
                name=employee.name,
                team=employee.team,
                jira_account_id=employee.jira_account_id,
                slack_user_id=employee.slack_user_id,
                project_id=project.project_id,
            )
        )

    db.commit()
    return (
        db.query(Project)
        .options(selectinload(Project.employees))
        .filter(Project.project_id == project.project_id)
        .one()
    )


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: str, db: Session = Depends(get_db)) -> Project:
    project = (
        db.query(Project)
        .options(selectinload(Project.employees))
        .filter(Project.project_id == project_id)
        .one_or_none()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    return project
