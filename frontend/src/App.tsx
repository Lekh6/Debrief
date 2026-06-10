import { FormEvent, useEffect, useMemo, useState } from "react";
import readmeContent from "../../README.md?raw";

import { ConfirmationModal } from "./components/ConfirmationModal";
import { UploadPanel } from "./components/UploadPanel";
import {
  ConfirmTaskInput,
  DeliveryTargets,
  Employee,
  ExtractionResponse,
  HostReviewRow,
  Project,
  addProjectMember,
  confirmMeetingTasks,
  createProject,
  extractMeetingTasks,
  listProjects,
} from "./lib/api";

interface PushToastState {
  title: string;
  successes: string[];
  failures: string[];
  generatedAt: string;
}

type AppPage = "review" | "teams" | "profile" | "readme";

interface AppPreferences {
  accent: "moss" | "clay" | "ink";
  compactMode: boolean;
  reduceMotion: boolean;
  cardReviewEnabled: boolean;
  darkMode: boolean;
}

const fallbackProjects: Project[] = [
  {
    project_id: "168d62d7-e74a-49e7-b81d-a8b83be46ea2",
    name: "Website Redesign Demo",
    jira_project_key: "KAN",
    slack_channel_id: "C-DEMO-WEB",
    employees: [],
  },
  {
    project_id: "b1c18e49-48cb-4181-aa01-1957df96413d",
    name: "Mobile Launch Demo",
    jira_project_key: "KAN",
    slack_channel_id: "C-DEMO-MOBILE",
    employees: [],
  },
];

const defaultDeliveryTargets: DeliveryTargets = {
  google_calendar: true,
  jira: true,
  slack: true,
};

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
      included: employeeTasks.length > 0,
      delivery_targets: { ...defaultDeliveryTargets },
    };
  });
}

function toConfirmTasks(rows: HostReviewRow[]): ConfirmTaskInput[] {
  return rows
    .filter((row) => row.included)
    .map((row) => ({
      title: row.purpose.split("\n")[0].trim().slice(0, 120) || `${row.employee_name} task`,
      description: row.purpose.trim() || `${row.employee_name} task`,
      assignee_id: row.employee_id,
      assignee_name: row.employee_name,
      deadline: row.deadline,
      confidence: row.confidence,
      confidence_reasons: row.confidence_reasons,
      delivery_targets: row.delivery_targets,
    }));
}

function ReadmePage() {
  return (
    <section className="panel readme-panel">
      <div className="panel-heading">
        <p className="eyebrow">Project guide</p>
        <h2>README.md</h2>
      </div>
      <pre>{readmeContent}</pre>
    </section>
  );
}

function ProfilePreferencesPage({
  preferences,
  onPreferencesChange,
}: {
  preferences: AppPreferences;
  onPreferencesChange: (updates: Partial<AppPreferences>) => void;
}) {
  return (
    <section className="panel preferences-panel">
      <div className="panel-heading">
        <p className="eyebrow">Profile</p>
        <h2>Preferences</h2>
      </div>

      <div className="profile-grid">
        <article className="profile-block">
          <span className="avatar-mark">LK</span>
          <div>
            <h3>Lekha</h3>
            <p className="muted">Host workspace preferences are saved for this browser session.</p>
          </div>
        </article>

        <article className="preference-block">
          <h3>Accent</h3>
          <div className="segmented-control">
            {(["moss", "clay", "ink"] as const).map((accent) => (
              <button
                className={preferences.accent === accent ? "active" : ""}
                key={accent}
                onClick={() => onPreferencesChange({ accent })}
                type="button"
              >
                {accent}
              </button>
            ))}
          </div>
        </article>

        <article className="preference-block">
          <h3>Workspace</h3>
          <label className="toggle-row">
            <span>Compact mode</span>
            <input
              checked={preferences.compactMode}
              type="checkbox"
              onChange={(event) => onPreferencesChange({ compactMode: event.target.checked })}
            />
          </label>
          <label className="toggle-row">
            <span>Reduce motion</span>
            <input
              checked={preferences.reduceMotion}
              type="checkbox"
              onChange={(event) => onPreferencesChange({ reduceMotion: event.target.checked })}
            />
          </label>
          <label className="toggle-row">
            <span>Member card review</span>
            <input
              checked={preferences.cardReviewEnabled}
              type="checkbox"
              onChange={(event) => onPreferencesChange({ cardReviewEnabled: event.target.checked })}
            />
          </label>
          <label className="toggle-row">
            <span>Dark mode</span>
            <input
              checked={preferences.darkMode}
              type="checkbox"
              onChange={(event) => onPreferencesChange({ darkMode: event.target.checked })}
            />
          </label>
        </article>
      </div>
    </section>
  );
}

