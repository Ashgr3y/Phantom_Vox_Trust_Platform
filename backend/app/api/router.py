from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect, status
from sqlalchemy import func, or_, select, text, update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    get_current_user,
    require_roles,
    verify_password,
)
from app.db.bootstrap import TENANT_ID
from app.db.session import SessionLocal, engine, get_db
from app.inference.rawnetlite import rawnetlite_adapter
from app.models.entities import (
    Action,
    AuditEvent,
    ConsentRecord,
    EvaluationRun,
    Incident,
    Integration,
    ModelVersion,
    MonitoringSession,
    Notification,
    Policy,
    PolicyVersion,
    RiskDecision,
    SensitiveTransaction,
    TrustedVoiceProfile,
    User,
    VerificationRequest,
)
from app.policy.trustfusion import EvidenceInput, PolicyThresholds, TrustFusionEngine
from app.schemas.api import (
    DemoStartRequest,
    EvaluationImportRequest,
    IncidentNoteRequest,
    IncidentResolveRequest,
    LoginRequest,
    PolicyCreateRequest,
    PolicyTestRequest,
    SessionCreate,
    TrustedVoiceEnrollRequest,
    VerificationCompleteRequest,
    VerificationCreateRequest,
)
from app.services.audit import append_audit_event, verify_audit_chain
from app.services.demo import advance_demo, play_demo, session_snapshot, start_demo_session
from app.streaming.hub import session_hub


router = APIRouter(prefix="/api/v1")
settings = get_settings()


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def _session_dict(row: MonitoringSession) -> dict:
    return {
        "id": row.id,
        "claimed_identity": row.claimed_identity,
        "organization": row.organization,
        "source": row.source,
        "language": row.language,
        "state": row.state,
        "risk_index": row.risk_index,
        "uncertainty": row.uncertainty,
        "duration_seconds": row.duration_seconds,
        "transaction_type": row.transaction_type,
        "transaction_value": row.transaction_value,
        "currency": row.currency,
        "operator": row.operator,
        "model_version": row.model_version,
        "policy_version": row.policy_version,
        "demo_scenario": row.demo_scenario,
        "status": row.status,
        "audio_retained": row.audio_retained,
        "created_at": _iso(row.created_at),
        "updated_at": _iso(row.updated_at),
    }


def _incident_dict(row: Incident) -> dict:
    return {
        "id": row.id,
        "session_id": row.session_id,
        "claimed_identity": row.claimed_identity,
        "source": row.source,
        "language": row.language,
        "peak_risk": row.peak_risk,
        "trigger": row.trigger,
        "prevented_action": row.prevented_action,
        "verification_result": row.verification_result,
        "severity": row.severity,
        "status": row.status,
        "assigned_analyst": row.assigned_analyst,
        "summary": row.summary,
        "analyst_notes": row.analyst_notes,
        "disposition": row.disposition,
        "model_version": row.model_version,
        "policy_version": row.policy_version,
        "created_at": _iso(row.created_at),
        "updated_at": _iso(row.updated_at),
    }


@router.post("/auth/login")
def login(payload: LoginRequest, db: Annotated[Session, Depends(get_db)]) -> dict:
    user = db.scalar(select(User).where(func.lower(User.email) == payload.email.lower(), User.active.is_(True)))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    token = create_access_token(user_id=user.id, tenant_id=user.tenant_id, role=user.role.name)
    append_audit_event(
        db,
        tenant_id=user.tenant_id,
        user_id=user.id,
        event_type="USER_LOGIN",
        entity_type="USER",
        entity_id=user.id,
        new_state="AUTHENTICATED",
        payload={"role": user.role.name},
    )
    db.commit()
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in_minutes": settings.access_token_minutes,
        "user": {"id": user.id, "name": user.full_name, "email": user.email, "role": user.role.name},
    }


@router.get("/health")
def health() -> dict:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(status_code=503, detail="Database is unavailable") from None
    if settings.require_ml and not rawnetlite_adapter.status()["active"]:
        raise HTTPException(status_code=503, detail="RawNetLite is not loaded")
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "demo_mode": settings.demo_mode,
        "database": "connected",
        "ml_required": settings.require_ml,
        "ml_active": rawnetlite_adapter.status()["active"],
        "raw_audio_retention": settings.retain_raw_audio,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/models")
def model_health() -> dict:
    return {"status": "available", "models": [rawnetlite_adapter.status()]}


