from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.bootstrap import TENANT_ID
from app.db.session import SessionLocal
from app.models.entities import (
    Action,
    AudioWindow,
    EvidenceScore,
    Incident,
    MonitoringSession,
    RiskDecision,
    SensitiveTransaction,
    VerificationRequest,
)
from app.policy.trustfusion import EvidenceInput, TrustFusionEngine
from app.services.audit import append_audit_event
from app.streaming.hub import session_hub


SCENARIOS: dict[str, dict] = {
    "genuine": {
        "label": "Genuine caller",
        "identity": "Aarav Mehta",
        "language": "English - Indian",
        "value": 485_000,
        "windows": [
            (0.10, 0.08, 0.14, 0.12, 0.08, 0.96),
            (0.13, 0.09, 0.12, 0.10, 0.07, 0.94),
            (0.11, 0.07, 0.10, 0.14, 0.06, 0.95),
            (0.09, 0.08, 0.11, 0.09, 0.05, 0.97),
        ],
    },
    "mid_call_clone": {
        "label": "Mid-call cloned-voice attack",
        "identity": "Aarav Mehta",
        "language": "English - Indian",
        "value": 4_850_000,
        "windows": [
            (0.12, 0.09, 0.16, 0.28, 0.08, 0.95),
            (0.15, 0.10, 0.18, 0.34, 0.10, 0.94),
            (0.76, 0.68, 0.65, 0.91, 0.56, 0.92),
            (0.93, 0.89, 0.78, 0.96, 0.71, 0.91),
            (0.98, 0.94, 0.84, 0.98, 0.78, 0.90),
            (0.97, 0.95, 0.86, 0.98, 0.81, 0.92),
        ],
    },
    "poor_quality": {
        "label": "Poor-quality call",
        "identity": "Kabir Singh",
        "language": "Hindi",
        "value": 720_000,
        "windows": [
            (0.49, 0.50, 0.52, 0.36, 0.61, 0.22),
            (0.55, 0.48, 0.57, 0.42, 0.66, 0.20),
            (0.46, 0.54, 0.50, 0.38, 0.60, 0.25),
        ],
    },
    "high_context_uncertain": {
        "label": "High-risk context with uncertain audio",
        "identity": "Sanjay Patel",
        "language": "Gujarati",
        "value": 9_250_000,
        "windows": [
            (0.45, 0.51, 0.55, 0.96, 0.52, 0.72),
            (0.48, 0.56, 0.61, 0.98, 0.58, 0.74),
            (0.52, 0.59, 0.63, 0.99, 0.62, 0.76),
            (0.50, 0.62, 0.66, 0.99, 0.64, 0.78),
        ],
    },
}


EVIDENCE_META = {
    "synthetic_speech": ("Synthetic Speech", "Vocoder-like acoustic artifacts increased", "rawnetlite-or-demo-1.0"),
    "speaker_mismatch": ("Speaker Identity", "Voice differs from the consented enrollment profile", "speaker-demo-1.0"),
    "prosody_anomaly": ("Prosody and Behavior", "Pause, rhythm, and energy patterns are atypical", "prosody-rules-1.0"),
    "context_risk": ("Context Risk", "Urgent high-value payment request increased contextual risk", "context-policy-1.0"),
    "out_of_distribution": ("Out-of-Distribution", "Audio differs from the detector's expected operating conditions", "ood-demo-1.0"),
    "channel_quality": ("Channel Quality", "Signal quality gate for reliable automated decisions", "quality-rules-1.0"),
}


