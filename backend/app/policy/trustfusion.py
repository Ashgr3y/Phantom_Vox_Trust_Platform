from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class EvidenceInput:
    name: str
    score: float
    quality: float = 1.0
    available: bool = True
    explanation: str = ""
    model_version: str = "unknown"


@dataclass(frozen=True)
class PolicyThresholds:
    low: float = 35
    monitor: float = 60
    step_up: float = 80
    critical: float = 80
    min_quality: float = 0.35
    min_available_weight: float = 0.45
    consecutive_high_windows: int = 2
    hysteresis_points: float = 7


@dataclass(frozen=True)
class TrustDecision:
    risk_index: float
    state: str
    recommended_action: str
    uncertainty: float
    reason: str
    fusion_mode: str


DEFAULT_WEIGHTS = {
    "synthetic_speech": 0.34,
    "speaker_mismatch": 0.23,
    "prosody_anomaly": 0.12,
    "context_risk": 0.18,
    "out_of_distribution": 0.08,
    "channel_quality_risk": 0.05,
}


class TrustFusionEngine:
    """Quality-aware, recent-window decision logic.

    This is an explicitly labelled policy-based fusion baseline. It must be
    replaced by a calibrated fusion model before probability claims are made.
    """

    def __init__(self, thresholds: PolicyThresholds | None = None) -> None:
        self.thresholds = thresholds or PolicyThresholds()

    def decide(
        self,
        evidence: Iterable[EvidenceInput],
        *,
        recent_risks: list[float] | None = None,
        previous_state: str | None = None,
    ) -> TrustDecision:
        items = list(evidence)
        quality_signal = next((item.score for item in items if item.name == "channel_quality" and item.available), None)
        if quality_signal is not None and quality_signal < self.thresholds.min_quality:
            return TrustDecision(
                risk_index=0,
                state="INSUFFICIENT_AUDIO",
                recommended_action="SECURE_CALLBACK",
                uncertainty=1 - quality_signal,
                reason="Audio quality is below the reliable-decision gate. Automatic approval is disabled.",
                fusion_mode="POLICY_BASELINE",
            )

        weighted_sum = 0.0
        available_weight = 0.0
        explanations: list[str] = []
        for item in items:
            key = "channel_quality_risk" if item.name == "channel_quality" else item.name
            if not item.available or key not in DEFAULT_WEIGHTS or item.name == "channel_quality":
                continue
            weight = DEFAULT_WEIGHTS[key] * max(0.25, item.quality)
            weighted_sum += max(0, min(1, item.score)) * weight
            available_weight += weight
            if item.score >= 0.65 and item.explanation:
                explanations.append(item.explanation)

        total_weight = sum(DEFAULT_WEIGHTS.values()) - DEFAULT_WEIGHTS["channel_quality_risk"]
        coverage = available_weight / total_weight if total_weight else 0
        if coverage < self.thresholds.min_available_weight:
            return TrustDecision(
                risk_index=0,
                state="UNCERTAIN",
                recommended_action="START_TRUSTED_VERIFICATION",
                uncertainty=1 - coverage,
                reason="Required evidence is unavailable. The system abstained instead of approving.",
                fusion_mode="POLICY_BASELINE",
            )

        current = (weighted_sum / available_weight) * 100 if available_weight else 0
        history = (recent_risks or [])[-3:]
        recency_weights = [0.15, 0.25, 0.60][-len(history):] if history else []
        if history:
            history_total = sum(weight * value for weight, value in zip(recency_weights, history)) / sum(recency_weights)
            risk = 0.68 * current + 0.32 * history_total
        else:
            risk = current

        risk = round(max(0, min(100, risk)), 1)
        consecutive_high = len([value for value in (history + [risk])[-self.thresholds.consecutive_high_windows:] if value >= self.thresholds.step_up])

        if risk >= self.thresholds.critical and consecutive_high >= self.thresholds.consecutive_high_windows:
            state, action = "CRITICAL", "HOLD_AND_ESCALATE"
        elif risk >= self.thresholds.monitor:
            state, action = "STEP_UP_REQUIRED", "HOLD_AND_VERIFY"
        elif risk >= self.thresholds.low:
            state, action = "MONITOR", "WARN_OPERATOR"
        else:
            state, action = "LOW_RISK", "CONTINUE_MONITORING"

        if previous_state == "CRITICAL" and risk >= self.thresholds.step_up - self.thresholds.hysteresis_points:
            state, action = "CRITICAL", "HOLD_AND_ESCALATE"
        elif (
            state != "CRITICAL"
            and previous_state == "STEP_UP_REQUIRED"
            and risk >= self.thresholds.monitor - self.thresholds.hysteresis_points
        ):
            state, action = "STEP_UP_REQUIRED", "HOLD_AND_VERIFY"

        uncertainty = round(max(0, min(1, 1 - coverage)), 2)
        reason = "; ".join(explanations[:2]) if explanations else "Evidence remained below the configured action thresholds."
        return TrustDecision(
            risk_index=risk,
            state=state,
            recommended_action=action,
            uncertainty=uncertainty,
            reason=reason,
            fusion_mode="POLICY_BASELINE",
        )
