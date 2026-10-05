import type { DashboardSummary, SessionSnapshot, User } from "../types";

const configuredApi = import.meta.env.VITE_API_URL as string | undefined;
const API_BASE = configuredApi || "/api/v1";

export const authStore = {
  token: () => sessionStorage.getItem("phantom-vox-token"),
  user: (): User | null => {
    const raw = sessionStorage.getItem("phantom-vox-user");
    return raw ? (JSON.parse(raw) as User) : null;
  },
  save: (token: string, user: User) => {
    sessionStorage.setItem("phantom-vox-token", token);
    sessionStorage.setItem("phantom-vox-user", JSON.stringify(user));
  },
  clear: () => {
    sessionStorage.removeItem("phantom-vox-token");
    sessionStorage.removeItem("phantom-vox-user");
  },
};

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = authStore.token();
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData)) headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (response.status === 401) {
    authStore.clear();
    window.dispatchEvent(new Event("phantom-vox-auth-expired"));
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(body.detail || `Request failed with ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  login: (email: string, password: string) =>
    request<{ access_token: string; user: User }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  health: () => request<Record<string, unknown>>("/health"),
  dashboard: () => request<DashboardSummary>("/dashboard/summary"),
  sessions: () => request<{ items: SessionSnapshot["session"][]; count: number }>("/sessions"),
  session: (id: string) => request<SessionSnapshot>(`/sessions/${id}`),
  stopSession: (id: string) => request(`/sessions/${id}/stop`, { method: "POST" }),
  analyzeAudio: (id: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<Record<string, unknown>>(`/sessions/${id}/audio`, { method: "POST", body: form });
  },
  startDemo: (scenario: string, autoplay = true) =>
    request<SessionSnapshot>("/demo/start", { method: "POST", body: JSON.stringify({ scenario, autoplay }) }),
  advanceDemo: (id: string) => request<SessionSnapshot>(`/demo/${id}/advance`, { method: "POST" }),
  resetDemo: () => request<{ stopped_sessions: number }>("/demo/reset", { method: "POST" }),
  incidents: (query = "") => request<{ items: unknown[]; count: number }>(`/incidents${query}`),
  incident: (id: string) => request<Record<string, unknown>>(`/incidents/${id}`),
  resolveIncident: (id: string, disposition: string) =>
    request(`/incidents/${id}/resolve`, { method: "POST", body: JSON.stringify({ disposition }) }),
  policies: () => request<{ items: unknown[]; count: number }>("/policies"),
  testPolicy: (id: string, body: Record<string, number>) =>
    request<Record<string, unknown>>(`/policies/${id}/test`, { method: "POST", body: JSON.stringify(body) }),
  publishPolicy: (id: string) => request(`/policies/${id}/publish`, { method: "POST" }),
  voices: () => request<{ items: unknown[]; count: number }>("/trusted-voices"),
  enrollVoice: (body: Record<string, unknown>) =>
    request<Record<string, unknown>>("/trusted-voices/enroll", { method: "POST", body: JSON.stringify(body) }),
  revokeVoice: (id: string) => request(`/trusted-voices/${id}`, { method: "DELETE" }),
  integrations: () => request<{ items: unknown[] }>("/integrations"),
  testIntegration: (id: string) => request<Record<string, unknown>>(`/integrations/${id}/test`, { method: "POST" }),
  models: () => request<{ items: unknown[] }>("/models"),
  evaluations: () => request<{ items: unknown[]; verified_benchmark_available: boolean }>("/evaluations"),
  importEvaluation: (body: Record<string, unknown>) =>
    request<Record<string, unknown>>("/evaluations/import", { method: "POST", body: JSON.stringify(body) }),
  audit: () => request<{ items: unknown[]; count: number }>("/audit"),
  verifyAudit: () => request<Record<string, unknown>>("/audit/verify", { method: "POST" }),
  completeVerification: (id: string, result: string) =>
    request(`/verifications/${id}/complete`, { method: "POST", body: JSON.stringify({ result }) }),
  holdTransaction: (id: string) => request(`/transactions/${id}/hold`, { method: "POST" }),
};

export function sessionWebSocketUrl(sessionId: string): string {
  const token = authStore.token() || "";
  const configured = import.meta.env.VITE_WS_URL as string | undefined;
  const base = configured || `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}/api/v1`;
  return `${base}/ws/sessions/${sessionId}?token=${encodeURIComponent(token)}`;
}
