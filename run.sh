#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
[ -f .env ] || cp .env.example .env
set -a; source .env; set +a
exec uvicorn app.main:app --host "${AGW_HOST:-127.0.0.1}" --port "${AGW_PORT:-8000}" --reload
