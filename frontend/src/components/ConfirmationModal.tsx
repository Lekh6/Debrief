import { useMemo, useState } from "react";

import { DeliveryTargets, Employee, ExtractionResponse, HostReviewRow } from "../lib/api";

interface ConfirmationModalProps {
  result: ExtractionResponse | null;
  rows: HostReviewRow[];
  employees: Employee[];
  busy: boolean;
  deliveryTargets: DeliveryTargets;
  onRowChange: (index: number, updates: Partial<HostReviewRow>) => void;
  onDeliveryTargetChange: (updates: Partial<DeliveryTargets>) => void;
  onClose: () => void;
  onConfirm: () => Promise<void>;
}

function fieldClass(level: string) {
  if (level === "medium") {
    return "confidence-medium";
  }
  if (level === "low") {
    return "confidence-low";
  }
  return "";
}

export function ConfirmationModal({
  result,
  rows,
  employees,
  busy,
  deliveryTargets,
  onRowChange,
  onDeliveryTargetChange,
  onClose,
  onConfirm,
}: ConfirmationModalProps) {
  const [expandedTeams, setExpandedTeams] = useState<Record<string, boolean>>({});
  const [selectedMemberId, setSelectedMemberId] = useState<string>(rows[0]?.employee_id ?? "");

  const groupedRows = useMemo(() => {
    return rows.reduce<Record<string, HostReviewRow[]>>((accumulator, row) => {
      if (!accumulator[row.team]) {
        accumulator[row.team] = [];
      }
      accumulator[row.team].push(row);
      return accumulator;
    }, {});
  }, [rows]);

  if (!result) {
    return null;
  }

  const teams = Object.keys(groupedRows);
  const singleTeamMode = teams.length <= 1;
  const selectedRow = rows.find((row) => row.employee_id === selectedMemberId) ?? rows[0] ?? null;

  return (
    <section className="confirmation-modal inline-confirmation">
        <div className="modal-header">
          <div>
            <p className="eyebrow">Host Confirmation</p>
            <h2>{result.project_name}</h2>
            <p className="muted">
              Project ID: <strong>{result.project_id}</strong>
            </p>
          </div>
          <button className="secondary-button" onClick={onClose} type="button">
            Close
          </button>
        </div>

        <section className="summary-block">
          <h3>Meeting summary</h3>
          <ul className="summary-list">
            {result.meeting_summary.slice(0, 5).map((line, index) => (
              <li key={`${line}-${index}`}>{line}</li>
            ))}
          </ul>
        </section>

        {!singleTeamMode ? (
          <section className="team-section">
            <div className="section-heading">
              <h3>Team tasks</h3>
              <span>{teams.length} teams</span>
            </div>

            <div className="team-stack">
              {teams.map((team) => {
                const isExpanded = expandedTeams[team] ?? false;
                const teamRows = groupedRows[team];
                const teamTasks = teamRows.filter((row) => row.purpose.trim());

                return (
                  <article className="team-card" key={team}>
                    <button
                      className="team-toggle"
                      onClick={() => setExpandedTeams((current) => ({ ...current, [team]: !isExpanded }))}
                      type="button"
                    >
                      <div>
                        <h4>{team}</h4>
                        <p>{teamTasks.length ? `${teamTasks.length} active member tasks` : "No team tasks mentioned yet"}</p>
                      </div>
                      <span>{isExpanded ? "Hide members" : "Reveal members"}</span>
                    </button>

                    <div className="team-purpose-list">
                      {teamTasks.length ? (
                        teamTasks.map((row) => (
                          <p key={row.employee_id}>
                            <strong>{row.employee_name}:</strong> {row.purpose}
                          </p>
                        ))
                      ) : (
                        <p>No tasks were assigned explicitly to this team in the transcript.</p>
                      )}
                    </div>

                    {isExpanded ? (
                      <div className="member-form-grid">
                        {teamRows.map((row) => {
                          const rowIndex = rows.findIndex((entry) => entry.employee_id === row.employee_id);
                          return (
                            <div className="member-editor" key={row.employee_id}>
                              <div className="member-heading">
                                <label className="member-include">
                                  <input
                                    checked={row.included}
                                    type="checkbox"
                                    onChange={(event) => onRowChange(rowIndex, { included: event.target.checked })}
                                  />
                                  <strong>{row.employee_name}</strong>
                                </label>
                                <span>{row.team}</span>
                              </div>

                              <label className={fieldClass(row.confidence.description)}>
                                <span>Task</span>
                                <textarea
                                  rows={4}
                                  value={row.purpose}
                                  onChange={(event) => onRowChange(rowIndex, { purpose: event.target.value })}
                                  placeholder="Left empty if not mentioned in the meeting."
                                />
                              </label>

                              <label className={fieldClass(row.confidence.deadline)}>
                                <span>Deadline</span>
                                <input
                                  type="date"
                                  value={row.deadline ?? ""}
                                  onChange={(event) => onRowChange(rowIndex, { deadline: event.target.value || null })}
                                />
                              </label>
                            </div>
                          );
                        })}
                      </div>
                    ) : null}
                  </article>
                );
              })}
            </div>
          </section>
        ) : (
          <section className="team-section">
            <div className="section-heading">
              <h3>Member tasks</h3>
              <span>Single-team view</span>
            </div>

            <div className="single-team-panel">
              <label>
                <span>Member</span>
                <select value={selectedRow?.employee_id ?? ""} onChange={(event) => setSelectedMemberId(event.target.value)}>
                  {rows.map((row) => (
                    <option key={row.employee_id} value={row.employee_id}>
                      {row.employee_name}
                    </option>
                  ))}
                </select>
              </label>

              {selectedRow ? (
                <div className="member-editor single-member-editor">
                  <div className="member-heading">
                    <label className="member-include">
                      <input
                        checked={selectedRow.included}
                        type="checkbox"
                        onChange={(event) =>
                          onRowChange(rows.findIndex((entry) => entry.employee_id === selectedRow.employee_id), {
                            included: event.target.checked,
                          })
                        }
                      />
                      <strong>{selectedRow.employee_name}</strong>
                    </label>
                    <span>{selectedRow.team}</span>
                  </div>

                  <label className={fieldClass(selectedRow.confidence.description)}>
                    <span>Task</span>
                    <textarea
                      rows={5}
                      value={selectedRow.purpose}
                      onChange={(event) =>
                        onRowChange(rows.findIndex((entry) => entry.employee_id === selectedRow.employee_id), {
                          purpose: event.target.value,
                        })
                      }
                      placeholder="Left empty if not mentioned in the meeting."
                    />
                  </label>

                  <label className={fieldClass(selectedRow.confidence.deadline)}>
                    <span>Deadline</span>
                    <input
                      type="date"
                      value={selectedRow.deadline ?? ""}
                      onChange={(event) =>
                        onRowChange(rows.findIndex((entry) => entry.employee_id === selectedRow.employee_id), {
                          deadline: event.target.value || null,
                        })
                      }
                    />
                  </label>
                </div>
              ) : null}
            </div>
          </section>
        )}

        <section className="delivery-section">
          <div>
            <h3>Push destinations</h3>
            <p className="muted">Select which platforms to update on:</p>
          </div>
          <div className="delivery-options">
            <label>
              <input
                checked={deliveryTargets.google_calendar}
                type="checkbox"
                onChange={(event) => onDeliveryTargetChange({ google_calendar: event.target.checked })}
              />
              Google Calendar
            </label>
            <label>
              <input
                checked={deliveryTargets.jira}
                type="checkbox"
                onChange={(event) => onDeliveryTargetChange({ jira: event.target.checked })}
              />
              Jira
            </label>
            <label>
              <input
                checked={deliveryTargets.slack}
                type="checkbox"
                onChange={(event) => onDeliveryTargetChange({ slack: event.target.checked })}
              />
              Slack
            </label>
          </div>
        </section>

        <div className="modal-actions">
          <button className="secondary-button" onClick={onClose} type="button">
            Clear review
          </button>
          <button className="primary-button" disabled={busy} onClick={() => void onConfirm()} type="button">
            {busy ? "Preparing push..." : "Confirm selected updates"}
          </button>
        </div>
      </section>
  );
}
