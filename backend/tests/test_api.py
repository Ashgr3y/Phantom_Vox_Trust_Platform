from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.inference.rawnetlite import rawnetlite_adapter


def test_health_and_authentication(client: TestClient, auth_headers: dict[str, str]) -> None:
    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["raw_audio_retention"] is False
    protected = client.get("/api/v1/dashboard/summary")
    assert protected.status_code == 401
    dashboard = client.get("/api/v1/dashboard/summary", headers=auth_headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["demo_data"] is True


def test_complete_mid_call_prevention_workflow(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post(
        "/api/v1/demo/start",
        headers=auth_headers,
        json={"scenario": "mid_call_clone", "autoplay": False},
    )
    assert response.status_code == 201
    session_id = response.json()["session"]["id"]
    snapshot = response.json()
    for _ in range(8):
        response = client.post(f"/api/v1/demo/{session_id}/advance", headers=auth_headers)
        assert response.status_code == 200
        snapshot = response.json()
    assert snapshot["transaction"]["status"] == "ON_HOLD"
    assert snapshot["verification"]["status"] == "FAILED"
    assert snapshot["incident_id"] is not None
    assert snapshot["session"]["audio_retained"] is False
    assert max(point["risk_index"] for point in snapshot["timeline"]) >= 80
    audit = client.post("/api/v1/audit/verify", headers=auth_headers)
    assert audit.status_code == 200
    assert audit.json()["valid"] is True


def test_poor_audio_abstains(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post(
        "/api/v1/demo/start",
        headers=auth_headers,
        json={"scenario": "poor_quality", "autoplay": False},
    )
    session_id = response.json()["session"]["id"]
    response = client.post(f"/api/v1/demo/{session_id}/advance", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["session"]["state"] == "INSUFFICIENT_AUDIO"
    assert response.json()["transaction"]["status"] == "PENDING"


def test_policy_create_publish_and_dry_run(client: TestClient, auth_headers: dict[str, str]) -> None:
    create = client.post(
        "/api/v1/policies",
        headers=auth_headers,
        json={
            "name": "Test High Value Payment",
            "category": "PAYMENT",
            "low_threshold": 35,
            "monitor_threshold": 60,
            "stepup_threshold": 78,
            "critical_threshold": 82,
            "consecutive_windows": 2,
        },
    )
    assert create.status_code == 201
    policy_id = create.json()["id"]
    test = client.post(
        f"/api/v1/policies/{policy_id}/test",
        headers=auth_headers,
        json={"synthetic_speech": 0.9, "speaker_mismatch": 0.8, "prosody_anomaly": 0.7, "context_risk": 0.95, "channel_quality": 0.9},
    )
    assert test.status_code == 200
    assert test.json()["dry_run"] is True
    publish = client.post(f"/api/v1/policies/{policy_id}/publish", headers=auth_headers)
    assert publish.status_code == 200
    assert publish.json()["status"] == "PUBLISHED"


def test_audio_upload_is_deleted_after_processing(client: TestClient, auth_headers: dict[str, str], monkeypatch) -> None:
    create = client.post(
        "/api/v1/sessions",
        headers=auth_headers,
        json={"claimed_identity": "Test Caller", "transaction_value": 1000},
    )
    session_id = create.json()["id"]
    captured: dict[str, str] = {}

    def fake_analyze(path: str) -> dict:
        captured["path"] = path
        assert Path(path).exists()
        return {
            "model": "RawNetLite",
            "model_version": "test",
            "score_type": "UNCALIBRATED_EVIDENCE",
            "duration_seconds": 1,
            "synthetic_score": 0.2,
            "peak_synthetic_score": 0.2,
            "windows": [],
            "raw_audio_retained": False,
        }

    monkeypatch.setattr(rawnetlite_adapter, "analyze", fake_analyze)
    response = client.post(
        f"/api/v1/sessions/{session_id}/audio",
        headers=auth_headers,
        files={"file": ("sample.wav", b"RIFF-demo-bytes", "audio/wav")},
    )
    assert response.status_code == 200
    assert response.json()["raw_audio_retained"] is False
    assert not Path(captured["path"]).exists()
