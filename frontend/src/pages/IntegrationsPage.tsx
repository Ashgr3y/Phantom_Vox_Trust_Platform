import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Activity, Braces, Building2, Check, Copy, ExternalLink, Globe2, Mail, MessageSquareText, Network, PhoneCall, PlugZap, Radio, Send, ShieldCheck, Webhook } from "lucide-react";
import { useState } from "react";
import { ErrorState, LoadingState } from "../components/States";
import { PageHeader } from "../components/PageHeader";
import { api } from "../services/api";

interface Integration { id: string; name: string; kind: string; status: string; mode: string; last_health_check: string | null; config: Record<string, string>; delivery_history: Array<Record<string, string>> }
const icons: Record<string, typeof Network> = { API: Globe2, WEBSOCKET: Radio, WEBHOOK: Webhook, TELEPHONY: PhoneCall, BANKING: Building2, CRM: Network, SECURITY: ShieldCheck, NOTIFICATION: MessageSquareText, COLLABORATION: Mail };

export function IntegrationsPage() {
  const [lastTest, setLastTest] = useState<{ id: string; result: string; mode: string } | null>(null);
  const [copied, setCopied] = useState(false);
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ["integrations"], queryFn: api.integrations });
  const integrations = (query.data?.items || []) as Integration[];
  const test = useMutation({ mutationFn: (id: string) => api.testIntegration(id), onSuccess: (result, id) => { setLastTest({ id, result: String(result.result), mode: String(result.mode) }); void queryClient.invalidateQueries({ queryKey: ["integrations"] }); } });
  const snippet = "POST /api/v1/sessions/{session_id}/audio\nAuthorization: Bearer <token>\nContent-Type: multipart/form-data\n\nfile=@call-window.wav";
  const copySnippet = async () => { await navigator.clipboard.writeText(snippet); setCopied(true); window.setTimeout(() => setCopied(false), 1500); };
  return (
    <div className="page-stack">
      <PageHeader eyebrow="Enterprise connection layer" title="Integrations" description="Connect voice channels, sensitive business workflows, and independent verification systems without hiding demo adapters." actions={<button className="button primary"><PlugZap size={17} />Configure integration</button>} />
      <section className="integration-overview panel"><div><span className="integration-summary-icon"><Activity size={22} /></span><div><small>Integration posture</small><strong>{integrations.filter((item) => item.status === "CONNECTED").length} connected · {integrations.filter((item) => item.status === "DEGRADED").length} degraded</strong></div></div><p><span className="demo-chip">Transparent modes</span> Live, demo, placeholder, and future adapters are labelled separately.</p></section>
      {query.isLoading ? <LoadingState lines={8} /> : query.isError ? <ErrorState message="Integration status could not be loaded" onRetry={() => query.refetch()} /> : <section className="integration-grid">{integrations.map((item) => { const Icon = icons[item.kind] || Network; const tested = lastTest?.id === item.id; return <article className="integration-card panel" key={item.id}><div className="integration-card-top"><span className="integration-icon"><Icon size={21} /></span><div><h2>{item.name}</h2><p>{item.kind.replaceAll("_", " ")}</p></div><span className={`connection-status ${item.status.toLowerCase()}`}><i />{item.status}</span></div><div className="integration-meta"><div><small>Operating mode</small><strong className={item.mode === "LIVE" ? "green-text" : "amber-text"}>{item.mode}</strong></div><div><small>Last health check</small><strong>{item.last_health_check ? new Date(item.last_health_check).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }) : "Not configured"}</strong></div></div>{item.mode !== "LIVE" && <p className="demo-disclaimer">{item.mode === "DEMO" ? "This adapter simulates delivery and records a signed event." : item.mode === "FUTURE" ? "Planned integration. No connection is implemented." : "Configuration placeholder. No external connection is active."}</p>}{tested && <div className="test-result"><Check size={16} /><span>Test result: {lastTest.result} ({lastTest.mode})</span></div>}<div className="card-actions"><button className="button secondary" disabled={test.isPending} onClick={() => test.mutate(item.id)}><Send size={15} />Test</button><button className="icon-button" aria-label={`Configure ${item.name}`}><ExternalLink size={17} /></button></div></article>; })}</section>}
      <section className="docs-grid">
        <article className="panel developer-doc"><div className="panel-header"><div><p className="eyebrow">Developer quick start</p><h2>OpenAPI and signed events</h2><p>Use authenticated session endpoints and verify every webhook signature before acting.</p></div><Braces size={24} /></div><div className="code-block"><div><span>Request example</span><button onClick={copySnippet}>{copied ? <Check size={15} /> : <Copy size={15} />}{copied ? "Copied" : "Copy"}</button></div><pre><code>{snippet}</code></pre></div><a className="button secondary" href="/api/docs" target="_blank" rel="noreferrer">Open API documentation <ExternalLink size={16} /></a></article>
        <article className="panel webhook-card"><div className="panel-header"><div><p className="eyebrow">Signed webhook</p><h2>Prevention event payload</h2></div><Webhook size={24} /></div><pre className="payload-preview">{JSON.stringify({ event: "transaction.held", session_id: "PV-2048", risk_index: 84, state: "STEP_UP_REQUIRED", action: "HOLD_AND_VERIFY", timestamp: "2026-09-22T10:12:08Z" }, null, 2)}</pre><div className="signature-note"><ShieldCheck size={17} /><span>HMAC-SHA256 signature · Retry-safe event ID · Demo delivery history retained</span></div></article>
      </section>
    </div>
  );
}