function TranscriptPreview({ result }: { result: ExtractionResponse }) {
  const [showFullTranscript, setShowFullTranscript] = useState(false);
  const transcriptLines = result.meeting_transcript.split(/\r?\n/).filter((line) => line.trim());
  const previewLines = transcriptLines.slice(0, 7);

  return (
    <>
      <section className="panel transcript-panel">
        <div className="panel-heading inline-heading">
          <div>
            <p className="eyebrow">Context</p>
            <h2>Resolved transcripts</h2>
          </div>
          {transcriptLines.length > 7 ? (
            <button className="secondary-button" onClick={() => setShowFullTranscript(true)} type="button">
              Show more
            </button>
          ) : null}
        </div>
        <div className="transcript-strip">
          <article>
            <h3>Meeting transcript</h3>
            <p className="transcript-content">{previewLines.join("\n")}</p>
          </article>
          <article>
            <h3>AI meeting summary</h3>
            <p className="transcript-content">{result.meeting_summary.join("\n")}</p>
          </article>
        </div>
      </section>

      {showFullTranscript ? (
        <section className="fullscreen-window">
          <div className="fullscreen-window-card">
            <div className="panel-heading inline-heading">
              <div>
                <p className="eyebrow">Meeting transcript</p>
                <h2>Full transcript</h2>
              </div>
              <button className="secondary-button" onClick={() => setShowFullTranscript(false)} type="button">
                Back
              </button>
            </div>
            <p className="transcript-content transcript-content-full">{result.meeting_transcript}</p>
          </div>
        </section>
      ) : null}
    </>
  );
}

function LoginPage({ onLogin }: { onLogin: () => void }) {
  const [hostId, setHostId] = useState("leka");
  const [password, setPassword] = useState("le124");
  const [loginError, setLoginError] = useState<string | null>(null);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (hostId === "leka" && password === "le124") {
      setLoginError(null);
      onLogin();
      return;
    }
    setLoginError("Invalid host ID or password.");
  }

  return (
    <main className="login-shell">
      <section className="login-card">
        <p className="eyebrow">Host Access</p>
        <h1>Sign in to Debrief control.</h1>
        {loginError ? <div className="banner banner-error">{loginError}</div> : null}
        <form className="login-form" onSubmit={handleSubmit}>
          <label>
            <span>Host ID</span>
            <input value={hostId} onChange={(event) => setHostId(event.target.value)} />
          </label>
          <label>
            <span>Password</span>
            <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
          </label>
          <button className="primary-button" type="submit">
            Login
          </button>
        </form>
      </section>
    </main>
  );
}

