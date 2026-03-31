import { useEffect, useState } from "react";

import { ConfirmationModal } from "./components/ConfirmationModal";
import { UploadPanel } from "./components/UploadPanel";
import {
  ConfirmTaskInput,
  ExtractionResponse,
  HostReviewRow,
  Project,
  confirmMeetingTasks,
  extractMeetingTasks,
  listProjects,
} from "./lib/api";

interface PushToastState {
  successes: string[];
  failures: string[];
}

const fallbackProjects: Project[] = [
  {
    project_id: "168d62d7-e74a-49e7-b81d-a8b83be46ea2",
    name: "Website Redesign Demo",
    jira_project_key: "WRD",
    slack_channel_id: "C-DEMO-WEB",
    employees: [],
  },
  {
    project_id: "b1c18e49-48cb-4181-aa01-1957df96413d",
    name: "Mobile Launch Demo",
    jira_project_key: "MLD",
    slack_channel_id: "C-DEMO-MOBILE",
    employees: [],
  },
];

function blankConfidence() {
  return {
    title: "high" as const,
    description: "high" as const,
    assignee: "high" as const,
    deadline: "high" as const,
  };
}

function toReviewRows(result: ExtractionResponse): HostReviewRow[] {
  return result.employees.map((employee) => {
    const employeeTasks = result.tasks.filter((task) => task.assignee_id === employee.employee_id);
    const primaryTask = employeeTasks[0] ?? null;

    return {
      employee_id: employee.employee_id,
      employee_name: employee.name,
      team: employee.team,
      purpose: employeeTasks.map((task) => task.description || task.title).filter(Boolean).join("\n"),
      deadline: primaryTask?.deadline ?? null,
      confidence: primaryTask?.confidence ?? blankConfidence(),
      confidence_reasons: primaryTask?.confidence_reasons ?? {},
    };
  });
}

function toConfirmTasks(rows: HostReviewRow[]): ConfirmTaskInput[] {
  return rows
    .filter((row) => row.purpose.trim())
    .map((row) => ({
      title: row.purpose.split("\n")[0].slice(0, 120) || `${row.employee_name} task`,
      description: row.purpose,
      assignee_id: row.employee_id,
      assignee_name: row.employee_name,
      deadline: row.deadline,
      confidence: row.confidence,
      confidence_reasons: row.confidence_reasons,
    }));
}

