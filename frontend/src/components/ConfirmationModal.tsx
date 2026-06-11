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
  cardReviewEnabled: boolean;
}

const deliveryLabels: Array<keyof DeliveryTargets> = ["slack", "google_calendar", "jira"];

function fieldClass(level: string) {
  if (level === "medium") {
    return "confidence-medium";
  }
  if (level === "low") {
    return "confidence-low";
  }
  return "";
}

function nextIsoDate(offset: number) {
  const date = new Date();
  date.setDate(date.getDate() + offset);
  return date.toISOString().slice(0, 10);
}

function prettyDeliveryName(target: keyof DeliveryTargets) {
  if (target === "google_calendar") {
    return "GCal";
  }
  return target[0].toUpperCase() + target.slice(1);
}

function DateControl({ value, onChange }: { value: string | null; onChange: (value: string | null) => void }) {
  return (
    <div className="date-control">
      <input
        inputMode="numeric"
        placeholder="YYYY-MM-DD"
        value={value ?? ""}
        onChange={(event) => onChange(event.target.value || null)}
      />
      <div className="date-chip-row">
        <button onClick={() => onChange(nextIsoDate(1))} type="button">
          Tomorrow
        </button>
        <button onClick={() => onChange(nextIsoDate(7))} type="button">
          +1 week
        </button>
        <button onClick={() => onChange(null)} type="button">
          Clear
        </button>
      </div>
    </div>
  );
}