@router.get("/dashboard/summary")
def dashboard_summary(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    sessions = list(
        db.scalars(
            select(MonitoringSession)
            .where(MonitoringSession.tenant_id == user.tenant_id)
            .order_by(MonitoringSession.created_at.desc())
            .limit(20)
        )
    )
    incidents = list(
        db.scalars(
            select(Incident).where(Incident.tenant_id == user.tenant_id).order_by(Incident.created_at.desc()).limit(8)
        )
    )
    integrations = list(db.scalars(select(Integration).where(Integration.tenant_id == user.tenant_id)))
    active = [item for item in sessions if item.status == "ACTIVE"]
    attention = [item for item in active if item.state in {"MONITOR", "STEP_UP_REQUIRED", "CRITICAL", "UNCERTAIN", "INSUFFICIENT_AUDIO"}]
    held_count = int(
        db.scalar(
            select(func.count(SensitiveTransaction.id))
            .join(MonitoringSession, MonitoringSession.id == SensitiveTransaction.session_id)
            .where(MonitoringSession.tenant_id == user.tenant_id, SensitiveTransaction.status.in_(["ON_HOLD", "BLOCKED"]))
        )
        or 0
    )
    completed_verifications = int(
        db.scalar(
            select(func.count(VerificationRequest.id))
            .join(MonitoringSession, MonitoringSession.id == VerificationRequest.session_id)
            .where(MonitoringSession.tenant_id == user.tenant_id, VerificationRequest.status.in_(["PASSED", "FAILED"]))
        )
        or 0
    )
    passed_verifications = int(
        db.scalar(
            select(func.count(VerificationRequest.id))
            .join(MonitoringSession, MonitoringSession.id == VerificationRequest.session_id)
            .where(MonitoringSession.tenant_id == user.tenant_id, VerificationRequest.status == "PASSED")
        )
        or 0
    )
    risk_activity = [
        {"time": row.created_at.strftime("%H:%M"), "risk": round(row.risk_index), "state": row.state}
        for row in reversed(sessions[:10])
    ]
    distribution: dict[str, int] = {}
    for item in sessions:
        distribution[item.state] = distribution.get(item.state, 0) + 1
    return {
        "demo_data": True,
        "kpis": {
            "active_sessions": len(active),
            "requiring_attention": len(attention),
            "actions_prevented": held_count,
            "average_risk": round(sum(item.risk_index for item in active) / max(1, len(active)), 1),
            "verification_success_rate": round((passed_verifications / completed_verifications) * 100, 1) if completed_verifications else None,
            "service_health": "OPERATIONAL",
        },
        "risk_activity": risk_activity,
        "state_distribution": [{"name": key, "value": value} for key, value in distribution.items()],
        "active_sessions": [_session_dict(item) for item in active[:8]],
        "incidents": [_incident_dict(item) for item in incidents],
        "integrations": [
            {"id": item.id, "name": item.name, "status": item.status, "mode": item.mode, "last_health_check": _iso(item.last_health_check)}
            for item in integrations
        ],
        "privacy": {
            "raw_audio_retention": settings.retain_raw_audio,
            "ephemeral_buffer_seconds": settings.ephemeral_buffer_seconds,
            "metadata_retention_days": settings.metadata_retention_days,
            "encryption": "Configured by deployment environment",
        },
    }


@router.post("/sessions", status_code=201)
def create_session(
    payload: SessionCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    row = MonitoringSession(
        tenant_id=user.tenant_id,
        claimed_identity=payload.claimed_identity,
        source=payload.source,
        language=payload.language,
        transaction_type=payload.transaction_type,
        transaction_value=payload.transaction_value,
        currency=payload.currency.upper(),
        state="WAITING_FOR_AUDIO",
        operator=user.full_name,
        audio_retained=False,
    )
    db.add(row)
    db.flush()
    transaction = SensitiveTransaction(
        session_id=row.id,
        reference=f"PV-{row.id[:8].upper()}",
        transaction_type=payload.transaction_type,
        value=payload.transaction_value,
        currency=payload.currency.upper(),
        status="PENDING",
    )
    db.add(transaction)
    append_audit_event(
        db,
        tenant_id=user.tenant_id,
        user_id=user.id,
        event_type="SESSION_CREATED",
        entity_type="SESSION",
        entity_id=row.id,
        new_state=row.state,
        payload={"source": row.source, "raw_audio_retained": False},
    )
    db.commit()
    return _session_dict(row)


@router.get("/sessions")
def list_sessions(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    search: str | None = None,
    state: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
) -> dict:
    statement = select(MonitoringSession).where(MonitoringSession.tenant_id == user.tenant_id)
    if search:
        pattern = f"%{search.strip()}%"
        statement = statement.where(
            or_(MonitoringSession.claimed_identity.ilike(pattern), MonitoringSession.id.ilike(pattern))
        )
    if state:
        statement = statement.where(MonitoringSession.state == state)
    rows = list(db.scalars(statement.order_by(MonitoringSession.created_at.desc()).limit(limit)))
    return {"items": [_session_dict(row) for row in rows], "count": len(rows)}


@router.get("/sessions/{session_id}")
def get_session(
    session_id: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    row = db.scalar(
        select(MonitoringSession).where(MonitoringSession.id == session_id, MonitoringSession.tenant_id == user.tenant_id)
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if row.demo_scenario:
        return session_snapshot(db, row.id)
    transaction = db.scalar(select(SensitiveTransaction).where(SensitiveTransaction.session_id == row.id))
    decisions = list(
        db.scalars(select(RiskDecision).where(RiskDecision.session_id == row.id).order_by(RiskDecision.sequence.asc()))
    )
    return {
        "session": _session_dict(row),
        "transaction": None if transaction is None else {"id": transaction.id, "reference": transaction.reference, "status": transaction.status},
        "timeline": [{"sequence": item.sequence, "risk_index": item.risk_index, "state": item.state} for item in decisions],
        "evidence": [],
    }


@router.post("/sessions/{session_id}/stop")
def stop_session(
    session_id: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    row = db.scalar(
        select(MonitoringSession).where(MonitoringSession.id == session_id, MonitoringSession.tenant_id == user.tenant_id)
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")
    previous = row.status
    row.status = "STOPPED"
    append_audit_event(
        db,
        tenant_id=user.tenant_id,
        user_id=user.id,
        event_type="SESSION_STOPPED",
        entity_type="SESSION",
        entity_id=row.id,
        previous_state=previous,
        new_state="STOPPED",
    )
    db.commit()
    return _session_dict(row)


@router.post("/sessions/{session_id}/audio")
async def analyze_session_audio(
    session_id: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    file: UploadFile = File(...),
) -> dict:
    row = db.scalar(
        select(MonitoringSession).where(MonitoringSession.id == session_id, MonitoringSession.tenant_id == user.tenant_id)
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".wav", ".flac", ".ogg"}:
        raise HTTPException(status_code=400, detail="Upload a WAV, FLAC, or OGG audio file")
    max_bytes = settings.max_upload_mb * 1024 * 1024
    payload = await file.read(max_bytes + 1)
    if len(payload) > max_bytes:
        raise HTTPException(status_code=413, detail=f"Audio upload exceeds {settings.max_upload_mb} MB")
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(payload)
            temp_path = Path(temp_file.name)
        try:
            result = await asyncio.to_thread(rawnetlite_adapter.analyze, str(temp_path))
        except RuntimeError as exc:
            raise HTTPException(
                status_code=503,
                detail=f"RawNetLite inference is unavailable. Install backend/requirements-ml.txt. {exc}",
            ) from exc
        append_audit_event(
            db,
            tenant_id=user.tenant_id,
            user_id=user.id,
            event_type="AUDIO_ANALYZED",
            entity_type="SESSION",
            entity_id=row.id,
            model_version=result["model_version"],
            policy_version=row.policy_version,
            payload={"score_type": result["score_type"], "raw_audio_retained": False},
        )
        db.commit()
        return result
    finally:
        if temp_path:
            temp_path.unlink(missing_ok=True)


@router.post("/demo/start", status_code=201)
async def start_demo(
    payload: DemoStartRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    row = start_demo_session(db, scenario_name=payload.scenario, user_id=user.id)
    snapshot = session_snapshot(db, row.id)
    if payload.autoplay:
        asyncio.create_task(play_demo(row.id, user.id))
    return snapshot


@router.post("/demo/{session_id}/advance")
async def demo_advance(
    session_id: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    row = db.scalar(select(MonitoringSession).where(MonitoringSession.id == session_id, MonitoringSession.tenant_id == user.tenant_id))
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")
    try:
        snapshot = advance_demo(db, session_id=session_id, user_id=user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await session_hub.broadcast(session_id, snapshot)
    return snapshot


@router.post("/demo/reset")
def reset_demo(
    user: Annotated[User, Depends(require_roles("Administrator", "Operator"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    rows = list(
        db.scalars(
            select(MonitoringSession).where(
                MonitoringSession.tenant_id == user.tenant_id,
                MonitoringSession.demo_scenario.is_not(None),
                MonitoringSession.status == "ACTIVE",
            )
        )
    )
    for row in rows:
        row.status = "STOPPED"
    db.commit()
    return {"stopped_sessions": len(rows), "message": "Active demonstration sessions were safely stopped"}


@router.get("/incidents")
def list_incidents(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    severity: str | None = None,
    incident_status: str | None = Query(default=None, alias="status"),
    language: str | None = None,
    search: str | None = None,
    limit: int = Query(default=100, ge=1, le=200),
) -> dict:
    statement = select(Incident).where(Incident.tenant_id == user.tenant_id)
    if severity:
        statement = statement.where(Incident.severity == severity)
    if incident_status:
        statement = statement.where(Incident.status == incident_status)
    if language:
        statement = statement.where(Incident.language == language)
    if search:
        pattern = f"%{search.strip()}%"
        statement = statement.where(or_(Incident.claimed_identity.ilike(pattern), Incident.id.ilike(pattern)))
    rows = list(db.scalars(statement.order_by(Incident.created_at.desc()).limit(limit)))
    return {"items": [_incident_dict(row) for row in rows], "count": len(rows)}


@router.get("/incidents/{incident_id}")
def get_incident(
    incident_id: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    row = db.scalar(select(Incident).where(Incident.id == incident_id, Incident.tenant_id == user.tenant_id))
    if row is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    actions = list(db.scalars(select(Action).where(Action.incident_id == row.id).order_by(Action.created_at.asc())))
    decisions = list(
        db.scalars(select(RiskDecision).where(RiskDecision.session_id == row.session_id).order_by(RiskDecision.sequence.asc()))
    )
    return {
        **_incident_dict(row),
        "timeline": [{"risk": item.risk_index, "state": item.state, "time": _iso(item.created_at)} for item in decisions],
        "actions": [{"type": item.action_type, "status": item.status, "details": item.details, "time": _iso(item.created_at)} for item in actions],
        "raw_audio_available": False,
        "audit_integrity": "HASH_CHAINED",
    }


@router.post("/incidents/{incident_id}/notes")
def add_incident_note(
    incident_id: str,
    payload: IncidentNoteRequest,
    user: Annotated[User, Depends(require_roles("Administrator", "Analyst", "Operator"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    row = db.scalar(select(Incident).where(Incident.id == incident_id, Incident.tenant_id == user.tenant_id))
    if row is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    row.analyst_notes = (row.analyst_notes + f"\n[{timestamp}] {user.full_name}: {payload.note}").strip()
    append_audit_event(
        db,
        tenant_id=user.tenant_id,
        user_id=user.id,
        event_type="INCIDENT_NOTE_ADDED",
        entity_type="INCIDENT",
        entity_id=row.id,
        payload={"note_length": len(payload.note)},
    )
    db.commit()
    return _incident_dict(row)


@router.post("/incidents/{incident_id}/resolve")
def resolve_incident(
    incident_id: str,
    payload: IncidentResolveRequest,
    user: Annotated[User, Depends(require_roles("Administrator", "Analyst"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    row = db.scalar(select(Incident).where(Incident.id == incident_id, Incident.tenant_id == user.tenant_id))
    if row is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    previous = row.status
    row.status = "RESOLVED"
    row.disposition = payload.disposition
    append_audit_event(
        db,
        tenant_id=user.tenant_id,
        user_id=user.id,
        event_type="INCIDENT_RESOLVED",
        entity_type="INCIDENT",
        entity_id=row.id,
        previous_state=previous,
        new_state="RESOLVED",
        payload={"disposition": payload.disposition},
    )
    db.commit()
    return _incident_dict(row)


@router.get("/policies")
def list_policies(user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]) -> dict:
    policies = list(db.scalars(select(Policy).where(Policy.tenant_id == user.tenant_id).order_by(Policy.name.asc())))
    items = []
    for policy in policies:
        version = db.scalar(
            select(PolicyVersion).where(PolicyVersion.policy_id == policy.id, PolicyVersion.version == policy.current_version)
        )
        items.append(
            {
                "id": policy.id,
                "name": policy.name,
                "category": policy.category,
                "status": policy.status,
                "current_version": policy.current_version,
                "author": policy.author,
                "updated_at": _iso(policy.updated_at),
                "thresholds": None if version is None else {
                    "low": version.low_threshold,
                    "monitor": version.monitor_threshold,
                    "step_up": version.stepup_threshold,
                    "critical": version.critical_threshold,
                    "min_speech_seconds": version.min_speech_seconds,
                    "consecutive_windows": version.consecutive_windows,
                    "verification_method": version.verification_method,
                    "retention_rule": version.retention_rule,
                },
            }
        )
    return {"items": items, "count": len(items)}


@router.post("/policies", status_code=201)
def create_policy(
    payload: PolicyCreateRequest,
    user: Annotated[User, Depends(require_roles("Administrator"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    if not (payload.low_threshold <= payload.monitor_threshold <= payload.stepup_threshold <= payload.critical_threshold):
        raise HTTPException(status_code=422, detail="Policy thresholds must be ordered from low to critical")
    policy = Policy(
        tenant_id=user.tenant_id,
        name=payload.name,
        category=payload.category,
        status="DRAFT",
        current_version=1,
        author=user.full_name,
    )
    db.add(policy)
    db.flush()
    db.add(
        PolicyVersion(
            policy_id=policy.id,
            version=1,
            low_threshold=payload.low_threshold,
            monitor_threshold=payload.monitor_threshold,
            stepup_threshold=payload.stepup_threshold,
            critical_threshold=payload.critical_threshold,
            min_speech_seconds=payload.min_speech_seconds,
            consecutive_windows=payload.consecutive_windows,
            verification_method=payload.verification_method,
            retention_rule=payload.retention_rule,
        )
    )
    append_audit_event(
        db,
        tenant_id=user.tenant_id,
        user_id=user.id,
        event_type="POLICY_CREATED",
        entity_type="POLICY",
        entity_id=policy.id,
        new_state="DRAFT",
        payload={"name": policy.name, "version": 1},
    )
    db.commit()
    return {"id": policy.id, "name": policy.name, "status": policy.status, "version": 1}


@router.post("/policies/{policy_id}/publish")
def publish_policy(
    policy_id: str,
    user: Annotated[User, Depends(require_roles("Administrator"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    policy = db.scalar(select(Policy).where(Policy.id == policy_id, Policy.tenant_id == user.tenant_id))
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found")
    previous = policy.status
    policy.status = "PUBLISHED"
    append_audit_event(
        db,
        tenant_id=user.tenant_id,
        user_id=user.id,
        event_type="POLICY_PUBLISHED",
        entity_type="POLICY",
        entity_id=policy.id,
        previous_state=previous,
        new_state="PUBLISHED",
        policy_version=f"{policy.name}-v{policy.current_version}",
    )
    db.commit()
    return {"id": policy.id, "status": policy.status, "version": policy.current_version}


@router.post("/policies/{policy_id}/test")
def test_policy(
    policy_id: str,
    payload: PolicyTestRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    policy = db.scalar(select(Policy).where(Policy.id == policy_id, Policy.tenant_id == user.tenant_id))
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found")
    version = db.scalar(
        select(PolicyVersion).where(PolicyVersion.policy_id == policy.id, PolicyVersion.version == policy.current_version)
    )
    thresholds = PolicyThresholds(
        low=version.low_threshold,
        monitor=version.monitor_threshold,
        step_up=version.stepup_threshold,
        critical=version.critical_threshold,
        consecutive_high_windows=version.consecutive_windows,
    )
    evidence = [
        EvidenceInput("synthetic_speech", payload.synthetic_speech, explanation="Synthetic-speech test evidence"),
        EvidenceInput("speaker_mismatch", payload.speaker_mismatch, explanation="Speaker-mismatch test evidence"),
        EvidenceInput("prosody_anomaly", payload.prosody_anomaly, explanation="Prosody test evidence"),
        EvidenceInput("context_risk", payload.context_risk, explanation="Context test evidence"),
        EvidenceInput("channel_quality", payload.channel_quality, explanation="Audio-quality test evidence"),
    ]
    decision = TrustFusionEngine(thresholds).decide(evidence)
    return {
        "dry_run": True,
        "policy": policy.name,
        "policy_version": policy.current_version,
        "risk_index": decision.risk_index,
        "state": decision.state,
        "recommended_action": decision.recommended_action,
        "reason": decision.reason,
        "fusion_mode": decision.fusion_mode,
    }


@router.get("/trusted-voices")
def list_trusted_voices(user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]) -> dict:
    rows = list(
        db.scalars(
            select(TrustedVoiceProfile)
            .where(TrustedVoiceProfile.tenant_id == user.tenant_id)
            .order_by(TrustedVoiceProfile.created_at.desc())
        )
    )
    return {
        "items": [
            {
                "id": row.id,
                "identity_name": row.identity_name,
                "language": row.language,
                "status": row.status,
                "enrollment_quality": row.enrollment_quality,
                "sample_count": row.sample_count,
                "expires_at": _iso(row.expires_at),
                "last_verified_at": _iso(row.last_verified_at),
                "consent_recorded": True,
                "demo_profile": row.embedding_ciphertext == "DEMO_PROFILE_NO_REAL_EMBEDDING",
            }
            for row in rows
        ],
        "count": len(rows),
    }


@router.post("/trusted-voices/enroll", status_code=201)
def enroll_trusted_voice(
    payload: TrustedVoiceEnrollRequest,
    user: Annotated[User, Depends(require_roles("Administrator", "Operator"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    if not payload.consent_confirmed:
        raise HTTPException(status_code=422, detail="Explicit consent is required for enrollment")
    consent = ConsentRecord(tenant_id=user.tenant_id, identity_name=payload.identity_name, granted=True)
    db.add(consent)
    db.flush()
    profile = TrustedVoiceProfile(
        tenant_id=user.tenant_id,
        consent_id=consent.id,
        identity_name=payload.identity_name,
        language=payload.language,
        status="PENDING_MODEL",
        enrollment_quality=0,
        sample_count=payload.sample_count,
        embedding_ciphertext=None,
        expires_at=datetime.now(timezone.utc) + timedelta(days=180),
    )
    db.add(profile)
    db.flush()
    append_audit_event(
        db,
        tenant_id=user.tenant_id,
        user_id=user.id,
        event_type="VOICE_PROFILE_ENROLLED",
        entity_type="TRUSTED_VOICE",
        entity_id=profile.id,
        new_state="PENDING_MODEL",
        payload={"consent_recorded": True, "sample_count": payload.sample_count, "speaker_model_active": False},
    )
    db.commit()
    return {
        "id": profile.id,
        "status": profile.status,
        "message": "Consent and profile metadata were saved. A real speaker-verification model must be configured before activation.",
        "demo_only": True,
    }


@router.delete("/trusted-voices/{profile_id}")
def revoke_trusted_voice(
    profile_id: str,
    user: Annotated[User, Depends(require_roles("Administrator"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    profile = db.scalar(
        select(TrustedVoiceProfile).where(TrustedVoiceProfile.id == profile_id, TrustedVoiceProfile.tenant_id == user.tenant_id)
    )
    if profile is None:
        raise HTTPException(status_code=404, detail="Trusted voice profile not found")
    previous = profile.status
    profile.status = "REVOKED"
    consent = db.get(ConsentRecord, profile.consent_id)
    if consent:
        consent.granted = False
        consent.revoked_at = datetime.now(timezone.utc)
    profile.embedding_ciphertext = None
    append_audit_event(
        db,
        tenant_id=user.tenant_id,
        user_id=user.id,
        event_type="VOICE_PROFILE_REVOKED",
        entity_type="TRUSTED_VOICE",
        entity_id=profile.id,
        previous_state=previous,
        new_state="REVOKED",
        payload={"embedding_deleted": True},
    )
    db.commit()
    return {"id": profile.id, "status": profile.status, "embedding_deleted": True}


def _change_transaction_status(
    *, db: Session, user: User, transaction_id: str, new_status: str, event_type: str
) -> dict:
    transaction = db.scalar(
        select(SensitiveTransaction)
        .join(MonitoringSession, MonitoringSession.id == SensitiveTransaction.session_id)
        .where(SensitiveTransaction.id == transaction_id, MonitoringSession.tenant_id == user.tenant_id)
    )
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    previous = transaction.status
    transaction.status = new_status
    if new_status in {"ON_HOLD", "BLOCKED"}:
        transaction.hold_reason = "Manual operator action"
    append_audit_event(
        db,
        tenant_id=user.tenant_id,
        user_id=user.id,
        event_type=event_type,
        entity_type="TRANSACTION",
        entity_id=transaction.id,
        previous_state=previous,
        new_state=new_status,
        payload={"reference": transaction.reference},
    )
    db.commit()
    return {"id": transaction.id, "reference": transaction.reference, "status": transaction.status}


@router.post("/transactions/{transaction_id}/hold")
def hold_transaction(
    transaction_id: str,
    user: Annotated[User, Depends(require_roles("Administrator", "Operator"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    return _change_transaction_status(db=db, user=user, transaction_id=transaction_id, new_status="ON_HOLD", event_type="TRANSACTION_HELD")


@router.post("/transactions/{transaction_id}/release")
def release_transaction(
    transaction_id: str,
    user: Annotated[User, Depends(require_roles("Administrator", "Operator"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    return _change_transaction_status(db=db, user=user, transaction_id=transaction_id, new_status="RELEASED", event_type="TRANSACTION_RELEASED")


@router.post("/transactions/{transaction_id}/block")
def block_transaction(
    transaction_id: str,
    user: Annotated[User, Depends(require_roles("Administrator", "Operator"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    return _change_transaction_status(db=db, user=user, transaction_id=transaction_id, new_status="BLOCKED", event_type="TRANSACTION_BLOCKED")


@router.post("/verifications", status_code=201)
def create_verification(
    payload: VerificationCreateRequest,
    user: Annotated[User, Depends(require_roles("Administrator", "Operator"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    session = db.scalar(
        select(MonitoringSession).where(MonitoringSession.id == payload.session_id, MonitoringSession.tenant_id == user.tenant_id)
    )
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    verification = VerificationRequest(
        session_id=session.id,
        transaction_id=payload.transaction_id,
        method=payload.method,
        destination_masked=payload.destination_masked,
        status="PENDING",
        reason=payload.reason,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=3),
    )
    db.add(verification)
    db.flush()
    append_audit_event(
        db,
        tenant_id=user.tenant_id,
        user_id=user.id,
        event_type="VERIFICATION_SENT",
        entity_type="VERIFICATION",
        entity_id=verification.id,
        new_state="PENDING",
        payload={"method": verification.method, "destination": verification.destination_masked},
    )
    db.commit()
    return {"id": verification.id, "status": verification.status, "expires_at": _iso(verification.expires_at)}


@router.post("/verifications/{verification_id}/complete")
def complete_verification(
    verification_id: str,
    payload: VerificationCompleteRequest,
    user: Annotated[User, Depends(require_roles("Administrator", "Operator"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    verification = db.scalar(
        select(VerificationRequest)
        .join(MonitoringSession, MonitoringSession.id == VerificationRequest.session_id)
        .where(VerificationRequest.id == verification_id, MonitoringSession.tenant_id == user.tenant_id)
    )
    if verification is None:
        raise HTTPException(status_code=404, detail="Verification not found")
    previous = verification.status
    verification.status = payload.result
    verification.result = payload.result
    if payload.result == "PASSED" and verification.transaction_id:
        transaction = db.get(SensitiveTransaction, verification.transaction_id)
        if transaction and transaction.status == "ON_HOLD":
            transaction.status = "RELEASED"
    append_audit_event(
        db,
        tenant_id=user.tenant_id,
        user_id=user.id,
        event_type="VERIFICATION_COMPLETED",
        entity_type="VERIFICATION",
        entity_id=verification.id,
        previous_state=previous,
        new_state=payload.result,
        payload={"method": verification.method},
    )
    db.commit()
    return {"id": verification.id, "status": verification.status, "result": verification.result}


@router.get("/audit")
def list_audit(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(default=100, ge=1, le=500),
) -> dict:
    rows = list(
        db.scalars(
            select(AuditEvent)
            .where(AuditEvent.tenant_id == user.tenant_id)
            .order_by(AuditEvent.sequence.desc())
            .limit(limit)
        )
    )
    return {
        "items": [
            {
                "sequence": row.sequence,
                "id": row.id,
                "event_type": row.event_type,
                "entity_type": row.entity_type,
                "entity_id": row.entity_id,
                "previous_state": row.previous_state,
                "new_state": row.new_state,
                "model_version": row.model_version,
                "policy_version": row.policy_version,
                "action_result": row.action_result,
                "previous_hash": row.previous_hash,
                "event_hash": row.event_hash,
                "created_at": _iso(row.created_at),
            }
            for row in rows
        ],
        "count": len(rows),
    }


@router.post("/audit/verify")
def verify_audit(
    _user: Annotated[User, Depends(require_roles("Administrator", "Auditor"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    return verify_audit_chain(db)


@router.get("/models")
def list_models(user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]) -> dict:
    del user
    rows = list(db.scalars(select(ModelVersion).order_by(ModelVersion.name.asc())))
    live_rawnet = rawnetlite_adapter.status()
    items = []
    for row in rows:
        item = {
            "id": row.id,
            "name": row.name,
            "purpose": row.purpose,
            "version": row.version,
            "input_format": row.input_format,
            "device": row.device,
            "status": row.status,
            "installed": row.installed,
            "demo_only": row.demo_only,
            "limitations": row.limitations,
            "loaded_at": _iso(row.loaded_at),
        }
        if row.name == "RawNetLite":
            item.update({key: live_rawnet[key] for key in ("status", "installed", "device", "active", "missing_dependencies", "load_error")})
        items.append(item)
    return {"items": items}


@router.get("/evaluations")
def list_evaluations(user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]) -> dict:
    rows = list(
        db.scalars(select(EvaluationRun).where(EvaluationRun.tenant_id == user.tenant_id).order_by(EvaluationRun.imported_at.desc()))
    )
    return {
        "items": [
            {
                "id": row.id,
                "name": row.name,
                "dataset_name": row.dataset_name,
                "verified": row.verified,
                "metrics": json.loads(row.metrics_json),
                "coverage": json.loads(row.coverage_json),
                "imported_at": _iso(row.imported_at),
            }
            for row in rows
        ],
        "verified_benchmark_available": any(row.verified for row in rows),
    }


@router.post("/evaluations/import", status_code=201)
def import_evaluation(
    payload: EvaluationImportRequest,
    user: Annotated[User, Depends(require_roles("Administrator", "Analyst"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    row = EvaluationRun(
        tenant_id=user.tenant_id,
        name=payload.name,
        dataset_name=payload.dataset_name,
        verified=payload.verified,
        metrics_json=json.dumps(payload.metrics, sort_keys=True),
        coverage_json=json.dumps(payload.coverage, sort_keys=True),
    )
    db.add(row)
    db.flush()
    append_audit_event(
        db,
        tenant_id=user.tenant_id,
        user_id=user.id,
        event_type="EVALUATION_IMPORTED",
        entity_type="EVALUATION",
        entity_id=row.id,
        new_state="VERIFIED" if row.verified else "UNVERIFIED",
        payload={"dataset": row.dataset_name, "verified": row.verified},
    )
    db.commit()
    return {"id": row.id, "verified": row.verified}


@router.get("/integrations")
def list_integrations(user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]) -> dict:
    rows = list(db.scalars(select(Integration).where(Integration.tenant_id == user.tenant_id).order_by(Integration.name.asc())))
    return {
        "items": [
            {
                "id": row.id,
                "name": row.name,
                "kind": row.kind,
                "status": row.status,
                "mode": row.mode,
                "last_health_check": _iso(row.last_health_check),
                "config": json.loads(row.config_masked),
                "delivery_history": json.loads(row.delivery_history_json),
            }
            for row in rows
        ]
    }


@router.post("/integrations/{integration_id}/test")
def test_integration(
    integration_id: str,
    user: Annotated[User, Depends(require_roles("Administrator", "Operator"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    row = db.scalar(select(Integration).where(Integration.id == integration_id, Integration.tenant_id == user.tenant_id))
    if row is None:
        raise HTTPException(status_code=404, detail="Integration not found")
    tested_at = datetime.now(timezone.utc)
    payload = {"integration_id": row.id, "event": "phantom_vox.test", "timestamp": tested_at.isoformat()}
    signature = hmac.new(settings.jwt_secret.encode(), json.dumps(payload, sort_keys=True).encode(), hashlib.sha256).hexdigest()
    result = "DELIVERED" if row.status == "CONNECTED" else "SIMULATED" if row.mode == "DEMO" else "NOT_CONFIGURED"
    history = json.loads(row.delivery_history_json)
    history.insert(0, {"timestamp": tested_at.isoformat(), "result": result})
    row.delivery_history_json = json.dumps(history[:10])
    row.last_health_check = tested_at
    append_audit_event(
        db,
        tenant_id=user.tenant_id,
        user_id=user.id,
        event_type="INTEGRATION_TESTED",
        entity_type="INTEGRATION",
        entity_id=row.id,
        payload={"result": result, "mode": row.mode},
    )
    db.commit()
    return {"result": result, "mode": row.mode, "signed_payload": payload, "signature": signature}


@router.get("/notifications")
def list_notifications(user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]) -> dict:
    rows = list(
        db.scalars(
            select(Notification)
            .where(Notification.tenant_id == user.tenant_id, or_(Notification.user_id == user.id, Notification.user_id.is_(None)))
            .order_by(Notification.created_at.desc())
            .limit(30)
        )
    )
    return {"items": [{"id": row.id, "title": row.title, "body": row.body, "severity": row.severity, "read": row.read} for row in rows]}


@router.websocket("/ws/sessions/{session_id}")
async def session_websocket(websocket: WebSocket, session_id: str, token: str = Query(...)) -> None:
    try:
        payload = decode_access_token(token)
    except HTTPException:
        await websocket.close(code=4401)
        return
    with SessionLocal() as db:
        row = db.scalar(
            select(MonitoringSession).where(
                MonitoringSession.id == session_id,
                MonitoringSession.tenant_id == payload.get("tenant_id"),
            )
        )
        if row is None:
            await websocket.close(code=4404)
            return
        snapshot = session_snapshot(db, row.id) if row.demo_scenario else {"type": "session_update", "session": _session_dict(row)}
    await session_hub.connect(session_id, websocket)
    try:
        await websocket.send_json(snapshot)
        while True:
            message = await websocket.receive_text()
            if message == "ping":
                await websocket.send_json({"type": "pong", "timestamp": datetime.now(timezone.utc).isoformat()})
    except WebSocketDisconnect:
        pass
    finally:
        await session_hub.disconnect(session_id, websocket)
