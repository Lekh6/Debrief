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
                "712020:31e03e2b-3f25-4d80-8b5b-d4bbb792f813",
                "lekharuthwik265@gmail.com",
                "lekharuthwik265@gmail.com",
                "Clara Zhou",
                "Data Platform Upgrade",
            ),
        )
        cur.execute(
            (
                "update employees "
                "set jira_account_id=?, jira_email=?, calendar_email=? "
                "where name=? and project_id=(select project_id from projects where name=?)"
            ),
            (
                "712020:692dd27a-7b8c-4567-9ec0-803231610f15",
                "lekharuthwik@gmail.com",
                "lekharuthwik@gmail.com",
                "Rahul Mehta",
                "Data Platform Upgrade",
            ),
        )
        cur.execute(
            (
                "update employees "
                "set jira_account_id=?, jira_email=?, calendar_email=? "
                "where name=? and project_id=(select project_id from projects where name=?)"
            ),
            (
                "712020:55725d14-7f90-4dec-bf73-c9dbf05d0ccc",
                "lekharuthwik262+t1@gmail.com",
                "lekharuthwik262+t1@gmail.com",
                "Eva Stone",
                "Data Platform Upgrade",
            ),
        )
        conn.commit()
        print("updated_project_and_clara")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
