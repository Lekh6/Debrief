import sqlite3


def main() -> None:
    conn = sqlite3.connect("backend/meetings.db")
    try:
        cur = conn.cursor()
        cur.execute(
            "update projects set jira_project_key=? where name=?",
            ("KAN", "Data Platform Upgrade"),
        )
        cur.execute(
            (
                "update employees "
                "set jira_account_id=?, jira_email=?, calendar_email=? "
                "where name=? and project_id=(select project_id from projects where name=?)"
            ),
            (
                "712020:7a900cde-636a-4f29-8b18-c82e6b78634a",
                "sashreek.addanki@gmail.com",
                "sashreek.addanki@gmail.com",
                "Clara Zhou",
                "Data Platform Upgrade",
            ),
        )
        conn.commit()
        print("updated_project_and_clara")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
