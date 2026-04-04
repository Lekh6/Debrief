import sqlite3


def main() -> None:
    conn = sqlite3.connect("backend/meetings.db")
    try:
        cur = conn.cursor()
        cur.execute(
            "update employees set jira_email=?, calendar_email=? where name=?",
            ("Sashreek.addanki@gmail.com", "Sashreek.addanki@gmail.com", "Clara Zhou"),
        )
        conn.commit()
        print(cur.rowcount)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
