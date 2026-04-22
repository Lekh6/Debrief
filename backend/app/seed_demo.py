from app.db.session import SessionLocal, init_db
from app.models.entities import Employee, Project


DEMO_PROJECTS = [
    {
        "name": "Website Redesign Demo",
        "jira_project_key": "WRD",
        "slack_channel_id": "C-DEMO-WEB",
        "employees": [
            {"name": "John Carter", "team": "Website", "jira_account_id": "jira-john-carter", "jira_email": "john.carter@example.com", "calendar_email": "john.carter@example.com", "slack_user_id": "UJOHN001"},
            {"name": "Maya Lee", "team": "Website", "jira_account_id": "jira-maya-lee", "jira_email": "maya.lee@example.com", "calendar_email": "maya.lee@example.com", "slack_user_id": "UMAYA001"},
            {"name": "Priya Nair", "team": "Website", "jira_account_id": "jira-priya-nair", "jira_email": "priya.nair@example.com", "calendar_email": "priya.nair@example.com", "slack_user_id": "UPRIYA01"},
        ],
    },
    {
        "name": "Mobile Launch Demo",
        "jira_project_key": "MLD",
        "slack_channel_id": "C-DEMO-MOBILE",
        "employees": [
            {"name": "Arjun Patel", "team": "Engineering", "jira_account_id": "jira-arjun-patel", "jira_email": "arjun.patel@example.com", "calendar_email": "arjun.patel@example.com", "slack_user_id": "UARJUN01"},
            {"name": "Sara Kim", "team": "QA", "jira_account_id": "jira-sara-kim", "jira_email": "sara.kim@example.com", "calendar_email": "sara.kim@example.com", "slack_user_id": "USARA001"},
            {"name": "Leo Grant", "team": "Product", "jira_account_id": "jira-leo-grant", "jira_email": "leo.grant@example.com", "calendar_email": "leo.grant@example.com", "slack_user_id": "ULEO0001"},
        ],
    },
    {
        "name": "Customer Success Rollout",
        "jira_project_key": "CSR",
        "slack_channel_id": "C-DEMO-CS",
        "employees": [
            {"name": "Nina Brooks", "team": "Customer Success", "jira_account_id": "jira-nina-brooks", "jira_email": "nina.brooks@example.com", "calendar_email": "nina.brooks@example.com", "slack_user_id": "UNINA001"},
            {"name": "Omar Hassan", "team": "Operations", "jira_account_id": "jira-omar-hassan", "jira_email": "omar.hassan@example.com", "calendar_email": "omar.hassan@example.com", "slack_user_id": "UOMAR001"},
        ],
    },
    {
        "name": "Data Platform Upgrade",
        "jira_project_key": "KAN",
        "slack_channel_id": "C-DEMO-DATA",
        "employees": [
            {"name": "Eva Stone", "team": "Data Engineering", "jira_account_id": "712020:55725d14-7f90-4dec-bf73-c9dbf05d0ccc", "jira_email": "lekharuthwik262+t1@gmail.com", "calendar_email": "lekharuthwik262+t1@gmail.com", "slack_user_id": "U0AQW0NCQAW"},
            {"name": "Rahul Mehta", "team": "Platform", "jira_account_id": "712020:692dd27a-7b8c-4567-9ec0-803231610f15", "jira_email": "lekharuthwik@gmail.com", "calendar_email": "lekharuthwik@gmail.com", "slack_user_id": "U0AUH5N144W"},
            {"name": "Clara Zhou", "team": "Analytics", "jira_account_id": "712020:31e03e2b-3f25-4d80-8b5b-d4bbb792f813", "jira_email": "lekharuthwik265@gmail.com", "calendar_email": "lekharuthwik265@gmail.com", "slack_user_id": "U0AUFQRDA5B"},
        ],
    },
]


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        created = 0
        for project_data in DEMO_PROJECTS:
            existing = db.query(Project).filter(Project.name == project_data["name"]).one_or_none()
            if existing:
                existing.jira_project_key = project_data["jira_project_key"]
                existing.slack_channel_id = project_data["slack_channel_id"]
                employees_by_name = {employee.name: employee for employee in db.query(Employee).filter(Employee.project_id == existing.project_id).all()}
                for employee_data in project_data["employees"]:
                    current = employees_by_name.get(employee_data["name"])
                    if current:
                        current.team = employee_data["team"]
                        current.jira_account_id = employee_data["jira_account_id"]
                        current.jira_email = employee_data["jira_email"]
                        current.calendar_email = employee_data["calendar_email"]
                        current.slack_user_id = employee_data["slack_user_id"]
                db.commit()
                print(f"Exists: {project_data['name']} -> {existing.project_id}")
                continue

            project = Project(
                name=project_data["name"],
                jira_project_key=project_data["jira_project_key"],
                slack_channel_id=project_data["slack_channel_id"],
            )
            db.add(project)
            db.flush()

            for employee in project_data["employees"]:
                db.add(
                    Employee(
                        name=employee["name"],
                        team=employee["team"],
                        jira_account_id=employee["jira_account_id"],
                        jira_email=employee["jira_email"],
                        calendar_email=employee["calendar_email"],
                        slack_user_id=employee["slack_user_id"],
                        project_id=project.project_id,
                    )
                )

            db.commit()
            created += 1
            print(f"Created: {project.name} -> {project.project_id}")

        print(f"Demo seed complete. New projects created: {created}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