def start_demo_session(db: Session, *, scenario_name: str, user_id: str) -> MonitoringSession:
    scenario = SCENARIOS[scenario_name]
    session = MonitoringSession(
        tenant_id=TENANT_ID,
        claimed_identity=scenario["identity"],
        organization="Northstar Cooperative Bank",
        source="Judge Demo",
        language=scenario["language"],
        state="LISTENING",
        risk_index=0,
        uncertainty=1,
        transaction_type="Vendor Payment",
        transaction_value=scenario["value"],
        currency="INR",
        operator="Priya Sharma",
        demo_scenario=scenario_name,
        status="ACTIVE",
        audio_retained=False,
    )
    db.add(session)
    db.flush()
    transaction = SensitiveTransaction(
        session_id=session.id,
        reference=f"PV-{session.id[:8].upper()}",
        transaction_type="Vendor Payment",
        value=scenario["value"],
        currency="INR",
        status="PENDING",
    )
    db.add(transaction)
    append_audit_event(
        db,
        tenant_id=TENANT_ID,
        user_id=user_id,
        event_type="SESSION_STARTED",
        entity_type="SESSION",
        entity_id=session.id,
        previous_state=None,
        new_state="LISTENING",
        model_version=session.model_version,
        policy_version=session.policy_version,
        payload={"scenario": scenario_name, "demo_mode": True, "raw_audio_retained": False},
    )
    db.commit()
    return session


def _build_evidence(values: tuple[float, float, float, float, float, float], *, scenario_name: str) -> list[EvidenceInput]:
    names = [
        "synthetic_speech",
        "speaker_mismatch",
        "prosody_anomaly",
        "context_risk",
        "out_of_distribution",
        "channel_quality",
    ]
    evidence = []
    for name, value in zip(names, values):
        _label, explanation, version = EVIDENCE_META[name]
        available = not (scenario_name == "high_context_uncertain" and name == "synthetic_speech")
        evidence.append(
            EvidenceInput(
                name=name,
                score=value,
                quality=values[-1],
                available=available,
                explanation=explanation if value >= 0.65 else "Evidence remained within the expected range",
                model_version=version,
            )
        )
    return evidence


