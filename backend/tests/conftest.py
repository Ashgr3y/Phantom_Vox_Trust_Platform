from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


_db_file = tempfile.NamedTemporaryFile(prefix="phantom-vox-test-", suffix=".db", delete=False)
_db_file.close()
os.environ["PHANTOM_VOX_DATABASE_URL"] = f"sqlite:///{_db_file.name}"
os.environ["PHANTOM_VOX_DEMO_TICK_SECONDS"] = "0.01"
os.environ["PHANTOM_VOX_SEED_DEMO_DATA"] = "true"

from app.main import app  # noqa: E402
from app.db.session import engine  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client
    engine.dispose()
    Path(_db_file.name).unlink(missing_ok=True)


@pytest.fixture(scope="session")
def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@phantomvox.local", "password": "PhantomVox@2026"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
