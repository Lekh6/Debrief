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

export interface HostReviewRow {
  employee_id: string;
  employee_name: string;
  team: string;
  purpose: string;
  deadline: string | null;
  confidence: TaskConfidence;
  confidence_reasons: Record<string, string>;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export async function listProjects(): Promise<Project[]> {
  const response = await fetch(`${API_BASE_URL}/projects`);
  if (!response.ok) {
    throw new Error("Failed to load demo projects");
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

export async function confirmMeetingTasks(meetingId: string, tasks: ConfirmTaskInput[]) {
  const response = await fetch(`${API_BASE_URL}/meetings/${meetingId}/confirm`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ tasks }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown confirmation error" }));
    throw new Error(error.detail ?? "Unknown confirmation error");
  }

  return response.json();
}
