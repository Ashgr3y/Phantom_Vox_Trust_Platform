# Phantom Vox Quick Start

## Fastest local judge demo

1. Install Python 3.11 or 3.12 and Node.js 20 or newer.
2. Open a terminal in the project directory.
3. Run the commands for your platform.

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

### Ubuntu

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements-base.txt
npm --prefix frontend install
npm --prefix frontend run build
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

4. Open `http://127.0.0.1:8000`.
5. Sign in with `admin@phantomvox.local` and `PhantomVox@2026`.
6. Select **Start judge demo**, choose **Mid-call clone**, and start monitoring.

## Optional real RawNetLite inference

Stop the server, return to the project root, and install:

```bash
pip install -r backend/requirements-ml.txt
```

Restart the server. In Live Guard, create a session and use **Upload audio**. The model score is uncalibrated evidence and must not be presented as verified accuracy.

## Docker Compose

```bash
docker compose up --build
```

The default Docker image includes CPU RawNetLite inference. Compose checks the actual model at startup. A base-only local image can still be built with `INSTALL_ML=false` and `PHANTOM_VOX_REQUIRE_ML=false`.

For a public HTTPS deployment with managed PostgreSQL, see [Public deployment](docs/DEPLOYMENT.md).

## Common fixes

- Port 8000 busy: replace `--port 8000` with `--port 8010`.
- Blank page after editing the frontend: run `npm --prefix frontend run build` again.
- RawNetLite unavailable: install `backend/requirements-ml.txt`.
- Database reset: stop the server, move `phantomvox.db` to a backup name, then restart.
- Windows script policy error: run PowerShell as your user and use `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` if permitted by your organization.
