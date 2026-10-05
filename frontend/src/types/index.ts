export type RiskState =
  | "WAITING_FOR_AUDIO"
  | "LISTENING"
  | "ANALYZING"
  | "LOW_RISK"
  | "MONITOR"
  | "STEP_UP_REQUIRED"
  | "CRITICAL"
  | "UNCERTAIN"
  | "INSUFFICIENT_AUDIO"
  | "POOR_AUDIO_QUALITY"
  | "DISCONNECTED"
  | "ERROR";

export interface User {
  id: string;
  name: string;
  email: string;
  role: string;
}

export interface SessionRecord {
  id: string;
  claimed_identity: string;
  organization: string;
  source: string;
  language: string;
  state: RiskState;
  risk_index: number;
  uncertainty: number;
  duration_seconds: number;
  transaction_type: string;
  transaction_value: number;
  currency: string;
  operator: string;
  model_version: string;
  policy_version: string;
  demo_scenario?: string | null;
  status: string;
  audio_retained: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface Evidence {
  name: string;
  label: string;
  score: number;
  quality: number;
  available: boolean;
  explanation: string;
  model_version: string;
}

export interface TimelinePoint {
  sequence: number;
  risk_index: number;
  state: RiskState;
  recommended_action: string;
  actual_action: string;
  created_at: string;
}

export interface SessionSnapshot {
  type: string;
  session: SessionRecord;
  transaction: null | {
    id: string;
    reference: string;
    status: string;
    value: number;
    currency: string;
    hold_reason?: string | null;
  };
  verification: null | {
    id: string;
    method: string;
    destination_masked: string;
    status: string;
    reason: string;
    expires_at: string;
    result?: string | null;
  };
  incident_id: string | null;
  evidence: Evidence[];
  timeline: TimelinePoint[];
  action_events?: string[];
}

export interface Incident {
  id: string;
  session_id: string;
  claimed_identity: string;
  source: string;
  language: string;
  peak_risk: number;
  trigger: string;
  prevented_action: string;
  verification_result: string;
  severity: string;
  status: string;
  assigned_analyst: string;
  summary: string;
  analyst_notes: string;
  disposition?: string | null;
  model_version: string;
  policy_version: string;
  created_at: string;
}

export interface DashboardSummary {
  demo_data: boolean;
  kpis: {
    active_sessions: number;
    requiring_attention: number;
    actions_prevented: number;
    average_risk: number;
    verification_success_rate: number | null;
    service_health: string;
  };
  risk_activity: { time: string; risk: number; state: string }[];
  state_distribution: { name: string; value: number }[];
  active_sessions: SessionRecord[];
  incidents: Incident[];
  integrations: { id: string; name: string; status: string; mode: string; last_health_check: string | null }[];
  privacy: {
    raw_audio_retention: boolean;
    ephemeral_buffer_seconds: number;
    metadata_retention_days: number;
    encryption: string;
  };
}
