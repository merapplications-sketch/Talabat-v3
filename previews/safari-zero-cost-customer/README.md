# TALABOT — Safari synthetic customer preview / STAGE 10
**Status: ARTIFACT STAGED IN GIT ONLY — NOT HOSTED, NOT PUBLISHED, NOT C-01**

- Source: `1cb85361d698d5da787d927a4c9ae7bd213c68c1` (approved original `customer.html` / `talabat-core.js`). Branch: `review/safari-zero-cost-synthetic-demo-20261113`.
- Demo entry: `index.html`. The approved Customer CSS, component layout, original embedded logo and palette are preserved byte-for-byte inside this *copied* demo document; the original product files in root remain untouched.
- Visual paths retained from the original: Home Dynamic Marketplace B, Restaurant Details v1.6, Product Customization Direction A, cart, DineOut Premium Gold, campaign/category sections. Runtime data is synthetic, based on `tools/qa_all.py` FIX and existing local 3D graphics. Only RU and EN are originally supported by this customer source.
- No TALABOT account, ChatGPT login or token needed. Local fake `supabase.createClient` returns a synthetic Customer session; not a real Auth, no real order/purchase.
- Checkout/payment, live chat, backend mutations, maps and geolocation disabled in demo guard; only safe local fake navigation/cart.
- CSP in page **once**, `default-src 'none'; connect-src 'none'; form-action 'none'`, only same-directory scripts/styles/images allowed; local sandbox transport APIs deny. No Supabase SDK shipped. `_headers` supplies equivalent policy when hosted on Cloudflare Pages later.
- All `assets/3d` are original repository blobs, including source license; no external images/fonts/CDN.
- **Static scan**: source JavaScript compiled syntactically with V8; 0 external service literal URLs and 0 production keys in demo HTML/JS/CSS. **Browser network recording, screenshots, widths and physical Safari NOT EXECUTED** because this session has no checkout and cannot run the artifact locally from this connector. Do not claim browser zero-request evidence or Safari approval until external independent review.
- Historical `tests/generated/candidate-preview.html` is admin-focused and unsafe to publish unchanged; this new customer demo is independent.
- Publication route **PROPOSED ONLY**: separate free static Cloudflare Pages project with isolated `pages.dev` hostname (or separate zero-cost GitHub Pages project), uploading *this preview directory only*. No custom domain or access cost required as a plan, subject to availability/security review and explicit owner approval. Do **not** replace existing TALABOT Pages/GitHub Pages or ChatGPT Sites. No public URL exists for this artifact now.
- Required reviewer action: validate local Safari-capable static server with no external network, DOM and request log at 320/360/390/430 RU and EN; Home→restaurant→required add-ons→fake cart→back→DineOut; assert zero egress and no order RPC. Then security/design sign-off, then owner approves exact publication. iPhone Safari remains a separate physical test.
- Owner dark-color feedback is **DEFERRED**, not accepted redesign; original source colors stay unchanged.

**Formal E2E 0/51; Admin 0/21; PHASE2 NO-GO.** No C-01, production, Cloudflare changes, SQL or CI.
