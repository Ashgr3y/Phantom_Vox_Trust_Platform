import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  AlertOctagon,
  BadgeCheck,
  CirclePause,
  CirclePlay,
  Clock3,
  FileAudio,
  Fingerprint,
  Headphones,
  Languages,
  LockKeyhole,
  Mic2,
  PhoneCall,
  Radio,
  RefreshCcw,
  ShieldAlert,
  ShieldCheck,
  Siren,
  Square,
  Upload,
  UserRound,
  Wifi,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Line, LineChart, CartesianGrid, Legend, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useSearchParams } from "react-router-dom";
import { Modal } from "../components/Modal";
import { PageHeader } from "../components/PageHeader";
import { RiskBadge } from "../components/RiskBadge";
import { RiskGauge } from "../components/RiskGauge";
import { ScoreBar } from "../components/ScoreBar";
import { useSessionSocket } from "../hooks/useSessionSocket";
import { api } from "../services/api";
import type { Evidence, SessionSnapshot } from "../types";

const scenarioOptions = [
  { id: "mid_call_clone", label: "Mid-call clone", detail: "Genuine start, cloned voice appears later", icon: Siren },
  { id: "genuine", label: "Genuine caller", detail: "Strong identity and low synthetic evidence", icon: BadgeCheck },
  { id: "poor_quality", label: "Poor audio", detail: "System abstains instead of approving", icon: Wifi },
  { id: "high_context_uncertain", label: "High-risk context", detail: "Context triggers step-up despite uncertainty", icon: ShieldAlert },
];

const evidenceIcons: Record<string, typeof Fingerprint> = {
  synthetic_speech: Radio,
  speaker_mismatch: Fingerprint,
  prosody_anomaly: Headphones,
  context_risk: ShieldAlert,
  channel_quality: Wifi,
  out_of_distribution: AlertOctagon,
};

const evidenceFallback: Evidence[] = [
  ["synthetic_speech", "Synthetic Speech"], ["speaker_mismatch", "Speaker Identity"], ["prosody_anomaly", "Prosody & Behavior"],
  ["context_risk", "Context Risk"], ["channel_quality", "Channel Quality"], ["out_of_distribution", "Out-of-Distribution"],
].map(([name, label]) => ({ name, label, score: 0, quality: 0, available: false, explanation: "Waiting for sufficient speech evidence", model_version: "Not evaluated" }));

