from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def uuid4_str() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Tenant(Base):
    __tablename__ = "tenants"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    name: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Role(Base):
    __tablename__ = "roles"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    name: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    role_id: Mapped[str] = mapped_column(ForeignKey("roles.id"))
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    role: Mapped[Role] = relationship(lazy="joined")
    tenant: Mapped[Tenant] = relationship(lazy="joined")


class MonitoringSession(Base):
    __tablename__ = "sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    claimed_identity: Mapped[str] = mapped_column(String(160))
    organization: Mapped[str] = mapped_column(String(160), default="Northstar Cooperative Bank")
    source: Mapped[str] = mapped_column(String(80), default="Judge Demo")
    language: Mapped[str] = mapped_column(String(80), default="English - Indian")
    state: Mapped[str] = mapped_column(String(40), default="WAITING_FOR_AUDIO", index=True)
    risk_index: Mapped[float] = mapped_column(Float, default=0)
    uncertainty: Mapped[float] = mapped_column(Float, default=1)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    transaction_type: Mapped[str] = mapped_column(String(100), default="Vendor Payment")
    transaction_value: Mapped[float] = mapped_column(Float, default=0)
    currency: Mapped[str] = mapped_column(String(8), default="INR")
    operator: Mapped[str] = mapped_column(String(120), default="Priya Sharma")
    model_version: Mapped[str] = mapped_column(String(80), default="trustfusion-demo-1.0")
    policy_version: Mapped[str] = mapped_column(String(80), default="bank-transfer-v1")
    demo_scenario: Mapped[str | None] = mapped_column(String(80), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", index=True)
    audio_retained: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class AudioWindow(Base):
    __tablename__ = "audio_windows"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), index=True)
    sequence: Mapped[int] = mapped_column(Integer)
    start_seconds: Mapped[float] = mapped_column(Float)
    end_seconds: Mapped[float] = mapped_column(Float)
    speech_seconds: Mapped[float] = mapped_column(Float, default=3)
    quality: Mapped[float] = mapped_column(Float, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (Index("idx_audio_window_session_sequence", "session_id", "sequence", unique=True),)


class EvidenceScore(Base):
    __tablename__ = "evidence_scores"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), index=True)
    audio_window_id: Mapped[str | None] = mapped_column(ForeignKey("audio_windows.id", ondelete="CASCADE"), nullable=True)
    name: Mapped[str] = mapped_column(String(80), index=True)
    score: Mapped[float] = mapped_column(Float)
    quality: Mapped[float] = mapped_column(Float, default=1)
    available: Mapped[bool] = mapped_column(Boolean, default=True)
    explanation: Mapped[str] = mapped_column(Text)
    model_version: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RiskDecision(Base):
    __tablename__ = "risk_decisions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), index=True)
    sequence: Mapped[int] = mapped_column(Integer)
    risk_index: Mapped[float] = mapped_column(Float)
    state: Mapped[str] = mapped_column(String(40), index=True)
    recommended_action: Mapped[str] = mapped_column(String(80))
    actual_action: Mapped[str] = mapped_column(String(80), default="CONTINUE_MONITORING")
    reason: Mapped[str] = mapped_column(Text)
    model_version: Mapped[str] = mapped_column(String(80))
    policy_version: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (Index("idx_risk_decision_session_sequence", "session_id", "sequence", unique=True),)