export default function App() {
  const [result, setResult] = useState<ExtractionResponse | null>(null);
  const [reviewRows, setReviewRows] = useState<HostReviewRow[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [pushToast, setPushToast] = useState<PushToastState | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const loadedProjects = await listProjects();
        setProjects(loadedProjects.length ? loadedProjects : fallbackProjects);
      } catch (requestError) {
        setProjects(fallbackProjects);
        setError(requestError instanceof Error ? requestError.message : "Failed to load projects");
      }
    })();
  }, []);

  async function handleExtract(payload: {
    projectId: string;
    meetingTranscript?: string;
    closingTranscript?: string;
    meetingAudio?: File | null;
    closingAudio?: File | null;
  }) {
    setBusy(true);
    setError(null);
    setSuccessMessage(null);
    setPushToast(null);
    try {
      const extraction = await extractMeetingTasks(payload);
      setResult(extraction);
      setReviewRows(toReviewRows(extraction));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unknown extraction error");
    } finally {
      setBusy(false);
    }
  }

  function handleRowChange(index: number, updates: Partial<HostReviewRow>) {
    setReviewRows((current) =>
      current.map((row, rowIndex) => (rowIndex === index ? { ...row, ...updates } : row)),
    );
  }

  async function handleConfirm() {
    if (!result) {
      return;
    }

    setBusy(true);
    setError(null);
    try {
      const confirmed = await confirmMeetingTasks(result.meeting_id, toConfirmTasks(reviewRows));
      const jiraCreated = confirmed.filter((task: any) => task.jira_status === "created").length;
      const calendarCreated = confirmed.filter((task: any) => task.google_calendar_status === "created").length;
      const calendarCreatedWithoutAttendee = confirmed.filter(
        (task: any) => task.google_calendar_status === "created_without_attendee",
      ).length;
      const jiraFailed = confirmed.filter((task: any) => task.jira_status === "failed").length;
      const calendarFailed = confirmed.filter((task: any) => task.google_calendar_status === "failed").length;
      const calendarErrorSample =
        confirmed.find((task: any) => task.google_calendar_error)?.google_calendar_error ?? null;
      const jiraErrorSample = confirmed.find((task: any) => task.jira_error)?.jira_error ?? null;
      setSuccessMessage(
        `Saved ${confirmed.length} tasks.`,
      );
      setPushToast({
        successes: [
          jiraCreated ? `${jiraCreated} Jira task${jiraCreated > 1 ? "s" : ""} pushed successfully.` : "",
          calendarCreated ? `${calendarCreated} calendar invite${calendarCreated > 1 ? "s" : ""} sent successfully.` : "",
          calendarCreatedWithoutAttendee
            ? `${calendarCreatedWithoutAttendee} calendar event${calendarCreatedWithoutAttendee > 1 ? "s" : ""} created without attendee invite.`
            : "",
        ].filter(Boolean),
        failures: [
          jiraFailed ? `${jiraFailed} Jira push${jiraFailed > 1 ? "es" : ""} failed.` : "",
          calendarFailed ? `${calendarFailed} calendar push${calendarFailed > 1 ? "es" : ""} failed.` : "",
          jiraErrorSample ? `Jira: ${jiraErrorSample}` : "",
          calendarErrorSample ? `Calendar: ${calendarErrorSample}` : "",
        ].filter(Boolean),
      });
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unknown confirmation error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="hero">
        <div>
          <p className="eyebrow">Post-Meeting Task Automation</p>
          <h1>Turn the last minute of a meeting into tracked work.</h1>
          <p className="hero-copy">
            Closing statements become the source of truth, the meeting transcript fills the gaps, and the host gets a fast
            confidence-based review flow before anything is pushed downstream.
          </p>
        </div>

        <div className="status-card">
          <p>Current build focus</p>
          <strong>Phase 1 extraction + early Phase 2 confirmation</strong>
          <span>{result ? `Extraction mode: ${result.extraction_mode}` : "Ready for the first project setup."}</span>
        </div>
      </section>

      {error ? <div className="banner banner-error">{error}</div> : null}
      {successMessage ? <div className="banner banner-success">{successMessage}</div> : null}
      {pushToast ? (
        <div className="push-toast">
          <button className="toast-close" onClick={() => setPushToast(null)} type="button">
            x
          </button>
          {pushToast.successes.length ? (
            <div className="toast-section toast-success">
              <strong>Succeeded</strong>
              {pushToast.successes.map((item) => (
                <p key={item}>{item}</p>
              ))}
            </div>
          ) : null}
          {pushToast.failures.length ? (
            <div className="toast-section toast-failure">
              <strong>Failed</strong>
              {pushToast.failures.map((item) => (
                <p key={item}>{item}</p>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}

      <UploadPanel busy={busy} onSubmit={handleExtract} projects={projects} />

      {result ? (
        <section className="panel transcript-panel">
          <div className="panel-heading">
            <p className="eyebrow">Context</p>
            <h2>Resolved transcripts</h2>
          </div>
          <div className="transcript-grid">
            <article>
              <h3>Meeting transcript</h3>
              <p>{result.meeting_transcript}</p>
            </article>
            <article>
              <h3>AI meeting summary</h3>
              <p>{result.meeting_summary.join("\n")}</p>
            </article>
          </div>
        </section>
      ) : null}

      {result ? (
        <ConfirmationModal
          busy={busy}
          employees={result?.employees ?? []}
          onClose={() => setResult(null)}
          onConfirm={handleConfirm}
          onRowChange={handleRowChange}
          result={result}
          rows={reviewRows}
        />
      ) : null}
    </main>
  );
}
