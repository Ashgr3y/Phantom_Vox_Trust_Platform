import { CheckCircle2, Eye, EyeOff, Fingerprint, LockKeyhole, ShieldCheck } from "lucide-react";
import { useState } from "react";
import { api, authStore } from "../services/api";
import type { User } from "../types";
import { Logo } from "./Logo";

export function LoginScreen({ onLogin }: { onLogin: (user: User) => void }) {
  const [email, setEmail] = useState("admin@phantomvox.local");
  const [password, setPassword] = useState("PhantomVox@2026");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const result = await api.login(email, password);
      authStore.save(result.access_token, result.user);
      onLogin(result.user);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to sign in");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="login-screen">
      <section className="login-story">
        <Logo />
        <div className="login-story-copy">
          <p className="eyebrow">Real-time voice defense</p>
          <h1>Hear the truth.<br /><span>Stop the fraud.</span></h1>
          <p>Continuous voice-risk analysis with explainable evidence, secondary verification, and action-level prevention.</p>
        </div>
        <div className="login-proof-grid">
          <div><ShieldCheck size={21} /><span><strong>Action-aware</strong><small>Holds sensitive workflows</small></span></div>
          <div><Fingerprint size={21} /><span><strong>Multi-evidence</strong><small>Voice, identity, context</small></span></div>
          <div><LockKeyhole size={21} /><span><strong>Privacy-first</strong><small>Raw audio off by default</small></span></div>
        </div>
        <div className="login-system-status"><span className="status-light healthy" /><div><strong>Demonstration environment ready</strong><small>All records are fictional and clearly labelled</small></div></div>
      </section>
      <section className="login-panel">
        <form className="login-card" onSubmit={submit}>
          <div className="login-card-header"><span className="login-icon"><ShieldCheck size={22} /></span><div><h2>Access operations console</h2><p>Use the seeded administrator account for the judge demonstration.</p></div></div>
          <label>Email address<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="username" required /></label>
          <label>Password<div className="password-field"><input type={showPassword ? "text" : "password"} value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" required /><button type="button" onClick={() => setShowPassword((value) => !value)} aria-label={showPassword ? "Hide password" : "Show password"}>{showPassword ? <EyeOff size={18} /> : <Eye size={18} />}</button></div></label>
          {error && <div className="form-error" role="alert">{error}</div>}
          <button className="button primary wide" disabled={loading}>{loading ? "Signing in…" : "Sign in securely"}</button>
          <div className="credential-note"><CheckCircle2 size={17} /><span><strong>Demo credentials are prefilled.</strong> Change them before any shared deployment.</span></div>
          <p className="login-disclaimer">Development authentication is active. External identity provider integration is documented for production.</p>
        </form>
      </section>
    </main>
  );
}