export function LiveGuardPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [scenario, setScenario] = useState(searchParams.get("demo") || "mid_call_clone");
  const [snapshot, setSnapshot] = useState<SessionSnapshot | null>(null);
  const [paused, setPaused] = useState(false);
  const [verificationOpen, setVerificationOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [chartData, setChartData] = useState<Array<Record<string, number | string>>>([]);
  const uploadRef = useRef<HTMLInputElement>(null);
  const startedRef = useRef(false);
  const queryClient = useQueryClient();
  const sessionId = searchParams.get("session");

  const acceptSnapshot = useCallback((next: SessionSnapshot) => {
    if (paused) return;
    setSnapshot(next);
    const latest = next.timeline[next.timeline.length - 1];
    if (latest) {
      const point: Record<string, number | string> = {
        sequence: latest.sequence + 1,
        time: `${latest.sequence + 1}s`,
        risk: latest.risk_index,
      };
      next.evidence.forEach((item) => { point[item.name] = Math.round(item.score * 100); });
      setChartData((current) => {
        const without = current.filter((item) => item.sequence !== point.sequence);
        return [...without, point].sort((a, b) => Number(a.sequence) - Number(b.sequence));
      });
    }
    if (next.verification) setVerificationOpen(true);
  }, [paused]);

  const socketStatus = useSessionSocket(sessionId, acceptSnapshot);

  useEffect(() => {
    if (!sessionId) return;
    api.session(sessionId).then(acceptSnapshot).catch((error) => setMessage(error instanceof Error ? error.message : "Unable to open session"));
  }, [sessionId, acceptSnapshot]);

  const startMutation = useMutation({
    mutationFn: () => api.startDemo(scenario, true),
    onSuccess: (data) => {
      setChartData([]);
      setSnapshot(data);
      setSearchParams({ session: data.session.id });
      setMessage("Judge demo started. Watch recent-window evidence change the decision.");
    },
    onError: (error) => setMessage(error instanceof Error ? error.message : "Unable to start demo"),
  });

  useEffect(() => {
    const requested = searchParams.get("demo");
    if (requested && !sessionId && !startedRef.current) {
      startedRef.current = true;
      setScenario(requested);
      api.startDemo(requested, true).then((data) => {
        setSnapshot(data);
        setSearchParams({ session: data.session.id });
      }).catch((error) => setMessage(error instanceof Error ? error.message : "Unable to start demo"));
    }
  }, [searchParams, sessionId, setSearchParams]);

  const reset = async () => {
    if (sessionId) await api.stopSession(sessionId).catch(() => undefined);
    setSnapshot(null); setChartData([]); setSearchParams({}); setVerificationOpen(false); setMessage("Session reset. Choose a scenario to begin again.");
    void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
  };

  const uploadAudio = async (file: File) => {
    if (!sessionId) { setMessage("Start a monitoring session before uploading audio."); return; }
    try {
      const result = await api.analyzeAudio(sessionId, file);
      setMessage(`RawNetLite analysis completed. Evidence score: ${Math.round(Number(result.synthetic_score) * 100)}. This is not a calibrated probability.`);
    } catch (error) { setMessage(error instanceof Error ? error.message : "Audio analysis failed"); }
  };

  const completeVerification = async (result: "PASSED" | "FAILED") => {
    if (!snapshot?.verification) return;
    await api.completeVerification(snapshot.verification.id, result);
    setVerificationOpen(false);
    setMessage(result === "PASSED" ? "Trusted verification passed. The stored workflow state was updated." : "Verification failed. The incident remains escalated.");
    const updated = await api.session(snapshot.session.id);
    acceptSnapshot(updated);
  };

  const activeSession = snapshot?.session;
  const evidence = snapshot?.evidence.length ? snapshot.evidence : evidenceFallback;
  return (
    <div className="page-stack live-guard-page">
      <PageHeader
        eyebrow="Continuous protection"
        title="Live Guard"
        description="Follow evidence as it arrives, then move from detection to a stored prevention action."
        actions={<div className="connection-cluster"><span className={`connection-pill ${socketStatus}`}><span className="status-light" />{socketStatus === "connected" ? "Live stream connected" : socketStatus === "idle" ? "No active stream" : socketStatus}</span><span className="demo-chip">Demo mode</span></div>}
      />

      <section className="panel session-launcher">
        <div className="launcher-top"><div><p className="eyebrow">Input and scenario</p><h2>Start a protected conversation</h2></div><div className="input-modes"><button className="mode-chip active"><Radio size={15} />Judge demo</button><button className="mode-chip" onClick={() => uploadRef.current?.click()}><Upload size={15} />Upload audio</button><button className="mode-chip" disabled title="Requires browser media permission"><Mic2 size={15} />Microphone</button><button className="mode-chip" disabled title="Configure an external adapter first"><PhoneCall size={15} />Twilio / SIP</button></div></div>
        <div className="scenario-row">{scenarioOptions.map(({ id, label, detail, icon: Icon }) => <button key={id} className={`scenario-card ${scenario === id ? "selected" : ""}`} onClick={() => setScenario(id)} disabled={!!sessionId}><Icon size={20} /><span><strong>{label}</strong><small>{detail}</small></span>{scenario === id && <ShieldCheck className="selection-check" size={17} />}</button>)}</div>
        <div className="launcher-controls">
          <div className="field-row"><label>Claimed identity<select disabled={!!sessionId} defaultValue="Aarav Mehta"><option>Aarav Mehta</option><option>Kabir Singh</option><option>Sanjay Patel</option></select></label><label>Language<select disabled={!!sessionId} defaultValue="English - Indian"><option>English - Indian</option><option>Hindi</option><option>Marathi</option><option>Gujarati</option></select></label><label>Transaction value<input disabled={!!sessionId} defaultValue="₹48,50,000" /></label></div>
          <div className="control-buttons">{!sessionId ? <button className="button primary" onClick={() => startMutation.mutate()} disabled={startMutation.isPending}><CirclePlay size={17} />{startMutation.isPending ? "Starting…" : "Start monitoring"}</button> : <><button className="button secondary" onClick={() => setPaused((value) => !value)}>{paused ? <CirclePlay size={17} /> : <CirclePause size={17} />}{paused ? "Resume view" : "Pause view"}</button><button className="button danger-ghost" onClick={reset}><Square size={15} />Stop & reset</button></>}</div>
        </div>
        <input ref={uploadRef} className="visually-hidden" type="file" accept=".wav,.flac,.ogg,audio/*" onChange={(event) => event.target.files?.[0] && uploadAudio(event.target.files[0])} />
      </section>

      {message && <div className="inline-message" role="status"><ShieldCheck size={17} /><span>{message}</span><button onClick={() => setMessage("")} aria-label="Dismiss message">×</button></div>}

      <section className="live-primary-grid">
        <article className="panel trust-panel">
          <div className="panel-header"><div><p className="eyebrow">Current decision</p><h2>{activeSession ? activeSession.claimed_identity : "No active session"}</h2></div>{activeSession && <span className="session-id">{activeSession.id.slice(0, 8).toUpperCase()}</span>}</div>
          {activeSession ? <>
            <div className="trust-overview"><RiskGauge value={activeSession.risk_index} state={activeSession.state} /><div className="session-facts"><div><UserRound size={17} /><span><small>Claimed identity</small><strong>{activeSession.claimed_identity}</strong></span></div><div><Languages size={17} /><span><small>Language</small><strong>{activeSession.language}</strong></span></div><div><Headphones size={17} /><span><small>Source</small><strong>{activeSession.source}</strong></span></div><div><Clock3 size={17} /><span><small>Duration</small><strong>{activeSession.duration_seconds}s</strong></span></div></div></div>
            <div className="recommendation-box"><span className={activeSession.state === "CRITICAL" ? "critical-icon" : "recommendation-icon"}>{activeSession.state === "CRITICAL" ? <AlertOctagon size={22} /> : <ShieldCheck size={22} />}</span><div><small>Recommended action</small><strong>{snapshot?.timeline.at(-1)?.recommended_action?.replaceAll("_", " ") || "CONTINUE MONITORING"}</strong><p>{activeSession.state === "INSUFFICIENT_AUDIO" ? "Use a secure callback because audio quality is below the decision gate." : activeSession.state === "CRITICAL" ? "Keep the sensitive action on hold and escalate to a supervisor." : "The policy engine will react to recent consecutive suspicious windows."}</p></div></div>
          </> : <div className="guard-empty"><ShieldCheck size={42} /><h3>Ready to protect a conversation</h3><p>Select one of the four reproducible scenarios above. The mid-call clone scenario shows the complete prevention workflow.</p></div>}
        </article>

        <aside className="panel action-panel">
          <div className="panel-header"><div><p className="eyebrow">Prevention workflow</p><h2>Action state</h2></div></div>
          <div className="action-state-list">
            <div><span className="action-step">1</span><span><small>Transaction</small><strong>{snapshot?.transaction?.status?.replaceAll("_", " ") || "Not started"}</strong></span>{snapshot?.transaction?.status === "ON_HOLD" && <LockKeyhole size={18} className="amber" />}</div>
            <div><span className="action-step">2</span><span><small>Verification</small><strong>{snapshot?.verification?.status || "Not required"}</strong></span>{snapshot?.verification && <Fingerprint size={18} className="blue" />}</div>
            <div><span className="action-step">3</span><span><small>Incident</small><strong>{snapshot?.incident_id ? "Created" : "No incident"}</strong></span>{snapshot?.incident_id && <ShieldAlert size={18} className="red" />}</div>
            <div><span className="action-step">4</span><span><small>Audit</small><strong>{activeSession ? "Recorded" : "Waiting"}</strong></span><ShieldCheck size={18} className="green" /></div>
          </div>
          {snapshot?.transaction && <div className="transaction-card"><small>Sensitive action</small><strong>{activeSession?.transaction_type}</strong><b>{new Intl.NumberFormat("en-IN", { style: "currency", currency: snapshot.transaction.currency, maximumFractionDigits: 0 }).format(snapshot.transaction.value)}</b><span>{snapshot.transaction.reference}</span></div>}
          <button className="button primary wide" disabled={!snapshot?.verification} onClick={() => setVerificationOpen(true)}><Fingerprint size={17} />{snapshot?.verification ? "Open secure verification" : "Verification not required"}</button>
        </aside>
      </section>

      <section className="panel timeline-panel">
        <div className="panel-header"><div><p className="eyebrow">Sequential decisioning</p><h2>Recent-window risk timeline</h2><p>Recent evidence is weighted more strongly. Two consecutive high-risk windows are required for a critical action.</p></div><div className="threshold-legend"><span><i className="low" />Low 35</span><span><i className="step" />Step-up 60</span><span><i className="critical" />Critical 80</span></div></div>
        <div className="live-chart"><ResponsiveContainer width="100%" height="100%"><LineChart data={chartData} margin={{ top: 8, right: 14, bottom: 2, left: -18 }}><CartesianGrid stroke="var(--chart-grid)" strokeDasharray="4 6" vertical={false} /><XAxis dataKey="time" stroke="var(--text-muted)" tickLine={false} axisLine={false} /><YAxis domain={[0, 100]} stroke="var(--text-muted)" tickLine={false} axisLine={false} /><Tooltip contentStyle={{ background: "var(--surface-raised)", border: "1px solid var(--border)", borderRadius: 10 }} /><Legend /><ReferenceLine y={60} stroke="#F59E0B" strokeDasharray="5 5" /><ReferenceLine y={80} stroke="#EF4444" strokeDasharray="5 5" /><Line type="monotone" dataKey="risk" name="Overall Risk" stroke="#2563EB" strokeWidth={3} dot={{ r: 4 }} connectNulls /><Line type="monotone" dataKey="synthetic_speech" name="Synthetic" stroke="#EF4444" strokeWidth={1.8} dot={false} connectNulls /><Line type="monotone" dataKey="speaker_mismatch" name="Speaker mismatch" stroke="#7C3AED" strokeWidth={1.8} dot={false} connectNulls /><Line type="monotone" dataKey="context_risk" name="Context" stroke="#F59E0B" strokeWidth={1.8} dot={false} connectNulls /></LineChart></ResponsiveContainer></div>
      </section>

      <section className="evidence-section"><div className="section-heading"><div><p className="eyebrow">Explainable evidence</p><h2>Why the Risk Index changed</h2></div><p>Demo-generated evidence is labelled by its model or rule version.</p></div><div className="evidence-grid">{evidence.map((item) => { const Icon = evidenceIcons[item.name] || Radio; return <article className={`evidence-card ${!item.available ? "unavailable" : ""}`} key={item.name}><div className="evidence-card-header"><span><Icon size={19} /></span><div><strong>{item.label}</strong><small>{item.available ? item.model_version : "Unavailable"}</small></div><b>{item.available ? Math.round(item.score * 100) : "—"}</b></div><ScoreBar value={item.available ? item.score : 0} label={`${item.label} score`} /><p>{item.explanation}</p><div className="evidence-footer"><span>{item.available ? "Evidence available" : "Not used in decision"}</span><span>Quality {Math.round(item.quality * 100)}</span></div></article>; })}</div></section>

      <section className="panel event-stream-panel"><div className="panel-header"><div><p className="eyebrow">Stored chronology</p><h2>Session event stream</h2></div></div><div className="event-stream">{snapshot?.timeline.length ? snapshot.timeline.map((item, index) => <div key={item.sequence}><span className={`event-dot ${item.state.toLowerCase()}`} /><time>{`${item.sequence + 1}s`}</time><span><strong>{index === 0 ? "First sufficient speech analyzed" : item.state.replaceAll("_", " ")}</strong><small>Risk {Math.round(item.risk_index)} · {item.actual_action.replaceAll("_", " ")}</small></span></div>) : <div className="event-placeholder"><Radio size={20} />Events will appear after monitoring begins.</div>}</div></section>

      <Modal open={verificationOpen && !!snapshot?.verification} onClose={() => setVerificationOpen(false)} title="Trusted-device verification" description="A separate trusted channel is required before the sensitive action can continue.">
        {snapshot?.verification && <div className="verification-dialog"><div className="verification-reason"><ShieldAlert size={22} /><span><strong>Why verification was triggered</strong><p>{snapshot.verification.reason}</p></span></div><div className="verification-meta"><div><small>Destination</small><strong>{snapshot.verification.destination_masked}</strong></div><div><small>Method</small><strong>{snapshot.verification.method.replaceAll("_", " ")}</strong></div><div><small>Status</small><strong>{snapshot.verification.status}</strong></div><div><small>Expires</small><strong>3 minutes</strong></div></div><div className="otp-demo"><label>Demonstration confirmation code</label><div>{[7, 4, 2, 9, 1, 8].map((digit, index) => <span key={index}>{digit}</span>)}</div><p>This code is seeded for the offline demo. No SMS is actually sent.</p></div><div className="modal-actions"><button className="button danger-ghost" onClick={() => completeVerification("FAILED")}>Simulate failure</button><button className="button primary" onClick={() => completeVerification("PASSED")}><ShieldCheck size={17} />Approve on trusted device</button></div></div>}
      </Modal>
    </div>
  );
}
