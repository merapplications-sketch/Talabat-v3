# .31 continuation34 — application audit and mail transport gate

Source ea65f5289f3d19ccc5d3dbb65b59650e23e01370 unchanged/clean; Sites active hosting41 verified. Previous evidence f8f9bc10217a2c24af76b62877c9b81182655a4c. No new deployment, migrations or persistent application writes.

V6.4.2 passed for implemented TALABOT authentication paths:16 rendered form combinations, full first-party Auth call inventory/manual review, live metadata corroboration; source core hash equals prior published-byte evidence. Canonical JSON+CSV updated. Effective counts1passed/330untested-or-partial/2failed/12NA. See continuation34/V6.4.2.md; do not generalize to password recovery/MFA/provider support.

Live read-only anon calls to6 RPCs rejected42501. Active synthetic caller permitted catalog, finance/orders/support permissions false. These are SQL-role probes, not HTTP JWT lifecycle proof or populated-resource IDOR closure.

cash_balances direct driver path and dispatch_tick role-only predicate remain candidates requiring runtime disabled-account proof. cash-balance-ban-probe.sql aborted at cash_allocation_immutable BEFORE access assertions. Cleanup users0/stores0/orders0/pilotfixturefalse verified. DO NOT bypass cash allocation guard or repeat same invalid fixture. Next requires supported application allocation/state transitions with independent proof object and no protected order mutation. dispatch_tick cannot be invoked broadly on live order offers merely to test a candidate.

Log test:precheck users/audit/errors0 and matching active transactions0. New native confirmation expired2min, no assertions. Absence cannot prove historic nonexecution vsrollback. No active confirmation remains; next needs an owner-ready native confirmation of exact rollback-only test, not repeated blind calls.

TRACE10 deployed-route probes returned405/no marker via proxy; actual built worker rejects7paths, permitsGET/HEAD. V13.4.4 remains partial because origin/provider/production attribution is not established.

Mail authorization:recipient merapplications@gmail.com; at most2 recovery emails and1 incident email subject starts TALABOT TEST. Used0/0. NO mailbox login permission, NO SMTP-sender use of recipient, NO paid signup. Recipient absent from Auth users and org team (team has1 other member); default Supabase SMTP cannot deliver there. CustomSMTP remains off. Account creation form prefilled email then closed without submission; do not claim created. Do not add org membership to enable mail. Need approved existing SMTP sender or owner-approved provider+domain setup; user chooses sender, secrets entered only in provider controls. After sender ready, account password creation uses manual secure handoff (browserAuth is sign-in only), then request recovery once and tell user to checkInbox/Spam. Do not request password work before transport ready. Alert needs genuine event-to-transport integration, not a standalone manual email.

Options:continuation34/OPTIONS-AR.md includes local existing host, Free target conditional on quota, separate Pro org from$25/mo and additionalprojectsfrom$10/mo plususage. No upgrade of current org containingproduction. Localnetwork tests do not prove managedIP quota. No services created/purchased.

Five accounts/passwords/sessions and protectedorders1/2/3/receipts unchanged; #3unsettled. Existing synthetic AAL2 preserved. No production/main/design/accounting-policy/internal-route changes. Remaining independent operation/permission inventory and correct fixture preparation are NOT externally blocked or claimed exhausted. Evidence tests saved; not yet automatically added to app deployment gate. Next prioritise actual app guards, not more prep-tool tests.