class Incident(Base):
    __tablename__ = "incidents"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"), index=True)
    claimed_identity: Mapped[str] = mapped_column(String(160))
    source: Mapped[str] = mapped_column(String(80))
    language: Mapped[str] = mapped_column(String(80))
    peak_risk: Mapped[float] = mapped_column(Float)
    trigger: Mapped[str] = mapped_column(String(160))
    prevented_action: Mapped[str] = mapped_column(String(160))
    verification_result: Mapped[str] = mapped_column(String(40), default="PENDING")
    severity: Mapped[str] = mapped_column(String(20), index=True)
    status: Mapped[str] = mapped_column(String(32), default="OPEN", index=True)
    assigned_analyst: Mapped[str] = mapped_column(String(120), default="Unassigned")
    summary: Mapped[str] = mapped_column(Text)
    analyst_notes: Mapped[str] = mapped_column(Text, default="")
    disposition: Mapped[str | None] = mapped_column(String(40), nullable=True)
    model_version: Mapped[str] = mapped_column(String(80))
    policy_version: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class SensitiveTransaction(Base):
    __tablename__ = "sensitive_transactions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), unique=True, index=True)
    reference: Mapped[str] = mapped_column(String(40), unique=True)
    transaction_type: Mapped[str] = mapped_column(String(100))
    value: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(8), default="INR")
    status: Mapped[str] = mapped_column(String(32), default="PENDING", index=True)
    hold_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class VerificationRequest(Base):
    __tablename__ = "verification_requests"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), index=True)
    transaction_id: Mapped[str | None] = mapped_column(ForeignKey("sensitive_transactions.id"), nullable=True)
    method: Mapped[str] = mapped_column(String(60))
    destination_masked: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(32), default="PENDING", index=True)
    reason: Mapped[str] = mapped_column(Text)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    result: Mapped[str | None] = mapped_column(String(40), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Action(Base):
    __tablename__ = "actions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    session_id: Mapped[str | None] = mapped_column(ForeignKey("sessions.id"), nullable=True, index=True)
    incident_id: Mapped[str | None] = mapped_column(ForeignKey("incidents.id"), nullable=True, index=True)
    action_type: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(32))
    actor_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    details: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ConsentRecord(Base):
    __tablename__ = "consent_records"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    identity_name: Mapped[str] = mapped_column(String(160))
    granted: Mapped[bool] = mapped_column(Boolean, default=True)
    text_version: Mapped[str] = mapped_column(String(40), default="consent-v1")
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class TrustedVoiceProfile(Base):
    __tablename__ = "trusted_voice_profiles"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    consent_id: Mapped[str] = mapped_column(ForeignKey("consent_records.id"))
    identity_name: Mapped[str] = mapped_column(String(160), index=True)
    language: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")
    enrollment_quality: Mapped[float] = mapped_column(Float)
    sample_count: Mapped[int] = mapped_column(Integer, default=3)
    embedding_ciphertext: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Policy(Base):
    __tablename__ = "policies"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    name: Mapped[str] = mapped_column(String(140))
    category: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(24), default="DRAFT")
    current_version: Mapped[int] = mapped_column(Integer, default=1)
    author: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class PolicyVersion(Base):
    __tablename__ = "policy_versions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    policy_id: Mapped[str] = mapped_column(ForeignKey("policies.id", ondelete="CASCADE"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    low_threshold: Mapped[float] = mapped_column(Float, default=35)
    monitor_threshold: Mapped[float] = mapped_column(Float, default=60)
    stepup_threshold: Mapped[float] = mapped_column(Float, default=80)
    critical_threshold: Mapped[float] = mapped_column(Float, default=80)
    min_speech_seconds: Mapped[float] = mapped_column(Float, default=3)
    consecutive_windows: Mapped[int] = mapped_column(Integer, default=2)
    verification_method: Mapped[str] = mapped_column(String(60), default="TRUSTED_DEVICE")
    retention_rule: Mapped[str] = mapped_column(String(80), default="METADATA_ONLY")
    rules_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (Index("idx_policy_version_unique", "policy_id", "version", unique=True),)


class Integration(Base):
    __tablename__ = "integrations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    kind: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(24), default="DISCONNECTED")
    mode: Mapped[str] = mapped_column(String(24), default="DEMO")
    last_health_check: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    config_masked: Mapped[str] = mapped_column(Text, default="{}")
    delivery_history_json: Mapped[str] = mapped_column(Text, default="[]")


class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(160))
    body: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(20))
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    sequence: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id: Mapped[str] = mapped_column(String(36), unique=True, default=uuid4_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    entity_type: Mapped[str] = mapped_column(String(60))
    entity_id: Mapped[str] = mapped_column(String(80), index=True)
    previous_state: Mapped[str | None] = mapped_column(String(80), nullable=True)
    new_state: Mapped[str | None] = mapped_column(String(80), nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(80), nullable=True)
    policy_version: Mapped[str | None] = mapped_column(String(80), nullable=True)
    action_result: Mapped[str] = mapped_column(String(80), default="SUCCESS")
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    previous_hash: Mapped[str] = mapped_column(String(64))
    event_hash: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    dataset_name: Mapped[str] = mapped_column(String(160))
    metrics_json: Mapped[str] = mapped_column(Text, default="{}")
    coverage_json: Mapped[str] = mapped_column(Text, default="{}")
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ModelVersion(Base):
    __tablename__ = "model_versions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    name: Mapped[str] = mapped_column(String(120), index=True)
    purpose: Mapped[str] = mapped_column(String(160))
    version: Mapped[str] = mapped_column(String(80))
    input_format: Mapped[str] = mapped_column(String(160))
    device: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(32))
    installed: Mapped[bool] = mapped_column(Boolean, default=False)
    demo_only: Mapped[bool] = mapped_column(Boolean, default=False)
    limitations: Mapped[str] = mapped_column(Text)
    loaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
