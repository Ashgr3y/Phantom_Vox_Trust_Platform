import io

import pytest

from app.core.config import Settings
from app.inference.rawnetlite import rawnetlite_adapter


@pytest.mark.parametrize("prefix", ["postgres://", "postgresql://"])
def test_provider_database_url_selects_installed_driver(prefix):
    settings = Settings(database_url=prefix + "user:pass@db/phantomvox", _env_file=None)
    assert settings.database_url == "postgresql+psycopg://user:pass@db/phantomvox"


def test_production_rejects_ephemeral_database():
    settings = Settings(environment="production", jwt_secret="x" * 48, database_url="sqlite:///:memory:", _env_file=None)
    with pytest.raises(RuntimeError, match="managed PostgreSQL"):
        settings.validate_production()


def test_real_checkpoint_upload_and_websocket(client, auth_headers):
    np = pytest.importorskip("numpy")
    sf = pytest.importorskip("soundfile")
    torch = pytest.importorskip("torch")
    torch.set_num_threads(1)
    rawnetlite_adapter.warmup()
    status = rawnetlite_adapter.status()
    assert status["active"] and status["load_error"] is None
    response = client.post("/api/v1/demo/start", headers=auth_headers, json={"scenario": "genuine", "autoplay": False})
    assert response.status_code == 201
    session_id = response.json()["session"]["id"]
    token = auth_headers["Authorization"].removeprefix("Bearer ")
    with client.websocket_connect(f"/api/v1/ws/sessions/{session_id}?token={token}") as socket:
        assert socket.receive_json()["session"]["id"] == session_id
        socket.send_text("ping")
        assert socket.receive_json()["type"] == "pong"
    audio = io.BytesIO()
    sf.write(audio, (0.1 * np.sin(2 * np.pi * 220 * np.arange(48000) / 16000)).astype("float32"), 16000, format="WAV")
    response = client.post(f"/api/v1/sessions/{session_id}/audio", headers=auth_headers,
                           files={"file": ("inference-smoke.wav", audio.getvalue(), "audio/wav")})
    assert response.status_code == 200
    result = response.json()
    assert result["model"] == "RawNetLite" and result["windows"]
    assert 0 <= result["synthetic_score"] <= 1 and result["raw_audio_retained"] is False
    assert client.post("/api/v1/audit/verify", headers=auth_headers).json()["valid"]
