import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Download, Filter, Search, ShieldAlert, UserCheck } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { EmptyState, ErrorState, LoadingState } from "../components/States";
import { Modal } from "../components/Modal";
import { PageHeader } from "../components/PageHeader";
import { api } from "../services/api";
import type { Incident } from "../types";

interface IncidentDetail extends Incident {
  timeline: Array<{ risk: number; state: string; time: string }>;
  actions: Array<{ type: string; status: string; details: string; time: string }>;
  raw_audio_available: boolean;
  audit_integrity: string;
}

export function InvestigationsPage() {
  const [params, setParams] = useSearchParams();
  const [search, setSearch] = useState(params.get("search") || "");
  const [severity, setSeverity] = useState("");
  const [status, setStatus] = useState("");
  const incidentId = params.get("incident");
  const queryClient = useQueryClient();
  const queryString = useMemo(() => {
    const next = new URLSearchParams();
    if (search) next.set("search", search);
    if (severity) next.set("severity", severity);
    if (status) next.set("status", status);
    const value = next.toString();
    return value ? `?${value}` : "";
  }, [search, severity, status]);
  const listQuery = useQuery({ queryKey: ["incidents", queryString], queryFn: () => api.incidents(queryString) });
  const detailQuery = useQuery({ queryKey: ["incident", incidentId], queryFn: () => api.incident(incidentId!), enabled: !!incidentId });
  const incidents = (listQuery.data?.items || []) as Incident[];
  const detail = detailQuery.data as unknown as IncidentDetail | undefined;
  const resolve = useMutation({
    mutationFn: (disposition: string) => api.resolveIncident(incidentId!, disposition),
    onSuccess: () => { void queryClient.invalidateQueries({ queryKey: ["incidents"] }); void queryClient.invalidateQueries({ queryKey: ["incident", incidentId] }); },
  });

  useEffect(() => {
    const value = params.get("search");
    if (value !== null) setSearch(value);
  }, [params]);

  const close = () => {
    const next = new URLSearchParams(params);
    next.delete("incident");
    setParams(next);
  };
  const exportReport = () => {
    if (!detail) return;
    const safe = { ...detail, raw_audio_available: false, export_notice: "Privacy-safe metadata report. No raw audio included." };
    const url = URL.createObjectURL(new Blob([JSON.stringify(safe, null, 2)], { type: "application/json" }));
    const anchor = document.createElement("a");
    anchor.href = url; anchor.download = `phantom-vox-incident-${detail.id.slice(0, 8)}.json`; anchor.click(); URL.revokeObjectURL(url);
  };

  return (
    <div className="page-stack">
      <PageHeader eyebrow="Case workspace" title="Investigations" description="Review explainable evidence, verify the prevention trail, and record an analyst disposition." actions={<button className="button secondary"><Download size={17} />Export filtered list</button>} />
      <section className="filter-bar panel">
        <label className="search-field"><Search size={17} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search identity or incident ID" /></label>
        <label><Filter size={16} /><select value={severity} onChange={(event) => setSeverity(event.target.value)}><option value="">All severities</option><option>CRITICAL</option><option>HIGH</option><option>MEDIUM</option></select></label>
        <label><select value={status} onChange={(event) => setStatus(event.target.value)}><option value="">All states</option><option>OPEN</option><option>UNDER_REVIEW</option><option>RESOLVED</option></select></label>
        <span className="result-count">{incidents.length} incidents</span>
      </section>
      <section className="panel table-panel investigations-table">
        {listQuery.isLoading ? <LoadingState lines={7} /> : listQuery.isError ? <ErrorState message="Incident records could not be loaded" onRetry={() => listQuery.refetch()} /> : !incidents.length ? <EmptyState title="No incidents match these filters" description="Clear a filter or start the high-risk judge scenario to create one." /> : <div className="table-scroll"><table><thead><tr><th>Incident</th><th>Claimed identity</th><th>Source</th><th>Language</th><th>Peak risk</th><th>Trigger</th><th>Prevented action</th><th>Verification</th><th>Severity</th><th>Status</th><th>Analyst</th></tr></thead><tbody>{incidents.map((incident) => <tr key={incident.id} className="clickable-row" onClick={() => { const next = new URLSearchParams(params); next.set("incident", incident.id); setParams(next); }}><td><div className="primary-cell"><strong>PV-{incident.id.slice(0, 6).toUpperCase()}</strong><span>{new Date(incident.created_at).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" })}</span></div></td><td>{incident.claimed_identity}</td><td>{incident.source}</td><td>{incident.language}</td><td><strong className={`risk-number ${incident.peak_risk >= 80 ? "critical" : "warning"}`}>{Math.round(incident.peak_risk)}</strong></td><td className="truncate-cell">{incident.trigger}</td><td className="truncate-cell">{incident.prevented_action}</td><td><span className={`small-status ${incident.verification_result.toLowerCase()}`}>{incident.verification_result}</span></td><td><span className={`severity-badge ${incident.severity.toLowerCase()}`}>{incident.severity}</span></td><td>{incident.status.replaceAll("_", " ")}</td><td>{incident.assigned_analyst}</td></tr>)}</tbody></table></div>}
      </section>

      <Modal open={!!incidentId} onClose={close} title={detail ? `Incident PV-${detail.id.slice(0, 8).toUpperCase()}` : "Loading incident"} description={detail?.summary}>
        {detailQuery.isLoading || !detail ? <LoadingState lines={6} /> : <div className="incident-detail">
          <div className="incident-summary-grid"><article><small>Peak Risk Index</small><strong className="critical-text">{Math.round(detail.peak_risk)}</strong><span>{detail.severity} severity</span></article><article><small>Prevented action</small><strong>{detail.prevented_action}</strong><span>{detail.verification_result} verification</span></article><article><small>Audit integrity</small><strong className="green-text"><CheckCircle2 size={17} />{detail.audit_integrity}</strong><span>No raw audio retained</span></article></div>
          <section className="detail-section"><div className="section-title"><h3>Risk timeline</h3><span>{detail.model_version}</span></div><div className="detail-chart"><ResponsiveContainer width="100%" height="100%"><AreaChart data={detail.timeline}><defs><linearGradient id="incidentRisk" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#EF4444" stopOpacity={0.35} /><stop offset="100%" stopColor="#EF4444" stopOpacity={0.02} /></linearGradient></defs><CartesianGrid stroke="var(--chart-grid)" strokeDasharray="4 6" vertical={false} /><XAxis dataKey="time" hide /><YAxis domain={[0, 100]} tickLine={false} axisLine={false} /><Tooltip contentStyle={{ background: "var(--surface-raised)", border: "1px solid var(--border)", borderRadius: 10 }} /><Area type="monotone" dataKey="risk" stroke="#EF4444" strokeWidth={2.5} fill="url(#incidentRisk)" /></AreaChart></ResponsiveContainer></div></section>
          <section className="detail-section"><div className="section-title"><h3>Action trail</h3><span>{detail.actions.length} stored actions</span></div><div className="action-trail">{detail.actions.length ? detail.actions.map((action, index) => <div key={`${action.type}-${index}`}><span><ShieldAlert size={16} /></span><div><strong>{action.type.replaceAll("_", " ")}</strong><p>{action.details || "Action completed and recorded"}</p></div><em>{action.status}</em></div>) : <p>No explicit action records are attached to this seeded case.</p>}</div></section>
          <section className="detail-section analyst-note"><div className="section-title"><h3>Analyst notes</h3><span>{detail.assigned_analyst}</span></div><p>{detail.analyst_notes || "No analyst note has been added."}</p></section>
          <div className="modal-actions split"><button className="button secondary" onClick={exportReport}><Download size={17} />Privacy-safe report</button><div><button className="button secondary" onClick={() => resolve.mutate("INCONCLUSIVE")}>Mark inconclusive</button><button className="button danger-ghost" onClick={() => resolve.mutate("FRAUD")}><ShieldAlert size={17} />Confirm fraud</button><button className="button primary" onClick={() => resolve.mutate("GENUINE")}><UserCheck size={17} />Confirm genuine</button></div></div>
        </div>}
      </Modal>
    </div>
  );
}
