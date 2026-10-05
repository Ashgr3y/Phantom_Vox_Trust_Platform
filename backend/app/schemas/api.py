from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=128)


class SessionCreate(BaseModel):
    claimed_identity: str = Field(min_length=2, max_length=160)
    source: str = "Browser Microphone"
    language: str = "English - Indian"
    transaction_type: str = "Vendor Payment"
    transaction_value: float = Field(default=0, ge=0, le=1_000_000_000)
    currency: str = Field(default="INR", min_length=3, max_length=8)


class DemoStartRequest(BaseModel):
    scenario: Literal["genuine", "mid_call_clone", "poor_quality", "high_context_uncertain"] = "mid_call_clone"
    autoplay: bool = True


class IncidentNoteRequest(BaseModel):
    note: str = Field(min_length=2, max_length=4000)


class IncidentResolveRequest(BaseModel):
    disposition: Literal["GENUINE", "FRAUD", "INCONCLUSIVE"]


class VerificationCreateRequest(BaseModel):
    session_id: str
    transaction_id: str | None = None
    method: Literal["TRUSTED_DEVICE", "OTP", "SECURE_CALLBACK", "SUPERVISOR_APPROVAL"] = "TRUSTED_DEVICE"
    destination_masked: str = "+91 •••••• 1842"
    reason: str = "Risk policy requires secondary verification"


class VerificationCompleteRequest(BaseModel):
    result: Literal["PASSED", "FAILED", "CANCELLED", "EXPIRED"]


class PolicyCreateRequest(BaseModel):
    name: str = Field(min_length=3, max_length=140)
    category: str = Field(min_length=3, max_length=80)
    low_threshold: float = Field(default=35, ge=0, le=100)
    monitor_threshold: float = Field(default=60, ge=0, le=100)
    stepup_threshold: float = Field(default=80, ge=0, le=100)
    critical_threshold: float = Field(default=80, ge=0, le=100)
    min_speech_seconds: float = Field(default=3, ge=1, le=30)
    consecutive_windows: int = Field(default=2, ge=1, le=10)
    verification_method: str = "TRUSTED_DEVICE"
    retention_rule: str = "METADATA_ONLY"

    @field_validator("monitor_threshold")
    @classmethod
    def validate_monitor(cls, value: float, info) -> float:
        low = info.data.get("low_threshold", 0)
        if value < low:
            raise ValueError("monitor_threshold must be greater than or equal to low_threshold")
        return value


class PolicyTestRequest(BaseModel):
    synthetic_speech: float = Field(ge=0, le=1)
    speaker_mismatch: float = Field(ge=0, le=1)
    prosody_anomaly: float = Field(ge=0, le=1)
    context_risk: float = Field(ge=0, le=1)
    channel_quality: float = Field(ge=0, le=1)


class TrustedVoiceEnrollRequest(BaseModel):
    identity_name: str = Field(min_length=2, max_length=160)
    language: str = Field(min_length=2, max_length=80)
    consent_confirmed: bool
    sample_count: int = Field(default=3, ge=3, le=10)


class EvaluationImportRequest(BaseModel):
    name: str
    dataset_name: str
    verified: bool = False
    metrics: dict[str, float | int | str | None]
    coverage: dict[str, Any] = {}


class EvidenceInputSchema(BaseModel):
    name: str
    score: float = Field(ge=0, le=1)
    quality: float = Field(default=1, ge=0, le=1)
    available: bool = True
    explanation: str = ""
    model_version: str = "rule-demo-1.0"
