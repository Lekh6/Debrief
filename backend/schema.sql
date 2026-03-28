CREATE TABLE IF NOT EXISTS projects (
  project_id UUID PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  jira_project_key VARCHAR(50),
  slack_channel_id VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS employees (
  employee_id UUID PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  team VARCHAR(120) NOT NULL,
  jira_account_id VARCHAR(255),
  slack_user_id VARCHAR(255),
  project_id UUID NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS meetings (
  meeting_id UUID PRIMARY KEY,
  project_id UUID NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
  date TIMESTAMP NOT NULL,
  meeting_transcript TEXT NOT NULL,
  closing_transcript TEXT NOT NULL,
  status VARCHAR(32) NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
  task_id UUID PRIMARY KEY,
  meeting_id UUID NOT NULL REFERENCES meetings(meeting_id) ON DELETE CASCADE,
  title VARCHAR(255) NOT NULL,
  description TEXT NOT NULL,
  assignee_id UUID REFERENCES employees(employee_id),
  deadline DATE,
  confidence JSONB NOT NULL,
  confidence_reasons JSONB NOT NULL,
  jira_issue_id VARCHAR(100),
  google_calendar_event_id VARCHAR(255),
  status VARCHAR(64) NOT NULL,
  slack_delivery_status VARCHAR(64) NOT NULL
);
