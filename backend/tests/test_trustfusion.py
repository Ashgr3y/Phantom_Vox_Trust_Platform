from app.policy.trustfusion import EvidenceInput, TrustFusionEngine


def test_quality_gate_abstains() -> None:
    decision = TrustFusionEngine().decide(
        [
            EvidenceInput("synthetic_speech", 0.2),
            EvidenceInput("speaker_mismatch", 0.2),
            EvidenceInput("context_risk", 0.2),
            EvidenceInput("channel_quality", 0.18),
        ]
    )
    assert decision.state == "INSUFFICIENT_AUDIO"
    assert decision.recommended_action == "SECURE_CALLBACK"


def test_missing_evidence_is_not_treated_as_zero_risk() -> None:
    decision = TrustFusionEngine().decide(
        [
            EvidenceInput("synthetic_speech", 0.1, available=False),
            EvidenceInput("speaker_mismatch", 0.1, available=False),
            EvidenceInput("context_risk", 0.9, available=False),
            EvidenceInput("channel_quality", 0.9),
        ]
    )
    assert decision.state == "UNCERTAIN"
    assert decision.recommended_action == "START_TRUSTED_VERIFICATION"


def test_recent_high_risk_windows_reach_critical() -> None:
    evidence = [
        EvidenceInput("synthetic_speech", 0.98, explanation="Synthetic evidence high"),
        EvidenceInput("speaker_mismatch", 0.96, explanation="Speaker mismatch high"),
        EvidenceInput("prosody_anomaly", 0.88),
        EvidenceInput("context_risk", 0.99),
        EvidenceInput("out_of_distribution", 0.82),
        EvidenceInput("channel_quality", 0.92),
    ]
    decision = TrustFusionEngine().decide(evidence, recent_risks=[88, 91], previous_state="STEP_UP_REQUIRED")
    assert decision.state == "CRITICAL"
    assert decision.risk_index >= 80
