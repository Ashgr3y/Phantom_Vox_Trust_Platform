#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_dir/backend"
../.venv/bin/python -m pytest -q
cd "$project_dir/frontend"
npm test
npm run build
