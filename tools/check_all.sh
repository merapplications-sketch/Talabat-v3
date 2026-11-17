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
echo "GATE1 11 original + 5 new local Supabase E2E scenarios"
python3 tools/gate1_e2e.py || fail=1
echo "BRIEF-11 mandatory offline Playwright WebKit iPhone-layout C01..C07"
python3 tools/brief11_webkit_layout.py || fail=1
# BRIEF-14 is an EXPLICIT opt-in on its source-pinned isolated QA branch only.
# Gate1 F/core/16 LOCAL scenarios above run FIRST against untouched original seed;
# only then add more local-only identities/records for the four ORIGINAL app views.
if [ "${FULL_AUDIT_BRIEF14:-0}" = "1" ]; then
  if [ "${SUPABASE_LOCAL_URL:-}" != 'http://127.0.0.1:54321' ]; then
    echo 'FULL_AUDIT_BLOCKED: no disposable LOCAL Supabase URL' >&2
    fail=1
  else
    python3 tools/full_audit_seed.py || fail=1
    python3 tools/full_audit.py || fail=1
  fi
fi
# BRIEF-15: optional only on isolated review CI; fail closed on any verified visual regression.
if [ "${FULL_AUDIT_BRIEF15:-0}" = "1" ]; then
  echo "BRIEF15 WebKit real HTML F01..F10 source-backed visual regressions"
  python3 tools/brief15_webkit.py || fail=1
fi
# BRIEF-15b: explicit source-backed WebKit RU/375 EN/390 UI geometry gate.
# Runs only against the isolated synthetic fixture; no production credentials.
if [ "${FULL_AUDIT_BRIEF15B:-0}" = "1" ]; then
  echo "BRIEF15b WebKit closed-store, compact toast and nine G-01..G-09 checks"
  BRIEF15B_MODE=after python3 tools/brief15b_webkit.py || fail=1
fi
if [ "$fail" -ne 0 ]; then
  echo "GATE1_NO_GO: incomplete or failing required gates" >&2
  exit 1
fi
echo "GATE1_PASS: all mandatory gates executed"
