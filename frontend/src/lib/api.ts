export type ConfidenceLevel = "high" | "medium" | "low";

export interface TaskConfidence {
  title: ConfidenceLevel;
  description: ConfidenceLevel;
  assignee: ConfidenceLevel;
  deadline: ConfidenceLevel;
}

export interface Employee {
  employee_id: string;
  project_id: string;
  name: string;
  team: string;
  jira_account_id: string | null;
  jira_email: string | null;
  calendar_email: string | null;
  slack_user_id: string | null;
}

export interface Project {
  project_id: string;
  name: string;
  jira_project_key: string | null;
  slack_channel_id: string | null;
  employees: Employee[];
}

export interface ExtractedTask {
  title: string;
  description: string;
  assignee: string | null;
  assignee_id: string | null;
  deadline: string | null;
  confidence: TaskConfidence;
  confidence_reasons: Record<string, string>;
}

export interface ExtractionResponse {
  meeting_id: string;
  project_id: string;
  project_name: string;
  meeting_transcript: string;
  closing_transcript: string;
  meeting_summary: string[];
  tasks: ExtractedTask[];
  extraction_mode: string;
  employees: Employee[];
  team_groups: Array<{
    team: string;
    tasks: ExtractedTask[];
    members: Array<{
      employee_id: string | null;
      employee_name: string;
      team: string;
      tasks: ExtractedTask[];
    }>;
  }>;
}

export interface ConfirmTaskInput {
  title: string;
  description: string;
  assignee_id: string | null;
  assignee_name: string | null;
  deadline: string | null;
  confidence: TaskConfidence;
  confidence_reasons: Record<string, string>;
}

export interface DeliveryTargets {
  jira: boolean;
  google_calendar: boolean;
  slack: boolean;
}

export interface HostReviewRow {
  employee_id: string;
  employee_name: string;
  team: string;
  purpose: string;
  deadline: string | null;
  confidence: TaskConfidence;
  confidence_reasons: Record<string, string>;
  included: boolean;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export function getGoogleAuthStartUrl(projectId: string) {
  return `${API_BASE_URL}/auth/google/start?project_id=${encodeURIComponent(projectId)}`;
}

export async function listProjects(): Promise<Project[]> {
  const response = await fetch(`${API_BASE_URL}/projects`);
  if (!response.ok) {
    throw new Error("Failed to load demo projects");
  }
  return response.json();
}

export async function createProject(payload: {
  name: string;
  jira_project_key?: string | null;
  slack_channel_id?: string | null;
  employees?: Array<Partial<Employee> & { name: string; team: string }>;
}): Promise<Project> {
  const response = await fetch(`${API_BASE_URL}/projects`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      name: payload.name,
      jira_project_key: payload.jira_project_key || null,
      slack_channel_id: payload.slack_channel_id || null,
      employees: payload.employees ?? [],
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to create project" }));
    throw new Error(error.detail ?? "Failed to create project");
  }

  return response.json();
}

export async function addProjectMember(
  projectId: string,
  payload: {
    name: string;
    team: string;
    jira_account_id?: string | null;
    jira_email?: string | null;
    calendar_email?: string | null;
    slack_user_id?: string | null;
  },
): Promise<Employee> {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/employees`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      name: payload.name,
      team: payload.team,
      jira_account_id: payload.jira_account_id || null,
      jira_email: payload.jira_email || null,
      calendar_email: payload.calendar_email || null,
      slack_user_id: payload.slack_user_id || null,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to add team member" }));
    throw new Error(error.detail ?? "Failed to add team member");
  }

  return response.json();
}

export async function extractMeetingTasks(payload: {
  projectId: string;
  meetingTranscript?: string;
  closingTranscript?: string;
  meetingAudio?: File | null;
  closingAudio?: File | null;
}): Promise<ExtractionResponse> {
  const formData = new FormData();
  formData.set("project_id", payload.projectId);
  if (payload.meetingTranscript) {
    formData.set("meeting_transcript", payload.meetingTranscript);
  }
  if (payload.closingTranscript) {
    formData.set("closing_transcript", payload.closingTranscript);
  }
  if (payload.meetingAudio) {
    formData.set("meeting_audio", payload.meetingAudio);
  }
  if (payload.closingAudio) {
    formData.set("closing_audio", payload.closingAudio);
  }

  const response = await fetch(`${API_BASE_URL}/meetings/extract`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown extraction error" }));
    throw new Error(error.detail ?? "Unknown extraction error");
  }

  return response.json();
}

export async function confirmMeetingTasks(meetingId: string, tasks: ConfirmTaskInput[], deliveryTargets: DeliveryTargets) {
  const response = await fetch(`${API_BASE_URL}/meetings/${meetingId}/confirm`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ tasks, delivery_targets: deliveryTargets }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown confirmation error" }));
    throw new Error(error.detail ?? "Unknown confirmation error");
  }

  return response.json();
}
