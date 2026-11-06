#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
test ! -e tests/pilot/.runtime.json || { echo 'Existing isolated runtime found; preserve it and use a fresh checkout.'; exit 1; }
command -v docker >/dev/null
python3 -m venv tests/pilot/cash/.venv
source tests/pilot/cash/.venv/bin/activate
pip -q install 'psycopg[binary]==3.2.10' 'typing_extensions==4.15.0'
export PILOT_PATCH_STAGE=full PILOT_DRIVER_RETURNS=1 PILOT_CASH_ALLOCATION=1
cleanup(){ docker compose --env-file tests/pilot/.runtime.env -f tests/pilot/compose.yml down -v --remove-orphans; rm -f tests/pilot/.runtime.json tests/pilot/.runtime.env; }
trap cleanup EXIT
python tests/pilot/lab.py env
docker compose --env-file tests/pilot/.runtime.env -f tests/pilot/compose.yml up -d db
python tests/pilot/lab.py db
docker compose --env-file tests/pilot/.runtime.env -f tests/pilot/compose.yml up -d auth
python tests/pilot/lab.py app
docker compose --env-file tests/pilot/.runtime.env -f tests/pilot/compose.yml up -d rest
npm ci --prefix tests/pilot
python tests/pilot/cash/setup.py
echo 'Open http://127.0.0.1:8080 — Ctrl+C destroys this disposable lab.'
python tests/pilot/cash/serve.py
