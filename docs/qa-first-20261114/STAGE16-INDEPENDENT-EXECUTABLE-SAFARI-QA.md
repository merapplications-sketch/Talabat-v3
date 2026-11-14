# TALABOT — STAGE 16 / Independent Executable Safari Demo QA

**Date:** 2026-11-14 · Asia/Dushanbe  
**Assignment:** [Issue #42](https://github.com/merapplications-sketch/Talabat-v3/issues/42) · [Master #26](https://github.com/merapplications-sketch/Talabat-v3/issues/26)  
**Mode:** Independent receiver-side import and conditional executable browser QA. No fixes, no production, no publishing.  
**Corrected customer demo source:** 3f74b29a7c4bcc89cef9e25dd73f574448ab7896  
**Delivered ZIP commit:** b8210fe7ca325f2ac10af09e8abfd03de1353a0a  
**Decision:** **ZIP_IMPORTED: BLOCKED** · **BROWSER QA: BLOCKED (NOT RUN)** · **FREE PUBLIC SAFARI PREVIEW REVIEW: NO-GO** · **PHASE2: NO-GO**.

## 1. Authoritative immutable delivery — previously accepted, not re-audited

The Stage15 programmer and PM independently accepted the actual binary GitHub archive, not the former source-only demo:

- Immutable download: [talabot-safari-demo-3f74b29a.zip](https://raw.githubusercontent.com/merapplications-sketch/Talabat-v3/b8210fe7ca325f2ac10af09e8abfd03de1353a0a/deliverables/stage15/talabot-safari-demo-3f74b29a.zip)
- [Publisher/source integrity manifest](https://github.com/merapplications-sketch/Talabat-v3/blob/b8210fe7ca325f2ac10af09e8abfd03de1353a0a/deliverables/stage15/zip-integrity.json): 967,486 bytes; **SHA256 20e674ae017b92a02ca937336f2fa54293fd79fc23e9d8ff559bd564046b82ae**; Git blob **7a7f83854f247880a4a56e21161a677aca582d2a**; **59 contained files, 45 WebP**, under safari-zero-cost-customer/; corrected fixture blob **a2336b6471c96a9a5ca921ccd13805eedf506e0b**.
- This **upstream** verification reports 59/59 CRC32 and SHA256 matching; it **does not prove ZIP import into this QA runner**. The proof has not been replayed. Previous Stage11–14 source, design and language simulation audits are accepted only within their original scope and were **not repeated**.
- Stage16 began with the exact supplied artifact URL, not old Git cloning or a reconstructed mock application.

## 2. Receiver import — actual attempts and failure boundary

| Evidence ID | Actual source/receiver operation | Observable result | Implication |
|---|---|---|---|
| R16-01 | Connected GitHub repository read of Issue #42, ZIP blob and Stage15 integrity metadata | File exists, matching immutable Git blob. GitHub connector fetch_file(encoding=base64) **returned encoded bytes**, 1,311,484 characters **including Base64 line breaks**; after whitespace removal 1,289,984 encoded characters, implying **967,486 binary bytes**. Header begins UEsDBBQA (ZIP PK header). | **GitHub connector binary acquisition: YES**. Only the remote connector response was available, not a receiver-local ZIP. This byte-size calculation is not a local SHA256 or local unpack operation. |
| R16-02 | Direct receiver local curl HEAD for the exact raw.githubusercontent.com artifact URL | **curl: (6) Could not resolve host: raw.githubusercontent.com**. Local DNS check likewise fails for github.com and api.github.com. | Container cannot directly download exact ZIP over current network. No repeated Git clone. |
| R16-03 | Container download helper for exact raw URL, and alternate GitHub raw route | Exact raw URL returned **download failed**. Alternate route reported not viewed/authorized, and web open of binary URLs returned **DisabledError**. | These routes did not materialize the archive. |
| R16-04 | Search automatically mounted local files and accessible cross-chat Library for the exact ZIP | Local /mnt/data had **no ZIP or extracted preview**. Library search found Stage15 handoff Markdown and old TALABOT materials, **not the binary ZIP**. The Stage15 handoff explicitly says independent receiver-local ZIP transfer was **NOT_VERIFIED**. | Metadata/receipt is not a usable executable artifact. No substitution with a prior source branch. |
| R16-05 | Check local browser prerequisites | /usr/bin/chromium available (launch verified: Chromium **144.0.7559.96**); Python Playwright is available. | Browser capability **IS AVAILABLE**; blocker is **binary handoff** to this file system, not a missing browser/package. |
| R16-06 | Start loopback preview / inspect receiver ZIP | **NOT STARTED**. No legitimate complete ZIP was present to hash/unzip/serve. | Do not report imported ZIP, CRC verification, screenshots, DOM, network requests or browser success. |

**Receiver acceptance:** **ZIP_IMPORTED = BLOCKED**. There is **no local path or measured receiver-side ZIP SHA256**, and no observed local 59-entry central directory or 45 WebP enumeration. The upstream manifest and connector's Base64 size do not satisfy the independent receiver import acceptance criterion.

**Precise technical blocker:** the GitHub connector runs in a tool environment that can **read the Base64 binary payload**, but this QA session has **no supported direct transfer operation to persist that payload into the local /mnt/data browser-test filesystem**. Existing local download routes are unable to reach/resolve the artifact endpoint. Work Cloud Browser local-file export into this runner was not available as a connected operation. **This is a transport handoff issue**, not evidence of any bug in the TALABOT demo.

A sanitized local receiver-attempt record was generated at **TALABOT_STAGE16_RECEIVER_BLOCKED.json** in the QA file area; it records BLOCKED and absence of runtime evidence, not a successful import.

## 3. Requested executable cases — actual status

**Safety gate:** test only if *the complete SHA-pinned ZIP has actually arrived locally*, is unpacked safely with 59 paths/45 WebP and SHA256 matches, and the browser is configured with disposable profile and blocked/logged non-loopback egress. This gate failed at import; therefore **the browser was not launched against a partial/imagined app**.

| Case | Requested behavior | Status in this execution | Genuine evidence |
|---|---|---|---|
| **S16-01** | Open original Home Dynamic Marketplace B without ChatGPT/TALABOT login | **BLOCKED — not executed** | No browser page, DOM, screenshot |
| **S16-02** | Categories, restaurants, campaigns and DineOut Gold | **BLOCKED — not executed** | No click or route evidence |
| **S16-03** | Restaurant Details v1.6 and Direction A mandatory/optional extras | **BLOCKED — not executed** | No chosen options/price/geometry |
| **S16-04** | Fake cart, quantity change, return/back/reload | **BLOCKED — not executed** | No in-browser cart assertions |
| **S16-05** | Real checkout, payment, chat blocked; no false success | **BLOCKED — not executed** | No click, intercepted RPC/DB, payment proof |
| **S16-06** | RU/EN first visit, toggles, persisted reload and ?lang | **BLOCKED — not executed** | Source fix previously accepted; no actual browser persistence proof |
| **S16-07** | 320/360/390/430 × RU/EN, source-faithful visuals | **BLOCKED — not executed** | 0/8 viewport-language cells; no screenshots/DOM dimensions |
| **S16-08** | Navigation and external links cannot make off-lab traffic | **BLOCKED — not executed** | No browser request/response/requestfailed or CSP violation traces |

**Executed numerator/denominator:** **0/8 interactive case groups**; **0/8** viewport-language combinations; **0 screenshot files**; **0 DOM measurement files**; **0 browser console captures**; **0 browser request traces**. **Actual browser-originating requests/failed requests: NOT OBSERVED because no browser run occurred**, *not* an observed zero-egress PASS.

Prior Chrome/source scans, Stage13 JavaScript simulation (8/8) and independent original CSS/asset identity are not counted as new Stage16 executable PASS. Any attempted unexpected external connection would stop an authorized future browser test; none was attempted by a TALABOT browser in this session, so no claim about the eventual page's egress is possible.

## 4. Remaining security, UX and Safari gaps

- **Production isolation:** source-level fake SDK, demo-only checkout guard and CSP from earlier reports remain under their prior acceptance; **independent runtime proof that no production/API/other off-origin requests are attempted remains UNTESTED**.
- **Real order/payment prevention:** **source-constrained** as reported previously, but interactive negative-path evidence on corrected ZIP remains **UNTESTED**. No actual order, wallet transaction, Supabase session or cash action was made.
- **Original visual identity:** no executable asset/stylesheet change was made by the consultant and historical code/design locks remain; **rendered comparisons are UNTESTED**. Dark old pilot login colors and demo banner 3.54:1 contrast issue remain **DEFERRED**, not repair authority.
- **Physical iPhone Safari:** **UNTESTED**. Headless Chromium availability is not a physical device/Safari PASS.
- **Public Safari preview hostname/Pages:** no URL provisioned, no publication performed, no Cloudflare or Supabase change; free no-login display cannot be accepted without receiver browser proof and separate owner authorization.

## 5. Narrowest next internal handoff — NO action required from owner

**Only unresolved prerequisite:** an authorized source/artifact custodian in the current team must provide the **same existing immutable ZIP** to the already installed independent QA runtime using an existing permitted cross-workspace **binary attachment/materialization path**, or an available Work Cloud Browser file download/export path **that actually makes the file accessible in that QA runtime**. No rebuild, fresh ZIP, new Git commit, credential, API permission, paid hosting, device purchase, app modification, GitHub Actions run or owner technical work. PM may route existing artifact access in its current process; **this consultant does not open tasks or dispatch teams**.

At receipt, the same reviewer records local SHA256, 59 entries/45 WebP and corrected fixture blob **then** serves the exact files on 127.0.0.1 with all nonlocal egress denied and attempted external URLs logged. Execute S16-01..08 with reproducible screenshots, DOM clientWidth/scrollWidth and bounding boxes, console/errors, requests/responses/requestfailed/WebSockets/CSP/navigation. Stop on first unintended off-loopback attempt. Only then consider a separately authorized **free isolated static HTTPS site without ChatGPT login, no production bindings**, subject to owner approval; **no deployment authorized now**.

## 6. Final decision and scope protection

**ZIP_IMPORTED: BLOCKED.** Binary content is reachable **inside the GitHub connector** and its encoded length matches the upstream expected byte count, but **was not transferred into the local browser runner**. The Stage16 executable test did **not run**. The specific file-transfer limitation is established, and the smallest non-owner dependency is identified.

**GO for public Safari preview review:** **NO-GO** until actual isolated browser network/security and UX evidence exists.  
**Formal product QA / C-01 / G1 / PHASE2:** **NO-GO**, unaffected by this synthetic-demo exercise.

No approved code, CSS, colors, logo, product design, SQL, Cloudflare, Supabase, credentials, live orders, financial settings, CI, production, deployment, merge or source artifact was changed. The review adds **one Markdown report to a documentation-only branch based on Stage15 ZIP delivery commit**. No new project tasks initiated.
