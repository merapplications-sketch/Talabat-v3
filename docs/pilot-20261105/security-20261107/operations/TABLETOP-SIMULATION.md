# Test-only tabletop packet — SIMULATED, not executed

Date 2026-11-07. This is a facilitator script and expected decision record, not evidence of a completed exercise. No key rotation, account compromise, loss, notification or restore actually occurred in preparing it. Use INCIDENT-RESPONSE.md boundaries unchanged. No browser/provider actions are authorized by this packet.

Current coordinating-reviewer baseline: .19 source `fd665456d30eb28612c13da93df7e6d71da9ec94`, hosting29, deployment `appgdep_6aef2b64e05c819181b2d2aa9a925f1b`, succeeded2026-11-07 13:45:27UTC. Customer and merchant sessions observed working per root. Consult `../CURRENT-RESUME.md` before any exercise; verify source/deployment/DB mapping again at kickoff. This document does not independently establish runtime controls. No tabletop was executed by this baseline update.

Participants to assign: commander, application owner, provider operator, recorder and independent observer. Start only after all agree the exercise uses fictional events and synthetic identifiers. Record actual exercise timestamps separately from the scenario clock.

| Scenario clock | Fictional inject | Required decision/evidence | Correct current limitation |
|---|---|---|---|
| T+00 | Scanner reports an invented privileged credential in a test build | Classify credential; identify test project and exposure interval; plan containment and evidence preservation | Do not supply a real key or assert an actual leak |
| T+10 | Simulated attacker holds two app sessions | List all revocation surfaces; decide how to isolate a disposable fixture | Database ban is not proof all Auth/Realtime/signed URL access ended |
| T+20 | Simulated dashboard shows missing synthetic order rows and object bytes | Inventory artifacts and choose a separate restore destination | Free Plan backup absence and no restore target prevent a real restore claim |
| T+35 | Fictional notification is “sent” but receiver gives no acknowledgement | Escalate to assigned owner; record delivery as unverified | No delivered-alert or on-call acceptance |
| T+50 | Fictional request spike reaches direct Supabase API | Identify direct-API exposure; request provider evidence without traffic generation | Managed-zone access and enforceable cost caps remain unverified |
| T+65 | Facilitator asks whether service can reopen | Require integrity reconciliation and access tests; enumerate unresolved gates | No pass based on tabletop discussion or fabricated recovery times |

Expected findings from the supplied evidence, not new observed failures: no demonstrated recoverable project backup; no timed isolated restore; operational owners/channels unassigned in this packet; no confirmed notification delivery; no confirmed managed-zone controls or enforceable spending ceiling; global session revocation coverage remains incomplete until newer evidence establishes otherwise.

Exercise record template: date/time; actual participants; inject; decision; authorized actor; evidence/reference; unresolved dependency; owner; due date. Do not prefill completion signatures. Completion means the discussion happened and decisions were captured; it never means technical controls passed. A later live restore requires the separate-target authorization and artifact gates in the runbook.
