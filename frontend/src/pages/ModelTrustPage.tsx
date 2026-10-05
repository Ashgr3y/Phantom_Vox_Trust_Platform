import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, BarChart3, BrainCircuit, CheckCircle2, Cpu, Database, Download, FileUp, Gauge, Info, Server, ShieldQuestion } from "lucide-react";
import { useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ErrorState, LoadingState } from "../components/States";
import { Modal } from "../components/Modal";
import { PageHeader } from "../components/PageHeader";
import { api } from "../services/api";

interface ModelItem { id: string; name: string; purpose: string; version: string; input_format: string; device: string; status: string; installed: boolean; demo_only: boolean; limitations: string; active?: boolean; missing_dependencies?: string[]; load_error?: string | null }
interface Evaluation { id: string; name: string; dataset_name: string; verified: boolean; metrics: Record<string, number | string | null>; coverage: Record<string, unknown>; imported_at: string }

export function ModelTrustPage() {
  const [importOpen, setImportOpen] = useState(false);
  const [fileName, setFileName] = useState("");
  const [payload, setPayload] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState("");
  const queryClient = useQueryClient();
  const modelsQuery = useQuery({ queryKey: ["models"], queryFn: api.models });
  const evaluationsQuery = useQuery({ queryKey: ["evaluations"], queryFn: api.evaluations });
  const models = (modelsQuery.data?.items || []) as ModelItem[];
  const evaluations = (evaluationsQuery.data?.items || []) as Evaluation[];
  const verified = evaluations.find((item) => item.verified);
  const importRun = useMutation({ mutationFn: () => api.importEvaluation(payload!), onSuccess: () => { setImportOpen(false); setPayload(null); setFileName(""); void queryClient.invalidateQueries({ queryKey: ["evaluations"] }); }, onError: (caught) => setError(caught instanceof Error ? caught.message : "Import failed") });

  const onFile = async (file: File) => {
    setError(""); setFileName(file.name);
    try {
      const parsed = JSON.parse(await file.text()) as Record<string, unknown>;
      if (!parsed.name || !parsed.dataset_name || typeof parsed.metrics !== "object") throw new Error("Report must contain name, dataset_name, and metrics");
      setPayload(parsed);
    } catch (caught) { setPayload(null); setError(caught instanceof Error ? caught.message : "Invalid JSON report"); }
  };
  const metricChart = verified ? Object.entries(verified.metrics).filter(([, value]) => typeof value === "number").slice(0, 8).map(([name, value]) => ({ name: name.replaceAll("_", " "), value: Number(value) })) : [];

  return (
    <div className="page-stack">
      <PageHeader eyebrow="Scientific accountability" title="Model Trust" description="See exactly which models are installed, what each score means, and where verified evidence is still missing." actions={<button className="button primary" onClick={() => setImportOpen(true)}><FileUp size={17} />Import evaluation report</button>} />
      {(modelsQuery.isLoading || evaluationsQuery.isLoading) ? <LoadingState lines={8} /> : modelsQuery.isError ? <ErrorState message="Model inventory could not be loaded" onRetry={() => modelsQuery.refetch()} /> : <>
        <section className="model-inventory"><div className="section-heading"><div><p className="eyebrow">Runtime truth</p><h2>Model inventory</h2></div><p>Only genuinely present models are marked installed.</p></div><div className="model-grid">{models.map((model) => <article className={`model-card panel ${model.installed ? "installed" : ""}`} key={model.id}><div className="model-card-head"><span><BrainCircuit size={22} /></span><div><h3>{model.name}</h3><p>{model.purpose}</p></div><span className={`small-status ${model.installed ? "active" : model.demo_only ? "demo_only" : "not_installed"}`}>{model.status.replaceAll("_", " ")}</span></div><dl><div><dt>Version</dt><dd>{model.version}</dd></div><div><dt>Input</dt><dd>{model.input_format}</dd></div><div><dt>Device</dt><dd>{model.device}</dd></div><div><dt>Runtime</dt><dd>{model.active ? "Loaded" : model.installed ? "Lazy load" : "Unavailable"}</dd></div></dl>{model.missing_dependencies?.length ? <div className="model-warning"><AlertTriangle size={16} />Install optional dependencies: {model.missing_dependencies.join(", ")}</div> : null}<div className="limitation-box"><Info size={16} /><p>{model.limitations}</p></div></article>)}</div></section>
        {!verified ? <section className="no-benchmark panel"><div className="benchmark-icon"><ShieldQuestion size={30} /></div><div><p className="eyebrow">Evidence required</p><h2>No verified benchmark has been imported</h2><p>Run the evaluation pipeline against a labeled manifest before making accuracy, EER, language, accent, codec, or latency claims.</p><div className="coverage-tags"><span>Genuine speech</span><span>TTS</span><span>Voice conversion</span><span>Replay</span><span>Indian languages</span><span>Telephony codecs</span><span>Noise</span><span>Unseen generators</span></div></div><button className="button secondary" onClick={() => setImportOpen(true)}><FileUp size={17} />Import verified JSON</button></section> : <section className="verified-benchmark panel"><div className="panel-header"><div><p className="eyebrow">Verified benchmark</p><h2>{verified.name}</h2><p>{verified.dataset_name} · Imported {new Date(verified.imported_at).toLocaleDateString("en-IN")}</p></div><span className="verified-seal"><CheckCircle2 size={18} />Verified</span></div><div className="benchmark-content"><div className="metric-chart"><ResponsiveContainer width="100%" height="100%"><BarChart data={metricChart}><CartesianGrid stroke="var(--chart-grid)" vertical={false} /><XAxis dataKey="name" tickLine={false} axisLine={false} fontSize={11} /><YAxis tickLine={false} axisLine={false} /><Tooltip contentStyle={{ background: "var(--surface-raised)", border: "1px solid var(--border)", borderRadius: 10 }} /><Bar dataKey="value" fill="#2563EB" radius={[5, 5, 0, 0]} /></BarChart></ResponsiveContainer></div><div className="metric-list">{metricChart.map((item) => <div key={item.name}><span>{item.name}</span><strong>{item.value}</strong></div>)}</div></div></section>}
        <section className="trust-method-grid"><article className="panel"><Gauge size={22} /><h3>Calibration first</h3><p>The RawNetLite sigmoid is stored as uncalibrated evidence, not presented as a final probability.</p></article><article className="panel"><Database size={22} /><h3>Coverage by subgroup</h3><p>Evaluation reports can include generator, language, accent, gender, codec, and noise breakdowns.</p></article><article className="panel"><Cpu size={22} /><h3>Operational metrics</h3><p>Measure first-score latency, action latency, CPU, RAM, and concurrent-stream capacity.</p></article><article className="panel"><Server size={22} /><h3>Version traceability</h3><p>Every stored decision carries a model version and policy version for reproducibility.</p></article></section>
      </>}
      <Modal open={importOpen} onClose={() => setImportOpen(false)} title="Import an evaluation report" description="Only import metrics produced from a labeled, reproducible evaluation run.">
        <div className="evaluation-import"><label className="report-dropzone"><FileUp size={31} /><strong>{fileName || "Choose evaluation-report.json"}</strong><p>Required fields: name, dataset_name, verified, metrics, and coverage.</p><input type="file" accept="application/json,.json" onChange={(event) => event.target.files?.[0] && onFile(event.target.files[0])} /></label>{error && <div className="form-error">{error}</div>}{payload && <div className="report-preview"><CheckCircle2 size={18} /><span><strong>{String(payload.name)}</strong><small>{String(payload.dataset_name)} · Verified: {String(payload.verified ?? false)}</small></span></div>}<div className="import-warning"><AlertTriangle size={17} /><p>Setting <code>verified: true</code> is an attestation. The application does not fabricate or independently certify uploaded metrics.</p></div><div className="modal-actions"><button className="button secondary" onClick={() => setImportOpen(false)}>Cancel</button><button className="button primary" disabled={!payload || importRun.isPending} onClick={() => importRun.mutate()}><FileUp size={17} />Import report</button></div></div>
      </Modal>
    </div>
  );
}
