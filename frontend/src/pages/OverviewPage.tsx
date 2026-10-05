import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  ArrowRight,
  BadgeCheck,
  Ban,
  Headphones,
  HeartPulse,
  LockKeyhole,
  Radio,
  ShieldAlert,
  ShieldCheck,
} from "lucide-react";
import { Area, AreaChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useNavigate } from "react-router-dom";
import { ErrorState, LoadingState } from "../components/States";
import { PageHeader } from "../components/PageHeader";
import { RiskBadge } from "../components/RiskBadge";
import { StatCard } from "../components/StatCard";
import { api } from "../services/api";

const pieColors = ["#10B981", "#F59E0B", "#EF4444", "#2563EB", "#22D3EE", "#7C3AED"];

const formatCurrency = (value: number, currency = "INR") =>
  new Intl.NumberFormat("en-IN", { style: "currency", currency, maximumFractionDigits: 0 }).format(value);

export function OverviewPage() {
  const navigate = useNavigate();
  const query = useQuery({ queryKey: ["dashboard"], queryFn: api.dashboard, refetchInterval: 20_000 });
  if (query.isLoading) return <><PageHeader title="Operations overview" description="Voice-risk operations and prevention status." /><LoadingState lines={7} /></>;
  if (query.isError || !query.data) return <ErrorState message={query.error instanceof Error ? query.error.message : "Dashboard data is unavailable"} onRetry={() => query.refetch()} />;
  const data = query.data;
  const verification = data.kpis.verification_success_rate;
  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="Operations command centre"
        title="Voice trust, at a glance"
        description="Monitor active protection, intervene in risky conversations, and verify every prevention action."
        actions={<button className="button primary" onClick={() => navigate("/live-guard?demo=mid_call_clone")}><Radio size={17} />Start judge demo</button>}
      />
      <div className="notice-strip"><span className="demo-chip">Seeded demo data</span><p>Metrics below are fictional demonstration records, not production performance claims.</p></div>
      <section className="stats-grid" aria-label="Key metrics">
        <StatCard label="Active protected sessions" value={data.kpis.active_sessions} detail="Across configured channels" icon={Headphones} tone="blue" />
        <StatCard label="Requiring attention" value={data.kpis.requiring_attention} detail="Operator review or step-up" icon={ShieldAlert} tone="amber" />
        <StatCard label="Actions prevented" value={data.kpis.actions_prevented} detail="Held or blocked workflows" icon={Ban} tone="red" />
        <StatCard label="Average Risk Index" value={data.kpis.average_risk} detail="Active sessions only" icon={Activity} tone="cyan" />
        <StatCard label="Verification success" value={verification === null ? "No result" : `${verification}%`} detail="Completed verifications" icon={BadgeCheck} tone="green" />
        <StatCard label="Service health" value="Operational" detail="API and session engine" icon={HeartPulse} tone="green" />
      </section>

      <section className="overview-grid">
        <article className="panel chart-panel wide-panel">
          <div className="panel-header"><div><p className="eyebrow">Live activity</p><h2>Risk Index across recent sessions</h2></div><span className="legend-note"><span className="legend-swatch blue" />Risk Index</span></div>
          <div className="chart-box" aria-label="Recent Risk Index activity chart">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data.risk_activity} margin={{ top: 12, right: 10, left: -20, bottom: 0 }}>
                <defs><linearGradient id="riskFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#2563EB" stopOpacity={0.35} /><stop offset="100%" stopColor="#2563EB" stopOpacity={0.02} /></linearGradient></defs>
                <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="4 6" vertical={false} />
                <XAxis dataKey="time" stroke="var(--text-muted)" tickLine={false} axisLine={false} fontSize={12} />
                <YAxis domain={[0, 100]} stroke="var(--text-muted)" tickLine={false} axisLine={false} fontSize={12} />
                <Tooltip contentStyle={{ background: "var(--surface-raised)", border: "1px solid var(--border)", borderRadius: 10 }} />
                <Area type="monotone" dataKey="risk" stroke="#2563EB" strokeWidth={2.5} fill="url(#riskFill)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </article>
        <article className="panel distribution-panel">
          <div className="panel-header"><div><p className="eyebrow">Current mix</p><h2>Session states</h2></div></div>
          <div className="distribution-content">
            <div className="donut-chart"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={data.state_distribution} dataKey="value" nameKey="name" innerRadius={52} outerRadius={74} paddingAngle={4}>{data.state_distribution.map((entry, index) => <Cell key={entry.name} fill={pieColors[index % pieColors.length]} />)}</Pie><Tooltip contentStyle={{ background: "var(--surface-raised)", border: "1px solid var(--border)", borderRadius: 10 }} /></PieChart></ResponsiveContainer><div className="donut-center"><strong>{data.active_sessions.length}</strong><span>Active</span></div></div>
            <div className="chart-legend">{data.state_distribution.map((entry, index) => <div key={entry.name}><span style={{ background: pieColors[index % pieColors.length] }} /><em>{entry.name.replaceAll("_", " ")}</em><strong>{entry.value}</strong></div>)}</div>
          </div>
        </article>
      </section>

      <section className="content-grid two-one">
        <article className="panel table-panel">
          <div className="panel-header"><div><p className="eyebrow">Live protection</p><h2>Active sessions</h2></div><button className="text-button" onClick={() => navigate("/live-guard")}>Open Live Guard <ArrowRight size={15} /></button></div>
          <div className="table-scroll">
            <table><thead><tr><th>Caller</th><th>Source</th><th>Language</th><th>Risk</th><th>State</th><th>Sensitive action</th><th>Updated</th></tr></thead>
              <tbody>{data.active_sessions.map((session) => <tr key={session.id} onClick={() => navigate(`/live-guard?session=${session.id}`)} className="clickable-row"><td><div className="primary-cell"><strong>{session.claimed_identity}</strong><span>{session.id.slice(0, 8).toUpperCase()}</span></div></td><td>{session.source}</td><td>{session.language}</td><td><strong className={session.risk_index >= 80 ? "risk-number critical" : session.risk_index >= 60 ? "risk-number warning" : "risk-number"}>{Math.round(session.risk_index)}</strong></td><td><RiskBadge state={session.state} compact /></td><td>{session.transaction_type}<small>{formatCurrency(session.transaction_value, session.currency)}</small></td><td>{session.duration_seconds}s</td></tr>)}</tbody>
            </table>
          </div>
        </article>
        <aside className="panel privacy-panel">
          <div className="privacy-hero-icon"><LockKeyhole size={24} /></div><p className="eyebrow">Privacy posture</p><h2>Raw audio retention is off</h2><p>Streaming audio stays in an ephemeral {data.privacy.ephemeral_buffer_seconds}-second buffer. The demo stores only scores, decisions, and actions.</p>
          <ul className="check-list"><li><ShieldCheck size={16} />Metadata retention: {data.privacy.metadata_retention_days} days</li><li><ShieldCheck size={16} />Tenant-isolated records</li><li><ShieldCheck size={16} />Hash-chained audit events</li></ul>
          <button className="button secondary wide" onClick={() => navigate("/privacy-audit")}>Review privacy controls</button>
        </aside>
      </section>

      <section className="content-grid equal">
        <article className="panel">
          <div className="panel-header"><div><p className="eyebrow">Latest cases</p><h2>High-risk incidents</h2></div><button className="text-button" onClick={() => navigate("/investigations")}>View all <ArrowRight size={15} /></button></div>
          <div className="incident-list">{data.incidents.slice(0, 4).map((incident) => <button key={incident.id} onClick={() => navigate(`/investigations?incident=${incident.id}`)}><span className={`severity-marker ${incident.severity.toLowerCase()}`} /><span><strong>{incident.claimed_identity}</strong><small>{incident.prevented_action}</small></span><div><b>{Math.round(incident.peak_risk)}</b><small>{incident.severity}</small></div></button>)}</div>
        </article>
        <article className="panel">
          <div className="panel-header"><div><p className="eyebrow">Connected estate</p><h2>Integration health</h2></div><button className="text-button" onClick={() => navigate("/integrations")}>Manage <ArrowRight size={15} /></button></div>
          <div className="health-list">{data.integrations.slice(0, 6).map((integration) => <div key={integration.id}><span className={`status-light ${integration.status === "CONNECTED" ? "healthy" : integration.status === "DEGRADED" ? "warning" : "offline"}`} /><span><strong>{integration.name}</strong><small>{integration.mode === "LIVE" ? "Live adapter" : `${integration.mode.toLowerCase()} mode`}</small></span><em>{integration.status}</em></div>)}</div>
        </article>
      </section>
    </div>
  );
}
