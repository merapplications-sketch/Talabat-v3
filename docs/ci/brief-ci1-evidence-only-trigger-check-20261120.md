# TALABOT BRIEF-CI1 — evidence-only trigger check

Source candidate: `0a3fae9668b6bc778a33c1f2d26d4679d83d5a5b`.

This is a **documentation-only** change, deliberately committed **without** `[skip ci]`.
The two BRIEF-CI1 push workflows have `paths-ignore` entries covering
`docs/**`, `qa-shots/**`, and `*.md`; therefore this commit should not
start the H-01 or Home jobs.

No production/UI/source behavior, SQL, backend, or payment code changes.
