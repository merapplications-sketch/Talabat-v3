#!/usr/bin/env bash
# BRIEF-20 temporary isolated dry run. NO PUSH. Uses literal git revert.
set -Eeuo pipefail
test "$GITHUB_REPOSITORY" = "merapplications-sketch/Talabat-v3"
test "$GITHUB_REF" = "refs/heads/review/unified-fix-brief15-20261117"
echo "BRIEF20_BASELINE 7c7e66094c10614c01ad7359cda7bc3740e8fcfd"
echo "BRIEF20_START $(git rev-parse HEAD)"
git config user.name "talabot-brief20-local-qa"
git config user.email "talabot-brief20-local-qa@users.noreply.github.com"
reverts=(d880a9980ea5034db290b5eac5b96aea263a0476 fe754168b60a7eb9293b26dd316c3a5342e1d1cc b923e8866032b41687c8480fb8602bf2b9b64c95 db353cedc0a12eef419cf80f0e21cbc595e41d91 46ca47b96393fda9eb2cf3b9784ba173c8e860f2 39f0f561e4dda55a979e552892e82ce1c51d4e10 c1835cdfab9c9944f07b55bbea21018b0789b012 2f73dda265009d7f35d3eaf56baca7a6f7592b0d 0441736c1bde404943cb95fcb1eba0ed4a9e9a7f)
for sha in "${reverts[@]}"; do
 echo "=== BRIEF20_GIT_REVERT_BEGIN $sha ==="
 git show --format='%h %s' --name-only "$sha" | head -15
 if ! git revert --no-commit "$sha"; then
   echo "BRIEF20_REVERT_CONFLICT $sha"
   git status --short
   git diff --name-only --diff-filter=U
   git diff -- customer.html | head -100
   exit 6
 fi
 git diff --cached --name-only
 if ! git diff --cached --quiet; then
   git commit -m "Revert \"$(git log -1 --format=%s "$sha")\" (BRIEF-20 Home B owner)" -m "This reverts commit $sha."
   echo "BRIEF20_REVERT_SUCCESS $sha"
 else
   git revert --abort 2>/dev/null || :
   echo "BRIEF20_EMPTY_REVERT $sha"
 fi
done
echo BRIEF20_PROBE_REVERTS_ALL_OK
git diff --stat 71912aa6934279012500748edb04dac85b630da5 HEAD -- customer.html
echo "BRIEF20_PROBE_NO_PUSH"
