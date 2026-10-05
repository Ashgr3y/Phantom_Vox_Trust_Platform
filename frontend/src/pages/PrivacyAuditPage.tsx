import { useMutation, useQuery } from "@tanstack/react-query";
import { CheckCircle2, Clock3, Database, FileKey2, Fingerprint, Globe2, KeyRound, LockKeyhole, RefreshCw, ShieldCheck, Trash2, VolumeX } from "lucide-react";
import { useState } from "react";
import { ErrorState, LoadingState } from "../components/States";
import { PageHeader } from "../components/PageHeader";
import { api } from "../services/api";

interface AuditItem { sequence: number; id: string; event_type: string; entity_type: string; entity_id: string; previous_state: string | null; new_state: string | null; model_version: string | null; policy_version: string | null; action_result: string; previous_hash: string; event_hash: string; created_at: string }

export function PrivacyAuditPage() {
  const [integrity, setIntegrity] = useState<Record<string, unknown> | null>(null);
  const query = useQuery({ queryKey: ["audit"], queryFn: api.audit });
  const audit = (query.data?.items || []) as AuditItem[];
  const verify = useMutation({ mutationFn: api.verifyAudit, onSuccess: setIntegrity });
  return (
    <div className="page-stack">
      <PageHeader eyebrow="Privacy, governance, and proof" title="Privacy & Audit" description="Minimize voice data, control retention, and independently verify the chain of every sensitive action." actions={<button className="button primary" onClick={() => verify.mutate()} disabled={verify.isPending}><ShieldCheck size={17} />{verify.isPending ? "Verifying…" : "Verify audit integrity"}</button>} />
      {integrity && <div className={`integrity-banner ${integrity.valid ? "valid" : "invalid"}`}><span>{integrity.valid ? <CheckCircle2 size={22} /> : <FileKey2 size={22} />}</span><div><strong>{String(integrity.message)}</strong><p>{String(integrity.checked_events)} linked events checked · Latest hash {String(integrity.latest_hash || "unavailable").slice(0, 16)}…</p></div></div>}
      <section className="privacy-controls-grid">
        <article className="panel privacy-control featured"><div className="privacy-control-head"><span><VolumeX size={22} /></span><div><h2>Raw-audio retention</h2><p>Processing stays in an ephemeral memory buffer.</p></div><label className="switch"><input type="checkbox" checked={false} readOnly aria-label="Raw audio retention disabled" /><span /></label></div><div className="control-status"><ShieldCheck size={17} /><span><strong>Off by default</strong>No call chunks are written to disk.</span></div></article>
        <article className="panel privacy-control"><div className="privacy-control-head"><span><Clock3 size={22} /></span><div><h2>Ephemeral buffer</h2><p>Short-lived stream memory</p></div></div><strong className="control-value">15 seconds</strong><small>Automatically cleared after inference</small></article>
        <article className="panel privacy-control"><div className="privacy-control-head"><span><Database size={22} /></span><div><h2>Metadata retention</h2><p>Scores, policy, and action records</p></div></div><strong className="control-value">90 days</strong><small>Configurable per tenant policy</small></article>
        <article className="panel privacy-control"><div className="privacy-control-head"><span><Globe2 size={22} /></span><div><h2>Processing region</h2><p>Deployment-bound data residency</p></div></div><strong className="control-value smaller">Local demonstration</strong><small>Choose region during enterprise deployment</small></article>
        <article className="panel privacy-control"><div className="privacy-control-head"><span><KeyRound size={22} /></span><div><h2>Encryption</h2><p>Transport and protected fields</p></div></div><strong className="control-value smaller">TLS + deployment KMS</strong><small>Development database is local</small></article>
        <article className="panel privacy-control"><div className="privacy-control-head"><span><Trash2 size={22} /></span><div><h2>Deletion workflow</h2><p>Tenant-controlled erasure</p></div></div><button className="button secondary wide">Create deletion request</button></article>
      </section>
      <section className="privacy-principles panel"><div><LockKeyhole size={24} /><span><strong>Data minimization</strong><p>Store only the evidence and decisions needed to explain a prevention action.</p></span></div><div><Fingerprint size={24} /><span><strong>Consent and revocation</strong><p>Trusted voice profiles require consent, expiry, and immediate revocation controls.</p></span></div><div><FileKey2 size={24} /><span><strong>Tamper evidence</strong><p>Each event hash includes the previous hash, state transition, model, policy, and result.</p></span></div></section>
      <section className="panel table-panel audit-table"><div className="panel-header"><div><p className="eyebrow">Hash-chained chronology</p><h2>Audit events</h2><p>This is a cryptographic hash chain, not a blockchain.</p></div><button className="button secondary" onClick={() => query.refetch()}><RefreshCw size={16} />Refresh</button></div>{query.isLoading ? <LoadingState lines={7} /> : query.isError ? <ErrorState message="Audit events could not be loaded" onRetry={() => query.refetch()} /> : <div className="table-scroll"><table><thead><tr><th>Sequence</th><th>Event</th><th>Entity</th><th>State change</th><th>Model / policy</th><th>Result</th><th>Event hash</th><th>Time</th></tr></thead><tbody>{audit.map((item) => <tr key={item.id}><td><strong>#{item.sequence}</strong></td><td>{item.event_type.replaceAll("_", " ")}</td><td><div className="primary-cell"><strong>{item.entity_type}</strong><span>{item.entity_id.slice(0, 8)}</span></div></td><td>{item.previous_state || "—"} → {item.new_state || "—"}</td><td><div className="primary-cell"><strong>{item.model_version || "—"}</strong><span>{item.policy_version || "—"}</span></div></td><td><span className="small-status active">{item.action_result}</span></td><td><code className="hash-code">{item.event_hash.slice(0, 14)}…</code></td><td>{new Date(item.created_at).toLocaleString("en-IN", { dateStyle: "short", timeStyle: "short" })}</td></tr>)}</tbody></table></div>}</section>
    </div>
  );
}
