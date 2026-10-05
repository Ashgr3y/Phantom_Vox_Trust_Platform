import {
  Activity,
  Bell,
  BookOpenCheck,
  BrainCircuit,
  ChevronLeft,
  ChevronRight,
  CircleUserRound,
  FileSearch,
  Fingerprint,
  Menu,
  Moon,
  Network,
  Search,
  ShieldCheck,
  Sun,
  X,
} from "lucide-react";
import { useState, type ReactNode } from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { authStore } from "../services/api";
import type { User } from "../types";
import { useTheme } from "../hooks/useTheme";
import { Logo } from "./Logo";

const navigation = [
  { path: "/overview", label: "Overview", icon: Activity },
  { path: "/live-guard", label: "Live Guard", icon: ShieldCheck },
  { path: "/investigations", label: "Investigations", icon: FileSearch },
  { path: "/trusted-voices", label: "Trusted Voices", icon: Fingerprint },
  { path: "/policies", label: "Policies", icon: BookOpenCheck },
  { path: "/integrations", label: "Integrations", icon: Network },
  { path: "/model-trust", label: "Model Trust", icon: BrainCircuit },
  { path: "/privacy-audit", label: "Privacy & Audit", icon: ShieldCheck },
];

export function AppShell({ user, onLogout, children }: { user: User; onLogout: () => void; children: ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [search, setSearch] = useState("");
  const { theme, toggle } = useTheme();
  const location = useLocation();
  const navigate = useNavigate();
  const active = navigation.find((item) => location.pathname.startsWith(item.path)) ?? navigation[0];

  const onSearch = (event: React.FormEvent) => {
    event.preventDefault();
    const value = search.trim().toLowerCase();
    const match = navigation.find((item) => item.label.toLowerCase().includes(value));
    if (match) {
      navigate(match.path);
      setSearch("");
    } else if (value) {
      navigate(`/investigations?search=${encodeURIComponent(value)}`);
    }
  };

  return (
    <div className={`app-frame ${collapsed ? "sidebar-collapsed" : ""}`}>
      {mobileOpen && <button className="mobile-scrim" aria-label="Close navigation" onClick={() => setMobileOpen(false)} />}
      <aside className={`sidebar ${mobileOpen ? "mobile-open" : ""}`}>
        <div className="sidebar-brand">
          <Logo compact={collapsed} />
          <button className="mobile-close icon-button" onClick={() => setMobileOpen(false)} aria-label="Close navigation"><X size={20} /></button>
        </div>
        <div className="demo-ribbon"><span>Demo mode</span>{!collapsed && <small>Seeded records</small>}</div>
        <nav aria-label="Main navigation">
          {navigation.map(({ path, label, icon: Icon }) => (
            <NavLink key={path} to={path} onClick={() => setMobileOpen(false)} className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`} title={collapsed ? label : undefined}>
              <Icon size={19} aria-hidden="true" /><span>{label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="privacy-mini"><span className="status-light healthy" />{!collapsed && <div><strong>Privacy protected</strong><small>Raw audio off</small></div>}</div>
          <button className="collapse-button" onClick={() => setCollapsed((value) => !value)} aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}>
            {collapsed ? <ChevronRight size={18} /> : <><ChevronLeft size={18} /><span>Collapse</span></>}
          </button>
        </div>
      </aside>
      <div className="app-surface">
        <header className="topbar">
          <div className="topbar-left">
            <button className="mobile-menu icon-button" onClick={() => setMobileOpen(true)} aria-label="Open navigation"><Menu size={21} /></button>
            <div className="breadcrumb"><span>Phantom Vox</span><ChevronRight size={14} /><strong>{active.label}</strong></div>
          </div>
          <form className="global-search" onSubmit={onSearch} role="search">
            <Search size={17} aria-hidden="true" />
            <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search sessions, incidents, pages" aria-label="Global search" />
            <kbd>⌘ K</kbd>
          </form>
          <div className="topbar-actions">
            <div className="service-pill"><span className="status-light healthy" /><span>Services healthy</span></div>
            <button className="icon-button" aria-label="Notifications"><Bell size={19} /><span className="notification-dot">2</span></button>
            <button className="icon-button" onClick={toggle} aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}>
              {theme === "dark" ? <Sun size={19} /> : <Moon size={19} />}
            </button>
            <div className="profile-menu">
              <button className="profile-button" onClick={() => setProfileOpen((value) => !value)} aria-expanded={profileOpen}>
                <span className="avatar">YK</span><span className="profile-copy"><strong>{user.name}</strong><small>{user.role}</small></span>
              </button>
              {profileOpen && <div className="profile-popover"><div><CircleUserRound size={18} /><span><strong>{user.name}</strong><small>{user.email}</small></span></div><button onClick={() => { authStore.clear(); onLogout(); }}>Sign out</button></div>}
            </div>
          </div>
        </header>
        <main className="main-content">{children}</main>
      </div>
    </div>
  );
}
