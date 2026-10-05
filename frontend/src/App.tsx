import { useEffect, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { LoginScreen } from "./components/LoginScreen";
import { useWebMcp } from "./hooks/useWebMcp";
import { authStore } from "./services/api";
import type { User } from "./types";
import { IntegrationsPage } from "./pages/IntegrationsPage";
import { InvestigationsPage } from "./pages/InvestigationsPage";
import { LiveGuardPage } from "./pages/LiveGuardPage";
import { ModelTrustPage } from "./pages/ModelTrustPage";
import { OverviewPage } from "./pages/OverviewPage";
import { PoliciesPage } from "./pages/PoliciesPage";
import { PrivacyAuditPage } from "./pages/PrivacyAuditPage";
import { TrustedVoicesPage } from "./pages/TrustedVoicesPage";

function AuthenticatedApp({ user, onLogout }: { user: User; onLogout: () => void }) {
  useWebMcp();
  return (
    <AppShell user={user} onLogout={onLogout}>
      <Routes>
        <Route path="/overview" element={<OverviewPage />} />
        <Route path="/live-guard" element={<LiveGuardPage />} />
        <Route path="/investigations" element={<InvestigationsPage />} />
        <Route path="/trusted-voices" element={<TrustedVoicesPage />} />
        <Route path="/policies" element={<PoliciesPage />} />
        <Route path="/integrations" element={<IntegrationsPage />} />
        <Route path="/model-trust" element={<ModelTrustPage />} />
        <Route path="/privacy-audit" element={<PrivacyAuditPage />} />
        <Route path="*" element={<Navigate to="/overview" replace />} />
      </Routes>
    </AppShell>
  );
}

export default function App() {
  const [user, setUser] = useState<User | null>(() => authStore.user());
  useEffect(() => {
    const expired = () => setUser(null);
    window.addEventListener("phantom-vox-auth-expired", expired);
    return () => window.removeEventListener("phantom-vox-auth-expired", expired);
  }, []);
  if (!user || !authStore.token()) return <LoginScreen onLogin={setUser} />;
  return <AuthenticatedApp user={user} onLogout={() => setUser(null)} />;
}
