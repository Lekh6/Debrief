import { FormEvent, useEffect, useRef, useState } from "react";

import { Project, getGoogleAuthStartUrl } from "../lib/api";

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
  const [recordingMode, setRecordingMode] = useState<"meeting" | "closing">("meeting");
  const [recording, setRecording] = useState(false);
  const [recordingError, setRecordingError] = useState<string | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const hasInput = Boolean(transcript.trim() || meetingAudio || closingAudio);
  const canUseMic = typeof navigator !== "undefined" && Boolean(navigator.mediaDevices?.getUserMedia);

  useEffect(() => {
    return () => {
      releaseRecorderResources();
    };
  }, []);

  function releaseRecorderResources() {
    mediaRecorderRef.current = null;
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    chunksRef.current = [];
  }

  async function handleStartRecording() {
    setRecordingError(null);
    if (!canUseMic) {
      setRecordingError("Microphone recording is unavailable in this browser context.");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      streamRef.current = stream;
      mediaRecorderRef.current = recorder;
      chunksRef.current = [];

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      recorder.onerror = () => {
        setRecordingError("Recording failed. Please try again.");
      };

      recorder.onstop = () => {
        const audioBlob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
        const extension = recorder.mimeType.includes("wav") ? "wav" : "webm";
        const targetFile = new File([audioBlob], `${recordingMode}-recording.${extension}`, {
          type: audioBlob.type || "audio/webm",
        });
        if (recordingMode === "meeting") {
          setMeetingAudio(targetFile);
        } else {
          setClosingAudio(targetFile);
        }
        releaseRecorderResources();
      };

      recorder.start();
      setRecording(true);
    } catch {
      setRecordingError("Microphone access was denied or unavailable.");
      releaseRecorderResources();
    }
  }

  function handleStopRecording() {
    if (!mediaRecorderRef.current || mediaRecorderRef.current.state === "inactive") {
      setRecording(false);
      return;
    }
    mediaRecorderRef.current.stop();
    setRecording(false);
  }

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
        <h2>Capture audio or paste transcript</h2>
        <p className="muted">
          Record live meeting audio or upload files. Audio is transcribed by faster-whisper locally, then sent to Gemini for
          summary and task extraction.
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

        {projectId ? (
          <a className="oauth-link" href={getGoogleAuthStartUrl(projectId)} rel="noreferrer" target="_blank">
            Connect Google Calendar for this project
          </a>
        ) : null}

        <label>
          <span>Transcript</span>
          <textarea
            rows={12}
            value={transcript}
            onChange={(event) => setTranscript(event.target.value)}
            placeholder="Optional: paste transcript manually. Leave blank when recording or uploading audio."
          />
        </label>

        <section className="recorder-panel">
          <div className="recorder-controls">
            <label>
              <span>Record target</span>
              <select
                disabled={recording}
                value={recordingMode}
                onChange={(event) => setRecordingMode(event.target.value as "meeting" | "closing")}
              >
                <option value="meeting">Meeting recording</option>
                <option value="closing">Closing statement</option>
              </select>
            </label>
            {!recording ? (
              <button className="secondary-button" disabled={!canUseMic || busy} onClick={() => void handleStartRecording()} type="button">
                Start mic recording
              </button>
            ) : (
              <button className="secondary-button" onClick={handleStopRecording} type="button">
                Stop recording
              </button>
            )}
          </div>
          {recording ? <p className="muted">Recording in progress... click stop when done.</p> : null}
          {!recording && meetingAudio ? <p className="muted">Meeting file ready: {meetingAudio.name}</p> : null}
          {!recording && closingAudio ? <p className="muted">Closing file ready: {closingAudio.name}</p> : null}
          {!canUseMic ? <p className="muted">Mic recording is unavailable. Use file upload instead.</p> : null}
          {recordingError ? <p className="recording-error">{recordingError}</p> : null}
        </section>

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

        {!transcript.trim() && !meetingAudio && !closingAudio ? (
          <p className="recording-error">Provide at least one transcript or audio input before generating review.</p>
        ) : null}

        <button className="primary-button" disabled={busy || recording || !hasInput} type="submit">
          {busy ? "Generating review..." : "Generate host review"}
        </button>
      </form>
    </section>
  );
}
