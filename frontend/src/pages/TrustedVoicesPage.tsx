import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CalendarClock, Fingerprint, LockKeyhole, Plus, ShieldCheck, Trash2, UploadCloud, UserRoundCheck } from "lucide-react";
import { useState } from "react";
import { EmptyState, ErrorState, LoadingState } from "../components/States";
import { Modal } from "../components/Modal";
import { PageHeader } from "../components/PageHeader";
import { api } from "../services/api";

interface VoiceProfile {
  id: string; identity_name: string; language: string; status: string; enrollment_quality: number; sample_count: number;
  expires_at: string; last_verified_at: string | null; consent_recorded: boolean; demo_profile: boolean;
}

export function TrustedVoicesPage() {
  const [enrollOpen, setEnrollOpen] = useState(false);
  const [name, setName] = useState("");
  const [language, setLanguage] = useState("English - Indian");
  const [consent, setConsent] = useState(false);
  const [message, setMessage] = useState("");
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ["voices"], queryFn: api.voices });
  const profiles = (query.data?.items || []) as VoiceProfile[];
  const enroll = useMutation({
    mutationFn: () => api.enrollVoice({ identity_name: name, language, consent_confirmed: consent, sample_count: 3 }),
    onSuccess: (result) => { setEnrollOpen(false); setMessage(String(result.message)); setName(""); setConsent(false); void queryClient.invalidateQueries({ queryKey: ["voices"] }); },
    onError: (error) => setMessage(error instanceof Error ? error.message : "Enrollment failed"),
  });
  const revoke = useMutation({ mutationFn: api.revokeVoice, onSuccess: () => { setMessage("Profile revoked and stored embedding data deleted."); void queryClient.invalidateQueries({ queryKey: ["voices"] }); } });

  return (
    <div className="page-stack">
      <PageHeader eyebrow="Consent-based assurance" title="Trusted Voices" description="Manage speaker profiles as one factor in a wider verification policy. Voice is never the only authenticator." actions={<button className="button primary" onClick={() => setEnrollOpen(true)}><Plus size={17} />Enroll trusted voice</button>} />
      {message && <div className="inline-message"><ShieldCheck size={17} /><span>{message}</span><button onClick={() => setMessage("")}>×</button></div>}
      <section className="trust-principles-grid"><article className="panel"><span><ShieldCheck size={21} /></span><div><strong>Explicit consent</strong><p>Every profile is tied to a revocable consent record.</p></div></article><article className="panel"><span><LockKeyhole size={21} /></span><div><strong>Protected embeddings</strong><p>Store protected embeddings, never a reusable voice password.</p></div></article><article className="panel"><span><UserRoundCheck size={21} /></span><div><strong>Multi-factor only</strong><p>Speaker match informs risk but cannot independently approve.</p></div></article></section>
      <section className="panel table-panel">
        <div className="panel-header"><div><p className="eyebrow">Enrollment registry</p><h2>Consented identities</h2></div><span className="demo-chip">{profiles.length} profiles</span></div>
        {query.isLoading ? <LoadingState lines={6} /> : query.isError ? <ErrorState message="Trusted voice profiles could not be loaded" onRetry={() => query.refetch()} /> : !profiles.length ? <EmptyState title="No trusted voices enrolled" description="Begin with explicit consent and at least three quality-controlled samples." /> : <div className="voice-card-grid">{profiles.map((profile) => <article className="voice-profile-card" key={profile.id}><div className="voice-card-top"><div className="voice-avatar"><Fingerprint size={23} /></div><div><h3>{profile.identity_name}</h3><p>{profile.language}</p></div><span className={`small-status ${profile.status.toLowerCase()}`}>{profile.status.replaceAll("_", " ")}</span></div><div className="voice-quality"><div><span>Enrollment quality</span><strong>{profile.enrollment_quality ? `${Math.round(profile.enrollment_quality * 100)}%` : "Pending model"}</strong></div><div className="score-track"><span style={{ width: `${profile.enrollment_quality * 100}%` }} /></div></div><dl><div><dt>Samples</dt><dd>{profile.sample_count}</dd></div><div><dt>Consent</dt><dd>{profile.consent_recorded ? "Recorded" : "Missing"}</dd></div><div><dt>Expires</dt><dd>{new Date(profile.expires_at).toLocaleDateString("en-IN", { month: "short", year: "numeric" })}</dd></div><div><dt>Last verified</dt><dd>{profile.last_verified_at ? new Date(profile.last_verified_at).toLocaleDateString("en-IN") : "Never"}</dd></div></dl>{profile.demo_profile && <p className="demo-disclaimer">Demo profile. No production speaker embedding is included.</p>}<button className="button danger-ghost wide" onClick={() => revoke.mutate(profile.id)} disabled={profile.status === "REVOKED"}><Trash2 size={16} />Revoke profile</button></article>)}</div>}
      </section>
      <Modal open={enrollOpen} onClose={() => setEnrollOpen(false)} title="Enroll a trusted voice" description="This demonstration stores consent and profile metadata. A production speaker model is not bundled.">
        <form className="enrollment-flow" onSubmit={(event) => { event.preventDefault(); enroll.mutate(); }}>
          <div className="step-banner"><span>1</span><div><strong>Consent and identity</strong><p>The person must understand the purpose, retention, expiry, and revocation options.</p></div></div>
          <div className="field-row two"><label>Identity name<input value={name} onChange={(event) => setName(event.target.value)} placeholder="e.g. Aarav Mehta" required /></label><label>Primary language<select value={language} onChange={(event) => setLanguage(event.target.value)}><option>English - Indian</option><option>Hindi</option><option>Marathi</option><option>Tamil</option><option>Gujarati</option></select></label></div>
          <div className="sample-dropzone"><UploadCloud size={30} /><strong>Three speech samples required</strong><p>WAV or FLAC, at least 8 seconds each, with no clipping or background music.</p><button type="button" className="button secondary">Select sample files</button><span>Demo flow does not upload or retain audio</span></div>
          <label className="consent-check"><input type="checkbox" checked={consent} onChange={(event) => setConsent(event.target.checked)} /><span><strong>I confirm explicit enrollment consent was obtained.</strong><small>The profile can be revoked and embedding data deleted at any time.</small></span></label>
          <div className="retention-note"><CalendarClock size={18} /><span>Default expiry: 180 days · Raw enrollment audio retention: off</span></div>
          <div className="modal-actions"><button type="button" className="button secondary" onClick={() => setEnrollOpen(false)}>Cancel</button><button className="button primary" disabled={!consent || !name || enroll.isPending}><Fingerprint size={17} />{enroll.isPending ? "Saving…" : "Save enrollment metadata"}</button></div>
        </form>
      </Modal>
    </div>
  );
}
