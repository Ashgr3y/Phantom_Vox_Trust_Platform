import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Beaker, Braces, CheckCircle2, ChevronRight, FileClock, Plus, Save, ShieldCheck, SlidersHorizontal } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { ErrorState, LoadingState } from "../components/States";
import { PageHeader } from "../components/PageHeader";
import { api } from "../services/api";

interface PolicyItem {
  id: string; name: string; category: string; status: string; current_version: number; author: string; updated_at: string;
  thresholds: { low: number; monitor: number; step_up: number; critical: number; min_speech_seconds: number; consecutive_windows: number; verification_method: string; retention_rule: string };
}

export function PoliciesPage() {
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ["policies"], queryFn: api.policies });
  const policies = (query.data?.items || []) as PolicyItem[];
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [mode, setMode] = useState<"builder" | "json">("builder");
  const [testResult, setTestResult] = useState<Record<string, unknown> | null>(null);
  const selected = useMemo(() => policies.find((policy) => policy.id === selectedId) || policies[0], [policies, selectedId]);
  const [testEvidence, setTestEvidence] = useState({ synthetic_speech: 0.84, speaker_mismatch: 0.72, prosody_anomaly: 0.64, context_risk: 0.91, channel_quality: 0.88 });
  useEffect(() => { if (!selectedId && policies[0]) setSelectedId(policies[0].id); }, [policies, selectedId]);
  const test = useMutation({ mutationFn: () => api.testPolicy(selected.id, testEvidence), onSuccess: setTestResult });
  const publish = useMutation({ mutationFn: () => api.publishPolicy(selected.id), onSuccess: () => queryClient.invalidateQueries({ queryKey: ["policies"] }) });
  if (query.isLoading) return <><PageHeader title="Policies" description="Configure risk thresholds and prevention actions." /><LoadingState lines={8} /></>;
  if (query.isError || !selected) return <ErrorState message="Policy records could not be loaded" onRetry={() => query.refetch()} />;

  const jsonView = JSON.stringify({
    name: selected.name,
    version: selected.current_version,
    thresholds: selected.thresholds,
    actions: { monitor: "WARN_OPERATOR", step_up: "HOLD_AND_VERIFY", critical: "HOLD_AND_ESCALATE" },
    privacy: { retention: selected.thresholds.retention_rule },
  }, null, 2);

  return (
    <div className="page-stack">
      <PageHeader eyebrow="Versioned decision controls" title="Policies" description="Translate organizational risk appetite into readable, testable, and auditable actions." actions={<button className="button primary"><Plus size={17} />New policy</button>} />
      <div className="policy-layout">
        <aside className="panel policy-list-panel"><div className="panel-header"><div><p className="eyebrow">Templates</p><h2>Policy library</h2></div></div><div className="policy-list">{policies.map((policy) => <button key={policy.id} className={selected.id === policy.id ? "active" : ""} onClick={() => { setSelectedId(policy.id); setTestResult(null); }}><span className="policy-icon"><ShieldCheck size={18} /></span><span><strong>{policy.name}</strong><small>{policy.category} · v{policy.current_version}</small></span><em className={`small-status ${policy.status.toLowerCase()}`}>{policy.status}</em><ChevronRight size={16} /></button>)}</div></aside>
        <section className="policy-workspace">
          <article className="panel policy-editor">
            <div className="policy-titlebar"><div><div className="title-with-status"><h2>{selected.name}</h2><span className={`small-status ${selected.status.toLowerCase()}`}>{selected.status}</span></div><p>Version {selected.current_version} · Author {selected.author} · Updated {new Date(selected.updated_at).toLocaleDateString("en-IN")}</p></div><div className="segmented"><button className={mode === "builder" ? "active" : ""} onClick={() => setMode("builder")}><SlidersHorizontal size={15} />Builder</button><button className={mode === "json" ? "active" : ""} onClick={() => setMode("json")}><Braces size={15} />JSON</button></div></div>
            {mode === "builder" ? <div className="policy-builder">
              <section><div className="section-title"><div><h3>Risk thresholds</h3><p>Risk Index boundaries are configurable. They are not hardcoded in the interface.</p></div></div><div className="threshold-editor"><div className="threshold-scale"><span className="safe" style={{ width: `${selected.thresholds.low}%` }} /><span className="monitor" style={{ width: `${selected.thresholds.monitor - selected.thresholds.low}%` }} /><span className="step" style={{ width: `${selected.thresholds.critical - selected.thresholds.monitor}%` }} /><span className="critical" style={{ width: `${100 - selected.thresholds.critical}%` }} /></div><div className="threshold-values"><div><span className="safe-dot" />Low risk<strong>0–{selected.thresholds.low - 1}</strong></div><div><span className="monitor-dot" />Monitor<strong>{selected.thresholds.low}–{selected.thresholds.monitor - 1}</strong></div><div><span className="step-dot" />Step-up<strong>{selected.thresholds.monitor}–{selected.thresholds.critical - 1}</strong></div><div><span className="critical-dot" />Critical<strong>{selected.thresholds.critical}–100</strong></div></div></div></section>
              <section><div className="section-title"><div><h3>Decision safeguards</h3><p>Prevent one noisy window from causing an irreversible action.</p></div></div><div className="rule-grid"><article><span><FileClock size={18} /></span><div><small>Minimum speech</small><strong>{selected.thresholds.min_speech_seconds} seconds</strong><p>Collect enough voiced audio before scoring.</p></div></article><article><span><CheckCircle2 size={18} /></span><div><small>Consecutive windows</small><strong>{selected.thresholds.consecutive_windows} high-risk windows</strong><p>Required before a critical state.</p></div></article><article><span><ShieldCheck size={18} /></span><div><small>Verification</small><strong>{selected.thresholds.verification_method.replaceAll("_", " ")}</strong><p>Independent trusted-channel confirmation.</p></div></article><article><span><Save size={18} /></span><div><small>Retention</small><strong>{selected.thresholds.retention_rule.replaceAll("_", " ")}</strong><p>Raw audio remains disabled.</p></div></article></div></section>
              <section><div className="section-title"><div><h3>Human-readable actions</h3><p>What the system does at each decision level.</p></div></div><div className="human-rules"><div><span>When Risk Index is below {selected.thresholds.low}</span><strong>Continue monitoring</strong></div><div><span>When Risk Index reaches {selected.thresholds.low}</span><strong>Warn the operator</strong></div><div><span>When Risk Index reaches {selected.thresholds.monitor}</span><strong>Hold and verify</strong></div><div><span>When {selected.thresholds.consecutive_windows} windows reach {selected.thresholds.critical}</span><strong>Hold and escalate</strong></div></div></section>
            </div> : <pre className="json-editor" aria-label="Policy JSON">{jsonView}</pre>}
            <div className="policy-footer"><span><FileClock size={16} />Rollback history is retained after publication.</span><div><button className="button secondary">Save draft</button><button className="button primary" onClick={() => publish.mutate()} disabled={selected.status === "PUBLISHED" || publish.isPending}><ShieldCheck size={17} />{selected.status === "PUBLISHED" ? "Published" : "Publish policy"}</button></div></div>
          </article>
          <article className="panel policy-simulator"><div className="panel-header"><div><p className="eyebrow">Dry run</p><h2>Policy test simulator</h2><p>Evaluate synthetic evidence without changing live sessions.</p></div><Beaker size={24} /></div><div className="simulator-sliders">{Object.entries(testEvidence).map(([key, value]) => <label key={key}><span>{key.replaceAll("_", " ")}<strong>{Math.round(value * 100)}</strong></span><input type="range" min="0" max="100" value={Math.round(value * 100)} onChange={(event) => setTestEvidence((current) => ({ ...current, [key]: Number(event.target.value) / 100 }))} /></label>)}</div><button className="button primary wide" onClick={() => test.mutate()} disabled={test.isPending}><Beaker size={17} />{test.isPending ? "Testing…" : "Run dry-run decision"}</button>{testResult && <div className="simulation-result"><div><small>Risk Index</small><strong>{String(testResult.risk_index)}</strong></div><div><small>Decision</small><strong>{String(testResult.state).replaceAll("_", " ")}</strong></div><div><small>Action</small><strong>{String(testResult.recommended_action).replaceAll("_", " ")}</strong></div><p>{String(testResult.reason)}</p><span>Policy-based demo fusion · No live action performed</span></div>}</article>
        </section>
      </div>
    </div>
  );
}
