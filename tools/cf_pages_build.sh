#!/usr/bin/env bash
# TALABOT BRIEF-CF1: static Cloudflare Pages Git build, no deploy or backend changes.
set -Eeuo pipefail
umask 022

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd -- "$ROOT"
OUT="$ROOT/site"

# Match the approved OPS preview bundle; do not copy SQL, tools, QA or secrets.
for file in customer.html driver.html merchant.html admin.html talabat-core.js; do
  if [[ ! -f "$file" || -L "$file" ]]; then
    printf 'CF1_STOP: missing or linked source file: %s\n' "$file" >&2
    exit 1
  fi
done
if [[ ! -d assets || -L assets ]] || [[ -n "$(find assets -type l -print -quit)" ]]; then
  printf 'CF1_STOP: assets absent or contain symbolic links\n' >&2
  exit 1
fi
if [[ -L "$OUT" ]]; then
  printf 'CF1_STOP: site output is a symlink\n' >&2
  exit 1
fi
rm -rf -- "$OUT"
mkdir -p -- "$OUT"
cp -- customer.html driver.html merchant.html admin.html talabat-core.js "$OUT/"
cp -R -- assets "$OUT/assets"

# The same two OPS-generated static files; no Workers, Functions, D1, or Vite.
printf '/*\n  X-Robots-Tag: noindex, nofollow\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: no-referrer\n' > "$OUT/_headers"
printf '<!doctype html><meta charset=utf-8><title>TALABOT Gate1 preview</title><ul><li><a href=driver.html>driver</a><li><a href=customer.html>customer</a><li><a href=merchant.html>merchant</a></ul>' > "$OUT/index.html"

for file in customer.html driver.html merchant.html admin.html talabat-core.js \
  assets/size-brief7/driver.css assets/driver-tech/device-notes-v3.js \
  assets/driver-tech/nav-cash-brief8.js index.html _headers; do
  if [[ ! -s "$OUT/$file" ]]; then
    printf 'CF1_STOP: required output missing or empty: %s\n' "$file" >&2
    exit 1
  fi
done

# Inspect every shipped file, including binary assets; never print matching secrets.
# Public Supabase anon keys are not private credentials, but service-role keys are banned.
blocked='service_role|talabot-pilot-20261106|talabot-safari-demo-20261115|sb_secret_[[:alnum:]_-]+|sk_(live|test)_[[:alnum:]_-]{12,}|github_pat_[[:alnum:]_]{20,}|gh[pousr]_[[:alnum:]_]{20,}|AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----|SUPABASE_SERVICE_ROLE_KEY|CLOUDFLARE_API_TOKEN[[:space:]]*[:=][[:space:]]*[^[:space:]]+|AWS_SECRET_ACCESS_KEY[[:space:]]*[:=]|(secret_key|private_key|api_token|access_token)[[:space:]]*[:=][[:space:]]*["\x27]?[[:alnum:]_+/-]{20,}'
while IFS= read -r -d '' file; do
  if LC_ALL=C grep -aEiq -- "$blocked" "$file"; then
    printf 'CF1_STOP: forbidden project reference or confidential credential in %s\n' "${file#"$OUT/"}" >&2
    exit 1
  fi
done < <(find "$OUT" -type f -print0)

printf 'CF1_STATIC_BUILD_PASS: %s files in site/ (no network, no deploy)\n' "$(find "$OUT" -type f | wc -l | tr -d ' ')"
