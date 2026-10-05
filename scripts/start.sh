#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_dir"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
.venv/bin/python -m pip install -r backend/requirements-base.txt
if [[ ! -d frontend/node_modules ]]; then
  npm --prefix frontend install
fi
npm --prefix frontend run build
cd backend
../.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
