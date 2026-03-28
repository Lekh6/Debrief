import { FormEvent, useState } from "react";

import { Project } from "../lib/api";

interface UploadPanelProps {
  projects: Project[];
  onSubmit: (payload: {
    projectId: string;
    meetingTranscript?: string;
    closingTranscript?: string;
    meetingAudio?: File | null;
    closingAudio?: File | null;
  }) => Promise<void>;
  busy: boolean;
}

export function UploadPanel({ projects, onSubmit, busy }: UploadPanelProps) {
  const [projectId, setProjectId] = useState("");
  const [transcript, setTranscript] = useState("");
  const [meetingAudio, setMeetingAudio] = useState<File | null>(null);
  const [closingAudio, setClosingAudio] = useState<File | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSubmit({
      projectId,
      meetingTranscript: transcript || undefined,
      closingTranscript: transcript || undefined,
      meetingAudio,
      closingAudio,
    });
  }

  return (
    <section className="panel upload-panel">
      <div className="panel-heading">
        <p className="eyebrow">Phase 1 Intake</p>
        <h2>Paste a meeting transcript</h2>
        <p className="muted">
          For the demo, paste one transcript and we will use it as the primary meeting context and decision summary input.
        </p>
      </div>

      <form className="upload-form" onSubmit={handleSubmit}>
        <label>
          <span>Project</span>
          <select required value={projectId} onChange={(event) => setProjectId(event.target.value)}>
            <option value="">Select demo project</option>
            {projects.map((project) => (
              <option key={project.project_id} value={project.project_id}>
                {project.name} | {project.project_id}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span>Transcript</span>
          <textarea
            required
            rows={12}
            value={transcript}
            onChange={(event) => setTranscript(event.target.value)}
            placeholder="Paste the meeting transcript here. Mention assignees, responsibilities, and deadlines if available."
          />
        </label>

        <details className="demo-details">
          <summary>Optional file inputs</summary>
          <div className="file-grid">
            <label>
              <span>Meeting recording</span>
              <input type="file" accept="audio/*,.txt" onChange={(event) => setMeetingAudio(event.target.files?.[0] ?? null)} />
            </label>

            <label>
              <span>Closing statement</span>
              <input type="file" accept="audio/*,.txt" onChange={(event) => setClosingAudio(event.target.files?.[0] ?? null)} />
            </label>
          </div>
        </details>

        <button className="primary-button" disabled={busy} type="submit">
          {busy ? "Generating review..." : "Generate host review"}
        </button>
      </form>
    </section>
  );
}