def advance_demo(db: Session, *, session_id: str, user_id: str | None = None) -> dict:
    session = db.get(MonitoringSession, session_id)
    if session is None or not session.demo_scenario:
        raise ValueError("Demo session not found")
    scenario = SCENARIOS[session.demo_scenario]
    sequence = int(db.scalar(select(func.count(AudioWindow.id)).where(AudioWindow.session_id == session_id)) or 0)
    if sequence >= len(scenario["windows"]):
        if session.status == "ACTIVE":
            session.status = "COMPLETED"
            append_audit_event(
                db,
                tenant_id=session.tenant_id,
                user_id=user_id,
                event_type="SESSION_COMPLETED",
                entity_type="SESSION",
                entity_id=session.id,
                previous_state=session.state,
                new_state=session.state,
                model_version=session.model_version,
                policy_version=session.policy_version,
                payload={"raw_audio_retained": False},
            )
            db.commit()
        return session_snapshot(db, session_id)

    values = scenario["windows"][sequence]
    evidence = _build_evidence(values, scenario_name=session.demo_scenario)
    audio_window = AudioWindow(
        session_id=session.id,
        sequence=sequence,
        start_seconds=float(sequence),
        end_seconds=float(sequence + 3),
        speech_seconds=3,
        quality=values[-1],
    )
    db.add(audio_window)
    db.flush()
    for item in evidence:
        db.add(
            EvidenceScore(
                session_id=session.id,
                audio_window_id=audio_window.id,
                name=item.name,
                score=item.score,
                quality=item.quality,
                available=item.available,
                explanation=item.explanation,
                model_version=item.model_version,
            )
        )

    recent_decisions = list(
        db.scalars(
            select(RiskDecision)
            .where(RiskDecision.session_id == session.id)
            .order_by(RiskDecision.sequence.desc())
            .limit(3)
        )
    )
    recent_risks = [decision.risk_index for decision in reversed(recent_decisions)]
    previous_state = session.state
    decision = TrustFusionEngine().decide(evidence, recent_risks=recent_risks, previous_state=previous_state)
    session.state = decision.state
    session.risk_index = decision.risk_index
    session.uncertainty = decision.uncertainty
    session.duration_seconds = sequence + 3
    session.updated_at = datetime.now(timezone.utc)

    risk_decision = RiskDecision(
        session_id=session.id,
        sequence=sequence,
        risk_index=decision.risk_index,
        state=decision.state,
        recommended_action=decision.recommended_action,
        actual_action="CONTINUE_MONITORING",
        reason=decision.reason,
        model_version=session.model_version,
        policy_version=session.policy_version,
    )
    db.add(risk_decision)

    transaction = db.scalar(select(SensitiveTransaction).where(SensitiveTransaction.session_id == session.id))
    action_events: list[str] = []
    if decision.state in {"STEP_UP_REQUIRED", "CRITICAL"} and transaction and transaction.status == "PENDING":
        transaction.status = "ON_HOLD"
        transaction.hold_reason = "TrustFusion risk policy required secondary verification"
        risk_decision.actual_action = "TRANSACTION_HELD"
        verification = VerificationRequest(
            session_id=session.id,
            transaction_id=transaction.id,
            method="TRUSTED_DEVICE",
            destination_masked="Trusted device •••• 1842",
            status="PENDING",
            reason=decision.reason,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=3),
        )
        db.add(verification)
        db.add(Action(session_id=session.id, action_type="HOLD_TRANSACTION", status="COMPLETED", details=transaction.reference))
        action_events.extend(["TRANSACTION_HELD", "VERIFICATION_SENT"])
        append_audit_event(
            db,
            tenant_id=session.tenant_id,
            user_id=user_id,
            event_type="TRANSACTION_HELD",
            entity_type="TRANSACTION",
            entity_id=transaction.id,
            previous_state="PENDING",
            new_state="ON_HOLD",
            model_version=session.model_version,
            policy_version=session.policy_version,
            payload={"reference": transaction.reference, "reason": decision.reason},
        )

    if decision.state == "CRITICAL":
        verification = db.scalar(
            select(VerificationRequest)
            .where(VerificationRequest.session_id == session.id)
            .order_by(VerificationRequest.created_at.desc())
        )
        if verification and verification.status == "PENDING":
            verification.status = "FAILED"
            verification.result = "FAILED"
            action_events.append("VERIFICATION_FAILED")
        incident = db.scalar(select(Incident).where(Incident.session_id == session.id))
        if incident is None:
            incident = Incident(
                tenant_id=session.tenant_id,
                session_id=session.id,
                claimed_identity=session.claimed_identity,
                source=session.source,
                language=session.language,
                peak_risk=decision.risk_index,
                trigger="Consecutive high-risk windows and multi-evidence agreement",
                prevented_action="Vendor payment placed on hold",
                verification_result="FAILED",
                severity="CRITICAL",
                status="UNDER_REVIEW",
                assigned_analyst="Ananya Rao",
                summary="A mid-call change produced synthetic-speech, speaker-mismatch, and contextual-risk evidence. The simulated payment remains on hold.",
                model_version=session.model_version,
                policy_version=session.policy_version,
            )
            db.add(incident)
            db.flush()
            db.add(Action(session_id=session.id, incident_id=incident.id, action_type="ESCALATE_SUPERVISOR", status="COMPLETED", details="Critical demo incident"))
            action_events.extend(["INCIDENT_CREATED", "SUPERVISOR_ESCALATED"])
            append_audit_event(
                db,
                tenant_id=session.tenant_id,
                user_id=user_id,
                event_type="INCIDENT_CREATED",
                entity_type="INCIDENT",
                entity_id=incident.id,
                previous_state=None,
                new_state="UNDER_REVIEW",
                model_version=session.model_version,
                policy_version=session.policy_version,
                payload={"severity": "CRITICAL", "transaction_status": "ON_HOLD"},
            )
        else:
            incident.peak_risk = max(incident.peak_risk, decision.risk_index)

    if decision.state != previous_state:
        append_audit_event(
            db,
            tenant_id=session.tenant_id,
            user_id=user_id,
            event_type="RISK_STATE_CHANGED",
            entity_type="SESSION",
            entity_id=session.id,
            previous_state=previous_state,
            new_state=decision.state,
            model_version=session.model_version,
            policy_version=session.policy_version,
            payload={"risk_index": decision.risk_index, "fusion_mode": decision.fusion_mode},
        )
    db.commit()
    snapshot = session_snapshot(db, session_id)
    snapshot["action_events"] = action_events
    return snapshot


