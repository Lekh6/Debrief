from app.db.session import SessionLocal
from app.models.entities import Employee, Project


def main() -> None:
    db = SessionLocal()
    try:
      project = db.query(Project).filter(Project.name == "Website Redesign Demo").one_or_none()
      if not project:
          print("Website Redesign Demo project not found.")
          return

      employees = db.query(Employee).filter(Employee.project_id == project.project_id).all()
      for employee in employees:
          employee.team = "Website"
      db.commit()
      print(f"Updated project {project.project_id} to single-team mode.")
    finally:
      db.close()


if __name__ == "__main__":
    main()
