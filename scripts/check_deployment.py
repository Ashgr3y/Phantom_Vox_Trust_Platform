"""Run from any machine/cloud shell against the deployed judge demo.

Uses the fictional, public demo account unless DEMO_EMAIL/DEMO_PASSWORD override it.
Creates a demo session, performs real inference, verifies live updates and audit.
"""
import argparse
import io
import json
import math
import os
import struct
import wave
from urllib.parse import urlencode, urlsplit

import httpx
from websockets.sync.client import connect


def check(base_url: str) -> dict:
    base_url = base_url.rstrip("/")
    with httpx.Client(base_url=base_url, timeout=120, follow_redirects=True) as client:
        def call(method, path, **kwargs):
            response = client.request(method, "/api/v1" + path, **kwargs)
            response.raise_for_status()
            return response.json()

        website = client.get("/")
        website.raise_for_status()
        assert 'id="root"' in website.text
        deep_link = client.get("/live-guard")
        deep_link.raise_for_status()
        assert 'id="root"' in deep_link.text
        health = call("GET", "/health")
        assert health["database"] == "connected" and health["ml_active"]
        models = call("GET", "/health/models")["models"]
        assert models[0]["active"] and models[0]["load_error"] is None
        login = call("POST", "/auth/login", json={
            "email": os.environ.get("DEMO_EMAIL", "admin@phantomvox.local"),
            "password": os.environ.get("DEMO_PASSWORD", "PhantomVox@2026"),
        })
        token = login["access_token"]
        client.headers["Authorization"] = "Bearer " + token
        assert call("GET", "/dashboard/summary")["demo_data"]
        snapshot = call("POST", "/demo/start", json={"scenario": "mid_call_clone", "autoplay": False})
        session_id = snapshot["session"]["id"]
        parts = urlsplit(base_url)
        ws_base = ("wss" if parts.scheme == "https" else "ws") + "://" + parts.netloc
        ws_url = ws_base + "/api/v1/ws/sessions/" + session_id + "?" + urlencode({"token": token})
        with connect(ws_url, open_timeout=30) as socket:
            assert json.loads(socket.recv(timeout=30))["session"]["id"] == session_id
            socket.send("ping")
            assert json.loads(socket.recv(timeout=30))["type"] == "pong"
            for _ in range(7):
                snapshot = call("POST", f"/demo/{session_id}/advance")
                assert json.loads(socket.recv(timeout=30))["session"]["id"] == session_id
        assert snapshot["transaction"]["status"] == "ON_HOLD"
        assert snapshot["verification"]["status"] == "FAILED" and snapshot["incident_id"]
        audio = io.BytesIO()
        with wave.open(audio, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(16000)
            wav.writeframes(b"".join(struct.pack("<h", int(3000 * math.sin(2 * math.pi * 220 * n / 16000))) for n in range(48000)))
        result = call("POST", f"/sessions/{session_id}/audio", files={"file": ("smoke-test.wav", audio.getvalue(), "audio/wav")})
        assert result["model"] == "RawNetLite" and result["windows"]
        assert 0 <= result["synthetic_score"] <= 1 and result["raw_audio_retained"] is False
        assert call("POST", "/audit/verify")["valid"]
        return {"url": base_url, "website": "passed", "deep_link": "passed", "login": "passed",
                "dashboard": "passed", "websocket": "passed", "prevention_demo": "passed",
                "real_ml_upload": "passed", "audit": "passed", "model_device": models[0]["device"],
                "inference_score": result["synthetic_score"],
                "note": "Synthetic tone checks execution only, not detection accuracy. A consented speech sample and browser upload check are also required."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--allow-local-http", action="store_true")
    args = parser.parse_args()
    parts = urlsplit(args.url)
    if parts.scheme != "https" and not (args.allow_local_http and parts.scheme == "http" and parts.hostname in {"localhost", "127.0.0.1"}):
        parser.error("Use the public HTTPS URL")
    try:
        print(json.dumps(check(args.url), indent=2))
    except Exception as exc:
        # Never print a WebSocket URL containing its access token.
        raise SystemExit(f"Deployment check failed ({type(exc).__name__}); inspect server logs securely.") from None
