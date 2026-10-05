import { AlertOctagon, AlertTriangle, CheckCircle2, CircleHelp, Ear, Radio, ShieldQuestion } from "lucide-react";
import type { RiskState } from "../types";

const labels: Record<string, string> = {
  WAITING_FOR_AUDIO: "Waiting for audio",
  LISTENING: "Listening",
  ANALYZING: "Analyzing",
  LOW_RISK: "Low risk",
  MONITOR: "Monitor",
  STEP_UP_REQUIRED: "Step-up required",
  CRITICAL: "Critical",
  UNCERTAIN: "Uncertain",
  INSUFFICIENT_AUDIO: "Insufficient audio",
  POOR_AUDIO_QUALITY: "Poor audio quality",
  DISCONNECTED: "Disconnected",
  ERROR: "Error",
};

function iconFor(state: string) {
  if (state === "LOW_RISK") return CheckCircle2;
  if (state === "CRITICAL") return AlertOctagon;
  if (state === "STEP_UP_REQUIRED" || state === "MONITOR") return AlertTriangle;
  if (state === "LISTENING") return Ear;
  if (state === "ANALYZING") return Radio;
  if (state === "UNCERTAIN" || state === "INSUFFICIENT_AUDIO") return ShieldQuestion;
  return CircleHelp;
}

export function RiskBadge({ state, compact = false }: { state: RiskState | string; compact?: boolean }) {
  const Icon = iconFor(state);
  return (
    <span className={`risk-badge risk-${state.toLowerCase()}`}>
      <Icon size={compact ? 13 : 15} aria-hidden="true" />
      {labels[state] ?? state.replaceAll("_", " ")}
    </span>
  );
}
