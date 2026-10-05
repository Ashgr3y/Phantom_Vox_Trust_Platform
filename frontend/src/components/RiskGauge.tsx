import { RiskBadge } from "./RiskBadge";
import type { RiskState } from "../types";

export function RiskGauge({ value, state }: { value: number; state: RiskState }) {
  const clamped = Math.max(0, Math.min(100, value));
  return (
    <div className="risk-gauge-wrap">
      <div className="risk-gauge" style={{ "--risk": `${clamped * 3.6}deg` } as React.CSSProperties}>
        <div className="risk-gauge-inner"><strong>{Math.round(value)}</strong><span>Risk Index</span></div>
      </div>
      <RiskBadge state={state} />
      <p>Policy score, not a calibrated probability</p>
    </div>
  );
}
