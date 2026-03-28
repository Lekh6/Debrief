from app.db.session import SessionLocal, init_db
from app.models.entities import Employee, Project


DEMO_PROJECTS = [
    {
        "name": "Website Redesign Demo",
        "jira_project_key": "WRD",
        "slack_channel_id": "C-DEMO-WEB",
        "employees": [
            {"name": "John Carter", "team": "Website", "jira_account_id": "jira-john-carter", "slack_user_id": "UJOHN001"},
            {"name": "Maya Lee", "team": "Website", "jira_account_id": "jira-maya-lee", "slack_user_id": "UMAYA001"},
            {"name": "Priya Nair", "team": "Website", "jira_account_id": "jira-priya-nair", "slack_user_id": "UPRIYA01"},
        ],
    },
    {
        "name": "Mobile Launch Demo",
        "jira_project_key": "MLD",
        "slack_channel_id": "C-DEMO-MOBILE",
        "employees": [
            {"name": "Arjun Patel", "team": "Engineering", "jira_account_id": "jira-arjun-patel", "slack_user_id": "UARJUN01"},
            {"name": "Sara Kim", "team": "QA", "jira_account_id": "jira-sara-kim", "slack_user_id": "USARA001"},
            {"name": "Leo Grant", "team": "Product", "jira_account_id": "jira-leo-grant", "slack_user_id": "ULEO0001"},
        ],
    },
    {
        "name": "Customer Success Rollout",
        "jira_project_key": "CSR",
        "slack_channel_id": "C-DEMO-CS",
        "employees": [
            {"name": "Nina Brooks", "team": "Customer Success", "jira_account_id": "jira-nina-brooks", "slack_user_id": "UNINA001"},
            {"name": "Omar Hassan", "team": "Operations", "jira_account_id": "jira-omar-hassan", "slack_user_id": "UOMAR001"},
        ],
    },
    {
        "name": "Data Platform Upgrade",
        "jira_project_key": "DPU",
        "slack_channel_id": "C-DEMO-DATA",
        "employees": [
            {"name": "Eva Stone", "team": "Data Engineering", "jira_account_id": "jira-eva-stone", "slack_user_id": "UEVA0001"},
            {"name": "Rahul Mehta", "team": "Platform", "jira_account_id": "jira-rahul-mehta", "slack_user_id": "URAHUL01"},
            {"name": "Clara Zhou", "team": "Analytics", "jira_account_id": "jira-clara-zhou", "slack_user_id": "UCLARA01"},
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