def session_snapshot(db: Session, session_id: str) -> dict:
    session = db.get(MonitoringSession, session_id)
    if session is None:
        raise ValueError("Session not found")
    transaction = db.scalar(select(SensitiveTransaction).where(SensitiveTransaction.session_id == session.id))
    verification = db.scalar(
        select(VerificationRequest).where(VerificationRequest.session_id == session.id).order_by(VerificationRequest.created_at.desc())
    )
    decisions = list(
        db.scalars(select(RiskDecision).where(RiskDecision.session_id == session.id).order_by(RiskDecision.sequence.asc()))
    )
    latest_window = db.scalar(
        select(AudioWindow).where(AudioWindow.session_id == session.id).order_by(AudioWindow.sequence.desc()).limit(1)
    )
    evidence_rows = []
    if latest_window:
        evidence_rows = list(db.scalars(select(EvidenceScore).where(EvidenceScore.audio_window_id == latest_window.id)))
    incident = db.scalar(select(Incident).where(Incident.session_id == session.id))
    return {
        "type": "session_update",
        "session": {
            "id": session.id,
            "claimed_identity": session.claimed_identity,
            "organization": session.organization,
            "source": session.source,
            "language": session.language,
            "state": session.state,
            "risk_index": session.risk_index,
            "uncertainty": session.uncertainty,
            "duration_seconds": session.duration_seconds,
            "transaction_type": session.transaction_type,
            "transaction_value": session.transaction_value,
            "currency": session.currency,
            "operator": session.operator,
            "model_version": session.model_version,
            "policy_version": session.policy_version,
            "demo_scenario": session.demo_scenario,
            "status": session.status,
            "audio_retained": session.audio_retained,
            "updated_at": session.updated_at.isoformat(),
        },
        "transaction": None if transaction is None else {
            "id": transaction.id,
            "reference": transaction.reference,
            "status": transaction.status,
            "value": transaction.value,
            "currency": transaction.currency,
            "hold_reason": transaction.hold_reason,
        },
        "verification": None if verification is None else {
            "id": verification.id,
            "method": verification.method,
            "destination_masked": verification.destination_masked,
            "status": verification.status,
            "reason": verification.reason,
            "expires_at": verification.expires_at.isoformat(),
            "result": verification.result,
        },
        "incident_id": incident.id if incident else None,
        "evidence": [
            {
                "name": row.name,
                "label": EVIDENCE_META[row.name][0],
                "score": row.score,
                "quality": row.quality,
                "available": row.available,
                "explanation": row.explanation,
                "model_version": row.model_version,
            }
            for row in evidence_rows
        ],
        "timeline": [
            {
                "sequence": row.sequence,
                "risk_index": row.risk_index,
                "state": row.state,
                "recommended_action": row.recommended_action,
                "actual_action": row.actual_action,
                "created_at": row.created_at.isoformat(),
            }
            for row in decisions
        ],
    }


async def play_demo(session_id: str, user_id: str | None = None) -> None:
    settings = get_settings()
    while True:
        await asyncio.sleep(settings.demo_tick_seconds)
        with SessionLocal() as db:
            try:
                before = db.get(MonitoringSession, session_id)
                if before is None or before.status == "COMPLETED":
                    return
                snapshot = advance_demo(db, session_id=session_id, user_id=user_id)
            except Exception as exc:
                await session_hub.broadcast(session_id, {"type": "error", "message": str(exc)})
                return
        await session_hub.broadcast(session_id, snapshot)
        if snapshot["session"]["status"] == "COMPLETED":
            return