function TeamManagementPage({
  busy,
  projects,
  onRefresh,
  onError,
}: {
  busy: boolean;
  projects: Project[];
  onRefresh: () => Promise<void>;
  onError: (message: string) => void;
}) {
  const [newProject, setNewProject] = useState({ name: "", jira_project_key: "" });
  const [newMember, setNewMember] = useState({
    project_id: "",
    name: "",
    team: "",
    jira_email: "",
    calendar_email: "",
    slack_user_id: "",
  });

  const teamsByProject = useMemo(() => {
    return projects.map((project) => {
      const teams = project.employees.reduce<Record<string, Employee[]>>((accumulator, employee) => {
        if (!accumulator[employee.team]) {
          accumulator[employee.team] = [];
        }
        accumulator[employee.team].push(employee);
        return accumulator;
      }, {});
      return { project, teams };
    });
  }, [projects]);

  async function handleCreateProject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      await createProject(newProject);
      setNewProject({ name: "", jira_project_key: "" });
      await onRefresh();
    } catch (requestError) {
      onError(requestError instanceof Error ? requestError.message : "Failed to create project");
    }
  }

  async function handleAddMember(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      await addProjectMember(newMember.project_id, {
        name: newMember.name,
        team: newMember.team || "General",
        jira_email: newMember.jira_email,
        calendar_email: newMember.calendar_email,
        slack_user_id: newMember.slack_user_id,
      });
      setNewMember({ project_id: newMember.project_id, name: "", team: "", jira_email: "", calendar_email: "", slack_user_id: "" });
      await onRefresh();
    } catch (requestError) {
      onError(requestError instanceof Error ? requestError.message : "Failed to add team member");
    }
  }

  return (
    <section className="panel management-panel">
      <div className="panel-heading">
        <p className="eyebrow">Live Team Database</p>
        <h2>Manage projects, teams, and members</h2>
        <p className="muted">
          This page refreshes from the backend automatically and updates immediately after new projects or members are added.
        </p>
      </div>

      <div className="management-actions">
        <form className="management-form" onSubmit={handleCreateProject}>
          <h3>Add project</h3>
          <label>
            <span>Project name</span>
            <input required value={newProject.name} onChange={(event) => setNewProject({ ...newProject, name: event.target.value })} />
          </label>
          <label>
            <span>Jira project key</span>
            <input
              value={newProject.jira_project_key}
              onChange={(event) => setNewProject({ ...newProject, jira_project_key: event.target.value })}
            />
          </label>
          <button className="primary-button" disabled={busy} type="submit">
            Add project
          </button>
        </form>

        <form className="management-form" onSubmit={handleAddMember}>
          <h3>Add team member</h3>
          <label>
            <span>Project</span>
            <select
              required
              value={newMember.project_id}
              onChange={(event) => setNewMember({ ...newMember, project_id: event.target.value })}
            >
              <option value="">Choose project</option>
              {projects.map((project) => (
                <option key={project.project_id} value={project.project_id}>
                  {project.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>Member name</span>
            <input required value={newMember.name} onChange={(event) => setNewMember({ ...newMember, name: event.target.value })} />
          </label>
          <label>
            <span>Team name</span>
            <input required value={newMember.team} onChange={(event) => setNewMember({ ...newMember, team: event.target.value })} />
          </label>
          <label>
            <span>Google mail</span>
            <input
              type="email"
              value={newMember.calendar_email}
              onChange={(event) => setNewMember({ ...newMember, calendar_email: event.target.value })}
            />
          </label>
          <label>
            <span>Jira associated mail</span>
            <input
              type="email"
              value={newMember.jira_email}
              onChange={(event) => setNewMember({ ...newMember, jira_email: event.target.value })}
            />
          </label>
          <label>
            <span>Slack user ID</span>
            <input value={newMember.slack_user_id} onChange={(event) => setNewMember({ ...newMember, slack_user_id: event.target.value })} />
          </label>
          <button className="primary-button" disabled={busy} type="submit">
            Add member
          </button>
        </form>
      </div>

      <div className="project-directory">
        {teamsByProject.map(({ project, teams }) => (
          <article className="directory-project" key={project.project_id}>
            <div className="directory-project-header">
              <div>
                <h3>{project.name}</h3>
                <p>
                  Jira: <strong>{project.jira_project_key || "Not set"}</strong>
                </p>
              </div>
              <span>{project.employees.length} members</span>
            </div>

            {Object.entries(teams).map(([teamName, members]) => (
              <section className="directory-team" key={`${project.project_id}-${teamName}`}>
                <h4>{teamName}</h4>
                <div className="member-table">
                  <div className="member-table-row member-table-head">
                    <span>Name</span>
                    <span>Google mail</span>
                    <span>Jira associated mail</span>
                    <span>Slack</span>
                  </div>
                  {members.map((member) => (
                    <div className="member-table-row" key={member.employee_id}>
                      <span>{member.name}</span>
                      <span>{member.calendar_email || "Not set"}</span>
                      <span>{member.jira_email || "Not set"}</span>
                      <span>{member.slack_user_id || "Not set"}</span>
                    </div>
                  ))}
                </div>
              </section>
            ))}
          </article>
        ))}
      </div>
    </section>
  );
}

export default function App() {
  const [authenticated, setAuthenticated] = useState(false);
  const [page, setPage] = useState<AppPage>("review");
  const [result, setResult] = useState<ExtractionResponse | null>(null);
  const [reviewRows, setReviewRows] = useState<HostReviewRow[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [pushToast, setPushToast] = useState<PushToastState | null>(null);
  const [deliveryTargets, setDeliveryTargets] = useState<DeliveryTargets>(defaultDeliveryTargets);
  const [preferences, setPreferences] = useState<AppPreferences>({
    accent: "moss",
    compactMode: false,
    reduceMotion: false,
    cardReviewEnabled: true,
    darkMode: false,
  });

  async function refreshProjects() {
    try {
      const loadedProjects = await listProjects();
      setProjects(loadedProjects.length ? loadedProjects : fallbackProjects);
    } catch (requestError) {
      setProjects((current) => (current.length ? current : fallbackProjects));
      setError(requestError instanceof Error ? requestError.message : "Failed to load projects");
    }
  }

  useEffect(() => {
    if (!authenticated) {
      return;
    }
    void refreshProjects();
    const intervalId = window.setInterval(() => {
      void refreshProjects();
    }, 5000);
    return () => window.clearInterval(intervalId);
  }, [authenticated]);

  useEffect(() => {
    document.body.classList.toggle("theme-dark", preferences.darkMode);
    return () => {
      document.body.classList.remove("theme-dark");
    };
  }, [preferences.darkMode]);

  if (!authenticated) {
    return <LoginPage onLogin={() => setAuthenticated(true)} />;
  }

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
      setDeliveryTargets(defaultDeliveryTargets);
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

  function handleGlobalDeliveryTargetChange(updates: Partial<DeliveryTargets>) {
    setDeliveryTargets((current) => ({ ...current, ...updates }));
    setReviewRows((current) =>
      current.map((row) => ({
        ...row,
        delivery_targets: { ...row.delivery_targets, ...updates },
      })),
    );
  }

  async function handleConfirm() {
    if (!result) {
      return;
    }

    setBusy(true);
    setError(null);
    try {
      const confirmed = await confirmMeetingTasks(result.meeting_id, toConfirmTasks(reviewRows), deliveryTargets);
      const jiraCreated = confirmed.filter((task: any) => task.jira_status === "created").length;
      const jiraCreatedWithoutAssignee = confirmed.filter((task: any) => task.jira_status === "created_without_assignee").length;
      const calendarCreated = confirmed.filter((task: any) => task.google_calendar_status === "created").length;
      const calendarNeedsReconnect = confirmed.filter((task: any) => task.google_calendar_status === "needs_reconnect").length;
      const slackDelivered = confirmed.filter((task: any) => task.slack_delivery_status === "delivered").length;
      const slackIssues = confirmed.filter(
        (task: any) =>
          task.slack_delivery_status &&
          task.slack_delivery_status !== "delivered" &&
          task.slack_delivery_status !== "not_sent",
      );
      const jiraFailed = confirmed.filter((task: any) => task.jira_status === "failed").length;
      const calendarFailed = confirmed.filter((task: any) => task.google_calendar_status === "failed").length;
      const slackFailed = slackIssues.length;
      const calendarErrorSample =
        confirmed.find((task: any) => task.google_calendar_status === "failed" && task.google_calendar_error)
          ?.google_calendar_error ??
        confirmed.find((task: any) => task.google_calendar_status === "needs_reconnect" && task.google_calendar_error)
          ?.google_calendar_error ??
        null;
      const jiraErrorSample =
        confirmed.find((task: any) => task.jira_status === "failed" && task.jira_error)?.jira_error ?? null;
      setSuccessMessage(`Saved ${confirmed.length} selected tasks.`);
      const successLines = [
        jiraCreated ? `${jiraCreated} Jira task${jiraCreated > 1 ? "s" : ""} pushed successfully.` : "",
        jiraCreatedWithoutAssignee
          ? `${jiraCreatedWithoutAssignee} Jira task${jiraCreatedWithoutAssignee > 1 ? "s" : ""} created without assignee.`
          : "",
        calendarCreated ? `${calendarCreated} calendar invite${calendarCreated > 1 ? "s" : ""} sent successfully.` : "",
        slackDelivered ? `${slackDelivered} Slack update${slackDelivered > 1 ? "s" : ""} delivered.` : "",
      ].filter(Boolean);
      const failureLines = [
        jiraFailed ? `${jiraFailed} Jira push${jiraFailed > 1 ? "es" : ""} failed.` : "",
        calendarFailed ? `${calendarFailed} calendar push${calendarFailed > 1 ? "es" : ""} failed.` : "",
        calendarNeedsReconnect ? "Google Calendar needs to be reconnected for this project." : "",
        slackFailed
          ? `${slackFailed} Slack update${slackFailed > 1 ? "s need" : " needs"} attention (${slackIssues[0].slack_delivery_status}).`
          : "",
        jiraErrorSample ? `Jira: ${jiraErrorSample}` : "",
        calendarErrorSample ? `Calendar: ${calendarErrorSample}` : "",
      ].filter(Boolean);
      const noTasksSubmitted = confirmed.length === 0;
      setPushToast({
        title: noTasksSubmitted
          ? "No tasks selected"
          : failureLines.length
            ? "Delivery completed with issues"
            : "Delivery completed",
        successes: successLines,
        failures: failureLines,
        generatedAt: new Date().toLocaleTimeString(),
      });
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unknown confirmation error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main
      className={[
        "app-shell",
        `accent-${preferences.accent}`,
        preferences.darkMode ? "theme-dark" : "",
        preferences.compactMode ? "compact-mode" : "",
        preferences.reduceMotion ? "reduce-motion" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <nav className="app-nav">
        <strong className="brand-mark">debrief</strong>
        <div className="nav-actions">
          <button className={page === "review" ? "nav-button active" : "nav-button"} onClick={() => setPage("review")} type="button">
            Review
          </button>
          <button className={page === "teams" ? "nav-button active" : "nav-button"} onClick={() => setPage("teams")} type="button">
            Teams
          </button>
          <button className={page === "profile" ? "nav-button active" : "nav-button"} onClick={() => setPage("profile")} type="button">
            Profile
          </button>
          <button className={page === "readme" ? "nav-button active" : "nav-button"} onClick={() => setPage("readme")} type="button">
            README
          </button>
          <button className="secondary-button" onClick={() => setAuthenticated(false)} type="button">
            Logout
          </button>
        </div>
      </nav>

      <section className="status-ribbon">
        <span>signed in as leka</span>
        <strong>{page === "teams" ? "team directory" : page === "profile" ? "preferences" : page === "readme" ? "project guide" : "host review"}</strong>
        <span>{result ? `extraction: ${result.extraction_mode}` : `${projects.length} projects loaded`}</span>
      </section>

      {error ? <div className="banner banner-error">{error}</div> : null}
      {successMessage ? <div className="banner banner-success">{successMessage}</div> : null}
      {pushToast ? (
        <div className="push-toast">
          <button className="toast-close" onClick={() => setPushToast(null)} type="button">
            x
          </button>
          <div className="toast-heading">
            <strong>{pushToast.title}</strong>
            <span className="muted">{pushToast.generatedAt}</span>
          </div>
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
          {!pushToast.successes.length && !pushToast.failures.length ? (
            <div className="toast-section">
              <p>No included tasks were submitted. Select at least one member task before confirming.</p>
            </div>
          ) : null}
        </div>
      ) : null}

      {page === "teams" ? (
        <TeamManagementPage busy={busy} onError={setError} onRefresh={refreshProjects} projects={projects} />
      ) : page === "profile" ? (
        <ProfilePreferencesPage
          preferences={preferences}
          onPreferencesChange={(updates) => setPreferences((current) => ({ ...current, ...updates }))}
        />
      ) : page === "readme" ? (
        <ReadmePage />
      ) : (
        <>
          <UploadPanel busy={busy} onSubmit={handleExtract} projects={projects} />

          {result ? <TranscriptPreview result={result} /> : null}

          {result ? (
            <ConfirmationModal
              busy={busy}
              deliveryTargets={deliveryTargets}
              employees={result?.employees ?? []}
              onClose={() => setResult(null)}
              onConfirm={handleConfirm}
              onDeliveryTargetChange={handleGlobalDeliveryTargetChange}
              onRowChange={handleRowChange}
              result={result}
              rows={reviewRows}
              cardReviewEnabled={preferences.cardReviewEnabled}
            />
          ) : null}
        </>
      )}
    </main>
  );
}