function DeliverySwitches({
  targets,
  onChange,
  compact = false,
}: {
  targets: DeliveryTargets;
  onChange: (updates: Partial<DeliveryTargets>) => void;
  compact?: boolean;
}) {
  return (
    <div className={compact ? "delivery-switches compact" : "delivery-switches"}>
      {deliveryLabels.map((target) => (
        <button
          className={targets[target] ? "active" : ""}
          key={target}
          onClick={() => onChange({ [target]: !targets[target] })}
          type="button"
        >
          {prettyDeliveryName(target)}
        </button>
      ))}
    </div>
  );
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
  cardReviewEnabled,
}: ConfirmationModalProps) {
  const [selectedTeam, setSelectedTeam] = useState("all");
  const [selectedEmployeeId, setSelectedEmployeeId] = useState(rows[0]?.employee_id ?? "");

  const teams = useMemo(() => {
    return ["all", ...Array.from(new Set(rows.map((row) => row.team)))];
  }, [rows]);

  const visibleRows = selectedTeam === "all" ? rows : rows.filter((row) => row.team === selectedTeam);
  const activeRow =
    visibleRows.find((row) => row.employee_id === selectedEmployeeId) ??
    visibleRows[0] ??
    null;

  const activeRowIndex = activeRow ? rows.findIndex((entry) => entry.employee_id === activeRow.employee_id) : -1;

  if (!result) {
    return null;
  }

  return (
    <section className="confirmation-modal inline-confirmation">
      <div className="modal-header">
        <div>
          <p className="eyebrow">Host confirmation</p>
          <h2>{result.project_name}</h2>
          <p className="muted">
            {employees.length} members available, {rows.filter((row) => row.included).length} selected for delivery.
          </p>
        </div>
        <button className="secondary-button" onClick={onClose} type="button">
          Clear review
        </button>
      </div>

      <section className="summary-block">
        <div className="section-heading">
          <h3>Meeting summary</h3>
          <div className="team-filter">
            {teams.map((team) => (
              <button className={selectedTeam === team ? "active" : ""} key={team} onClick={() => setSelectedTeam(team)} type="button">
                {team === "all" ? "All" : team}
              </button>
            ))}
          </div>
        </div>
        <div className="summary-row">
          {result.meeting_summary.slice(0, 5).map((line, index) => (
            <p key={`${line}-${index}`}>{line}</p>
          ))}
        </div>
      </section>

      {cardReviewEnabled ? (
        <section className="member-card-layout">
          <aside className="member-card-rail">
            {visibleRows.map((row) => (
              <button
                className={[
                  "member-select-card",
                  selectedEmployeeId === row.employee_id ? "active" : "",
                  row.included ? "included" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                key={row.employee_id}
                onClick={() => setSelectedEmployeeId(row.employee_id)}
                type="button"
              >
                <strong>{row.employee_name}</strong>
                <span>{row.team}</span>
              </button>
            ))}
          </aside>

          <div className={activeRow ? "member-detail-slide active" : "member-detail-slide"}>
            {activeRow && activeRowIndex >= 0 ? (
              <article className={activeRow.included ? "member-editor included" : "member-editor"}>
                <div className="member-heading">
                  <div className="member-include">
                    <label className="toggle-switch">
                      <input
                        checked={activeRow.included}
                        type="checkbox"
                        onChange={(event) => onRowChange(activeRowIndex, { included: event.target.checked })}
                      />
                      <span className="toggle-track"><span className="toggle-thumb" /></span>
                    </label>
                    <span className="include-label">Include</span>
                    <strong>{activeRow.employee_name}</strong>
                  </div>
                  <span>{activeRow.team}</span>
                </div>

                <label className={fieldClass(activeRow.confidence.description)}>
                  <span>Task transcript</span>
                  <textarea
                    rows={5}
                    value={activeRow.purpose}
                    onChange={(event) => onRowChange(activeRowIndex, { purpose: event.target.value })}
                    placeholder="Left empty if not mentioned in the meeting."
                  />
                </label>

                <label className={fieldClass(activeRow.confidence.deadline)}>
                  <span>Due date</span>
                  <DateControl value={activeRow.deadline} onChange={(deadline) => onRowChange(activeRowIndex, { deadline })} />
                </label>

                <div>
                  <span className="control-label">Platforms</span>
                  <DeliverySwitches
                    compact
                    targets={activeRow.delivery_targets}
                    onChange={(updates) =>
                      onRowChange(activeRowIndex, {
                        delivery_targets: { ...activeRow.delivery_targets, ...updates },
                      })
                    }
                  />
                </div>
              </article>
            ) : (
              <p className="muted">No members in this team.</p>
            )}
          </div>
        </section>
      ) : (
        <section className="member-review-grid">
          {visibleRows.map((row) => {
            const rowIndex = rows.findIndex((entry) => entry.employee_id === row.employee_id);
            return (
              <article className={row.included ? "member-editor included" : "member-editor"} key={row.employee_id}>
                <div className="member-heading">
                  <div className="member-include">
                    <label className="toggle-switch">
                      <input
                        checked={row.included}
                        type="checkbox"
                        onChange={(event) => onRowChange(rowIndex, { included: event.target.checked })}
                      />
                      <span className="toggle-track"><span className="toggle-thumb" /></span>
                    </label>
                    <span className="include-label">Include</span>
                    <strong>{row.employee_name}</strong>
                  </div>
                  <span>{row.team}</span>
                </div>

                <label className={fieldClass(row.confidence.description)}>
                  <span>Task transcript</span>
                  <textarea
                    rows={4}
                    value={row.purpose}
                    onChange={(event) => onRowChange(rowIndex, { purpose: event.target.value })}
                    placeholder="Left empty if not mentioned in the meeting."
                  />
                </label>

                <label className={fieldClass(row.confidence.deadline)}>
                  <span>Due date</span>
                  <DateControl value={row.deadline} onChange={(deadline) => onRowChange(rowIndex, { deadline })} />
                </label>

                <div>
                  <span className="control-label">Platforms</span>
                  <DeliverySwitches
                    compact
                    targets={row.delivery_targets}
                    onChange={(updates) =>
                      onRowChange(rowIndex, {
                        delivery_targets: { ...row.delivery_targets, ...updates },
                      })
                    }
                  />
                </div>
              </article>
            );
          })}
        </section>
      )}

      <section className="delivery-section">
        <div>
          <h3>Global delivery override</h3>
          <p className="muted">Toggle a platform here to apply that choice to every selected member.</p>
        </div>
        <DeliverySwitches targets={deliveryTargets} onChange={onDeliveryTargetChange} />
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
