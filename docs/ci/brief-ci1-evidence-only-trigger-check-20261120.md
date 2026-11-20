# TALABOT — BRIEF-CI1 isolated CI delivery and evidence-only trigger test

**Code SHA:** `c1029e9293ea6051c7c5287c9ce2592800489346`
**Branch:** `ci/brief-ci1-20261120`; baseline `af466951`.
**Code scope:** only two GitHub Actions YAML files and two CI test tools. No product UI, core, SQL, Supabase, main, or live deployment changes.

## Verified GitHub Actions on the same code SHA

- **H-01:** [44741775594](https://github.com/merapplications-sketch/Talabat-v3/actions/runs/44741775594), `success`, 208 s; original local-auth UI `24/24`, zero H01 blockers. SEC-18 local `16/16`. Frozen financial and role checks retained.
- **Home / focused WebKit:** [44741775666](https://github.com/merapplications-sketch/Talabat-v3/actions/runs/44741775666), `success`, 68 s; RU/375 Home smoke, selected BRIEF-29 tests, financial parity against approved baseline, screenshot artifact.
- **Full visual suite on ordinary push:** intentionally `skipped`.
- **Evidence-only path check:** commit `43346b4845c9bf3464dd268e41dabce454b7f5af` changed this `docs/**` file without `[skip ci]`; no Actions runs were created at that SHA.

## CI-02 structural blocker (NOT ACCEPTED YET)

The repository default branch `main` contains **no** `.github/workflows/` files.
GitHub requires a workflow to exist on the default branch for `workflow_dispatch` and scheduled triggers. The full visual suite is configured for manual dispatch, but **cannot be proven to run from this isolated candidate until a separately approved default-branch CI-only bootstrap**. No bootstrap, merge, schedule, or deployment was performed.

## Safety

The exact two `git diff --exit-code` guards, legacy core/finance safeguards, SEC-18, and H-01 24/24 checks remain fail-closed. The full legacy visual suite is deferred only in push-fast mode; its code remains available for future authorized full execution. Evidence commits are filtered by `paths-ignore`; evidence rebases are non-fatal without hiding actual test failures.

**Decision:** CI-01/03/04/05 candidate PASS; CI-02 BLOCKED/UNTESTED; no final acceptance or live publish.
