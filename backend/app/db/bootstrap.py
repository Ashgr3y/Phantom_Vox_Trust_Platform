from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import Base, SessionLocal, engine
from app.models.entities import (
    AuditEvent,
    ConsentRecord,
    Incident,
    Integration,
    ModelVersion,
    MonitoringSession,
    Policy,
    PolicyVersion,
    Role,
    SensitiveTransaction,
    Tenant,
    TrustedVoiceProfile,
    User,
)
from app.services.audit import append_audit_event


TENANT_ID = "11111111-1111-4111-8111-111111111111"
ADMIN_ID = "22222222-2222-4222-8222-222222222222"


def _seed(db: Session) -> None:
    if db.scalar(select(Tenant).where(Tenant.id == TENANT_ID)):
        return

    tenant = Tenant(id=TENANT_ID, name="Northstar Cooperative Bank")
    db.add(tenant)
    roles = {}
    for role_name in ("Administrator", "Operator", "Analyst", "Auditor", "Viewer"):
        role = Role(name=role_name)
        db.add(role)
        db.flush()
        roles[role_name] = role

    admin = User(
        id=ADMIN_ID,
        tenant_id=TENANT_ID,
        role_id=roles["Administrator"].id,
        full_name="Yash Kolhe",
        email="admin@phantomvox.local",
        password_hash=hash_password("PhantomVox@2026"),
    )
    operator = User(
        tenant_id=TENANT_ID,
        role_id=roles["Operator"].id,
        full_name="Priya Sharma",
        email="operator@phantomvox.local",
        password_hash=hash_password("Operator@2026"),
    )
    db.add_all([admin, operator])

    policy_templates = [
        ("Normal Support Call", "SUPPORT", 40, 65, 82, "SECURE_CALLBACK"),
        ("Password Reset", "IDENTITY", 30, 50, 72, "TRUSTED_DEVICE"),
        ("Bank Transfer", "PAYMENT", 35, 60, 80, "TRUSTED_DEVICE"),
        ("Vendor Payment", "PAYMENT", 32, 56, 76, "SUPERVISOR_APPROVAL"),
        ("Insurance Claim", "CLAIM", 36, 62, 81, "SECURE_CALLBACK"),
        ("Executive Approval", "EXECUTIVE", 28, 48, 70, "TRUSTED_DEVICE"),
    ]
    for name, category, low, monitor, critical, method in policy_templates:
        policy = Policy(
            tenant_id=TENANT_ID,
            name=name,
            category=category,
            status="PUBLISHED" if name == "Bank Transfer" else "DRAFT",
            current_version=1,
            author="Yash Kolhe",
        )
        db.add(policy)
        db.flush()
        db.add(
            PolicyVersion(
                policy_id=policy.id,
                version=1,
                low_threshold=low,
                monitor_threshold=monitor,
                stepup_threshold=critical,
                critical_threshold=critical,
                min_speech_seconds=3,
                consecutive_windows=2,
                verification_method=method,
                retention_rule="METADATA_ONLY",
                rules_json=json.dumps({"currency": "INR", "high_value_above": 1_000_000}),
            )
        )

    integration_data = [
        ("REST API", "API", "CONNECTED", "LIVE"),
        ("Session WebSockets", "WEBSOCKET", "CONNECTED", "LIVE"),
        ("Signed Webhooks", "WEBHOOK", "CONNECTED", "DEMO"),
        ("Twilio Media Streams", "TELEPHONY", "DISCONNECTED", "PLACEHOLDER"),
        ("SIP / Asterisk", "TELEPHONY", "DISCONNECTED", "PLACEHOLDER"),
        ("Banking Transaction API", "BANKING", "CONNECTED", "DEMO"),
        ("CRM", "CRM", "DISCONNECTED", "PLACEHOLDER"),
        ("SIEM", "SECURITY", "DEGRADED", "DEMO"),
        ("SMS Verification", "NOTIFICATION", "CONNECTED", "DEMO"),
        ("Microsoft Teams", "COLLABORATION", "DISCONNECTED", "FUTURE"),
    ]
    now = datetime.now(timezone.utc)
    for name, kind, status, mode in integration_data:
        db.add(
            Integration(
                tenant_id=TENANT_ID,
                name=name,
                kind=kind,
                status=status,
                mode=mode,
                last_health_check=now if status != "DISCONNECTED" else None,
                config_masked=json.dumps({"endpoint": "configured" if status == "CONNECTED" else "not configured"}),
                delivery_history_json="[]",
            )
        )

    db.add_all(
        [
            ModelVersion(
                name="RawNetLite",
                purpose="Synthetic-speech evidence",
                version="rawnetlite-checkpoint-1.0",
                input_format="16 kHz mono waveform, 3-second windows",
                device="runtime selected",
                status="ADAPTER_AVAILABLE",
                installed=True,
                demo_only=False,
                limitations="Uncalibrated checkpoint; benchmark evidence is not bundled.",
            ),
            ModelVersion(
                name="Speaker Verification Adapter",
                purpose="Consented speaker matching",
                version="adapter-1.0",
                input_format="Speaker embedding",
                device="not configured",
                status="DEMO_ONLY",
                installed=False,
                demo_only=True,
                limitations="ECAPA-TDNN is an integration slot and is not included.",
            ),
            ModelVersion(
                name="AASIST Adapter",
                purpose="Optional strong anti-spoofing detector",
                version="adapter-1.0",
                input_format="Audio waveform",
                device="not configured",
                status="NOT_INSTALLED",
                installed=False,
                demo_only=False,
                limitations="No AASIST architecture or checkpoint is included; the product never labels RawNetLite as AASIST.",
            ),
        ]
    )

    consent = ConsentRecord(tenant_id=TENANT_ID, identity_name="Aarav Mehta", granted=True)
    db.add(consent)
    db.flush()
    db.add(
        TrustedVoiceProfile(
            tenant_id=TENANT_ID,
            consent_id=consent.id,
            identity_name="Aarav Mehta",
            language="English - Indian",
            status="ACTIVE",
            enrollment_quality=0.92,
            sample_count=3,
            embedding_ciphertext="DEMO_PROFILE_NO_REAL_EMBEDDING",
            expires_at=now + timedelta(days=180),
            last_verified_at=now - timedelta(days=2),
        )
    )

    seeded_sessions = [
        ("Neha Kulkarni", "Hindi", 73, "STEP_UP_REQUIRED", 2_450_000, "ACTIVE"),
        ("Rohan Desai", "Marathi", 24, "LOW_RISK", 185_000, "ACTIVE"),
        ("Meera Iyer", "Tamil", 88, "CRITICAL", 6_700_000, "RESOLVED"),
    ]
    for index, (identity, language, risk, state, value, status) in enumerate(seeded_sessions, start=1):
        session = MonitoringSession(
            tenant_id=TENANT_ID,
            claimed_identity=identity,
            source="Contact Centre",
            language=language,
            state=state,
            risk_index=risk,
            uncertainty=0.12,
            duration_seconds=42 + index * 19,
            transaction_type="Vendor Payment",
            transaction_value=value,
            currency="INR",
            status=status,
            audio_retained=False,
            created_at=now - timedelta(minutes=index * 11),
        )
        db.add(session)
        db.flush()
        transaction_status = "ON_HOLD" if state in {"STEP_UP_REQUIRED", "CRITICAL"} else "PENDING"
        db.add(
            SensitiveTransaction(
                session_id=session.id,
                reference=f"TXN-DEMO-{index:04d}",
                transaction_type="Vendor Payment",
                value=value,
                currency="INR",
                status=transaction_status,
                hold_reason="Seeded demo record" if transaction_status == "ON_HOLD" else None,
            )
        )
        if state in {"STEP_UP_REQUIRED", "CRITICAL"}:
            db.add(
                Incident(
                    tenant_id=TENANT_ID,
                    session_id=session.id,
                    claimed_identity=identity,
                    source="Contact Centre",
                    language=language,
                    peak_risk=risk,
                    trigger="Multi-evidence risk threshold crossed",
                    prevented_action="Vendor payment placed on hold",
                    verification_result="FAILED" if state == "CRITICAL" else "PENDING",
                    severity="CRITICAL" if state == "CRITICAL" else "HIGH",
                    status="OPEN" if state != "CRITICAL" else "UNDER_REVIEW",
                    assigned_analyst="Ananya Rao" if state == "CRITICAL" else "Unassigned",
                    summary="Seeded demonstration incident. No raw audio is retained.",
                    model_version="trustfusion-demo-1.0",
                    policy_version="bank-transfer-v1",
                    created_at=session.created_at,
                )
            )

    db.flush()
    append_audit_event(
        db,
        tenant_id=TENANT_ID,
        user_id=ADMIN_ID,
        event_type="DEMO_DATA_SEEDED",
        entity_type="SYSTEM",
        entity_id=TENANT_ID,
        new_state="READY",
        payload={"records_are_demo": True, "raw_audio_retained": False},
    )
    db.commit()


def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)
    settings = get_settings()
    if settings.seed_demo_data:
        with SessionLocal() as db:
            _seed(db)
    if settings.database_url.startswith("sqlite"):
        with engine.begin() as connection:
            connection.execute(text("PRAGMA optimize"))
