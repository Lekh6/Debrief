// Debug utilities — set DEBUG_ENABLED to true and import in App.tsx to re-enable.
export const DEBUG_ENABLED = false;

export interface PushToastState {
  title: string;
  successes: string[];
  failures: string[];
  generatedAt: string;
}

export function buildPushToast(
  confirmed: any[],
  successMessage: string,
): PushToastState | null {
  if (!DEBUG_ENABLED) return null;

  const deliveryTargets = confirmed[0]?.delivery_targets ?? {};
  const jiraCreated = confirmed.filter((t: any) => t.jira_status === "created").length;
  const jiraCreatedWithoutAssignee = confirmed.filter((t: any) => t.jira_status === "created_without_assignee").length;
  const calendarCreated = confirmed.filter((t: any) => t.google_calendar_status === "created").length;
  const calendarNeedsReconnect = confirmed.filter((t: any) => t.google_calendar_status === "needs_reconnect").length;
  const slackDelivered = confirmed.filter(
    (t: any) =>
      t.slack_delivery_status &&
      t.slack_delivery_status !== "not_sent" &&
      !t.slack_delivery_status.startsWith("failed") &&
      !t.slack_delivery_status.includes("missing_") &&
      !t.slack_delivery_status.includes("skipped_"),
  ).length;
  const slackIssues = confirmed.filter(
    (t: any) =>
      t.slack_delivery_status &&
      t.slack_delivery_status !== "not_sent" &&
      (t.slack_delivery_status.startsWith("failed") ||
        t.slack_delivery_status.includes("missing_") ||
        t.slack_delivery_status.includes("skipped_")),
  );
  const jiraFailed = confirmed.filter((t: any) => t.jira_status === "failed").length;
  const calendarFailed = confirmed.filter((t: any) => t.google_calendar_status === "failed").length;
  const slackFailed = slackIssues.length;
  const calendarErrorSample =
    confirmed.find((t: any) => t.google_calendar_status === "failed" && t.google_calendar_error)
      ?.google_calendar_error ??
    confirmed.find((t: any) => t.google_calendar_status === "needs_reconnect" && t.google_calendar_error)
      ?.google_calendar_error ??
    null;
  const jiraErrorSample =
    confirmed.find((t: any) => t.jira_status === "failed" && t.jira_error)?.jira_error ?? null;

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
      ? `${slackFailed} Slack update${slackFailed > 1 ? "s need" : " needs"} attention (${slackIssues[0]?.slack_delivery_status ?? ""}).`
      : "",
    jiraErrorSample ? `Jira: ${jiraErrorSample}` : "",
    calendarErrorSample ? `Calendar: ${calendarErrorSample}` : "",
  ].filter(Boolean);
  const noTasksSubmitted = confirmed.length === 0;

  return {
    title: noTasksSubmitted
      ? "No tasks selected"
      : failureLines.length
        ? "Delivery completed with issues"
        : "Delivery completed",
    successes: successLines,
    failures: failureLines,
    generatedAt: new Date().toLocaleTimeString(),
  };
}

export function DebugPushToast({ pushToast, onClose }: { pushToast: PushToastState | null; onClose: () => void }) {
  if (!DEBUG_ENABLED || !pushToast) return null;
  return (
    <div className="push-toast">
      <button className="toast-close" onClick={onClose} type="button">x</button>
      <div className="toast-heading">
        <strong>{pushToast.title}</strong>
        <span className="muted">{pushToast.generatedAt}</span>
      </div>
      {pushToast.successes.length ? (
        <div className="toast-section toast-success">
          <strong>Succeeded</strong>
          {pushToast.successes.map((item) => <p key={item}>{item}</p>)}
        </div>
      ) : null}
      {pushToast.failures.length ? (
        <div className="toast-section toast-failure">
          <strong>Failed</strong>
          {pushToast.failures.map((item) => <p key={item}>{item}</p>)}
        </div>
      ) : null}
      {!pushToast.successes.length && !pushToast.failures.length ? (
        <div className="toast-section">
          <p>No included tasks were submitted. Select at least one member task before confirming.</p>
        </div>
      ) : null}
    </div>
  );
}

export function DebugBanners({ error, successMessage }: { error: string | null; successMessage: string | null }) {
  if (!DEBUG_ENABLED) return null;
  return (
    <>
      {error ? <div className="banner banner-error">{error}</div> : null}
      {successMessage ? <div className="banner banner-success">{successMessage}</div> : null}
    </>
  );
}
