#!/usr/bin/env bash
# TALABOT Gate1 only. FAIL CLOSED on unavailable contract or E2E gates.
set -u -o pipefail
cd "$(dirname "$0")/.."
fail=0
echo "GATE1 source checks F01..F04"
if command -v node >/dev/null 2>&1; then
  node tools/gate1_contract_checks.cjs || fail=1
else
  echo "BLOCKED: Node unavailable; F01..F04 unexecuted" >&2
  fail=1
fi
echo "GATE1 existing core contracts"
if [ -n "${GATE1_QR_DEPS:-}" ] && [ -f "$GATE1_QR_DEPS/node_modules/qrcode-generator/qrcode.js" ] && [ -f "$GATE1_QR_DEPS/node_modules/jsqr/dist/jsQR.js" ]; then
  python3 tools/core_contracts_check.py "$GATE1_QR_DEPS" || fail=1
else
  echo "BLOCKED: core_contracts_check.py requires existing qrcode-generator/jsQR at GATE1_QR_DEPS; no packages installed" >&2
  fail=1
fi
echo "GATE1 eleven separate Supabase E2E scenarios"
python3 tools/gate1_e2e.py || fail=1
if [ "$fail" -ne 0 ]; then
  echo "GATE1_NO_GO: incomplete or failing required gates" >&2
  exit 1
fi
echo "GATE1_PASS: all mandatory gates executed"
