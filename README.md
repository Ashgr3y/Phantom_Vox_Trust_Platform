# Phantom Vox

**Hear the truth. Stop the fraud.**

Phantom Vox is a judge-ready voice trust and fraud-prevention platform. It continuously combines voice evidence, speaker-consistency evidence, context, channel quality, and policy state. When recent consecutive windows cross a configured threshold, the platform can place a simulated sensitive transaction on hold, initiate secondary verification, create an incident, and write a tamper-evident audit event.

This repository is deliberately honest about what is real and what is simulated.

## What works end to end

- Responsive React and TypeScript operations console with eight workspaces
- Light and dark themes, keyboard focus, responsive navigation, dialogs, loading, empty, and error states
- FastAPI REST and authenticated WebSocket APIs
- SQLite persistence with PostgreSQL-compatible SQLAlchemy configuration
- Per-tenant sessions, decisions, transactions, verifications, incidents, policies, integrations, and audit events
- Four deterministic judge scenarios
- Recency-weighted TrustFusion policy baseline with quality gating, uncertainty, consecutive-window logic, and hysteresis
- Stored transaction transition from `PENDING` to `ON_HOLD`
- Stored verification and incident transitions
- SHA-256 hash-chained audit log with integrity verification
- Existing RawNetLite architecture and checkpoint preserved behind an optional lazy-loading adapter
- Raw audio disabled by default and upload temporary files deleted after processing
- Evaluation report importer that shows no accuracy claims until real labeled evidence is supplied
- Docker, Windows, and Ubuntu launch paths
- Automated backend, frontend, and build tests

## Honest capability labels

| Capability | Status |
|---|---|
| RawNetLite model files | Included |
| RawNetLite upload inference | Real when optional ML dependencies are installed |
| TrustFusion judge scenarios | Clearly labelled policy-based demo simulation |
| Transaction hold | Real stored state in the local database |
| Verification workflow | Real stored demo state; no real SMS is sent |
| Speaker verification | Adapter position and demo evidence only; ECAPA-TDNN is not bundled |
| AASIST | Not installed and never claimed as active |
| Twilio, SIP, Teams, CRM | Clearly labelled placeholder or future integrations |
| Accuracy, EER, language robustness | Not claimed until a labeled report is imported |

## Quick start

Requirements: Python 3.11 or 3.12 and Node.js 20 or newer.

### Ubuntu or macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements-base.txt
npm --prefix frontend install
npm --prefix frontend run build
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`.

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements-base.txt
npm --prefix frontend install
npm --prefix frontend run build
Set-Location backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

You can also run `powershell -ExecutionPolicy Bypass -File scripts\start.ps1`.

### Demo credentials

```text
Email:    admin@phantomvox.local
Password: PhantomVox@2026
```

These credentials are for local demonstration only. Change the JWT secret and account credentials before sharing a deployment.

## Enable RawNetLite audio uploads

The dashboard and judge scenarios work with the base dependencies. Install the optional ML dependencies to run the included checkpoint on uploaded WAV, FLAC, or OGG files:

```bash
pip install -r backend/requirements-ml.txt
```

The RawNetLite output is shown as an **uncalibrated evidence score**, not an impersonation probability.

## Five-minute judge demo

1. Sign in and show the Overview privacy card: raw-audio retention is off.
2. Select **Start judge demo**.
3. Use **Mid-call clone** and start monitoring.
4. Explain that the first windows look normal, then recent synthetic, speaker-mismatch, and context evidence rises.
5. Show the stored transaction change to `ON_HOLD`.
6. Show trusted-device verification and the critical incident.
7. Open Investigations to review the risk timeline and action trail.
8. Open Privacy & Audit and select **Verify audit integrity**.
9. Open Model Trust and point out that no benchmark values are fabricated.

The exact presenter script is in [docs/JUDGE_DEMO_SCRIPT.md](docs/JUDGE_DEMO_SCRIPT.md).

## Tests

```bash
cd backend
../.venv/bin/python -m pytest -q

cd ../frontend
npm test
npm run build
```

Current verified result in the supplied package:

- Backend: 8 tests passed
- Frontend: 4 tests passed
- TypeScript and Vite production build: passed
- Python syntax compilation: passed
- Docker configuration included but not executed in the build environment because Docker was unavailable

## Repository map

```text
frontend/             React operations console
backend/app/           FastAPI, persistence, policy, streaming, and APIs
backend/tests/         API, prevention, privacy, and policy tests
models/rawnetlite/     Preserved RawNetLite architecture and checkpoint
evaluation/            Labeled score protocol and transparent metric script
adapters/              Optional Windows loopback adapter
docs/                  Architecture, security, evaluation, judge, and API documents
scripts/               Windows, Ubuntu, seed, and test helpers
```

## Security defaults

- Raw-audio retention is off.
- CORS is restricted to configured origins.
- API and WebSocket access require a signed access token.
- File extension and upload size are validated.
- Sensitive actions are role-gated and audited.
- Database queries are tenant-scoped.
- Temporary uploads are deleted even after an inference error.
- Production mode rejects the bundled development JWT secret.

## Important documentation

- [Quick start](QUICK_START.md)
- [Architecture](docs/ARCHITECTURE.md)
- [API guide](docs/API_GUIDE.md)
- [Model card](docs/MODEL_CARD.md)
- [Privacy and security](docs/PRIVACY_AND_SECURITY.md)
- [Threat model](docs/THREAT_MODEL.md)
- [Evaluation guide](docs/EVALUATION_GUIDE.md)
- [Requirements traceability](docs/REQUIREMENTS_TRACEABILITY.md)
- [Judge questions and answers](docs/JUDGE_QA.md)
- [Known limitations](docs/KNOWN_LIMITATIONS.md)

## License and provenance

The original package's `LICENSE` and `NOTICE` files are preserved. The executable detector in this package is `RawNetLite`, not AASIST. Verify the checkpoint's training-data rights, provenance, and commercial-use conditions before any external deployment.
