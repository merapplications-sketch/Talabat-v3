// index.ts settlement binding (review of f174ce9, blocker 2) — LOCAL only: index.ts transpiled with TypeScript, Supabase client
// and Deno stubbed; no network, no project. Checks: RPC name / argument names, error -> throw, answer passed through as is.
//   node tools/navigation_index_binding_check.mjs <path to typescript module>
import fs from 'node:fs'; import { createRequire } from 'node:module';
const ts = createRequire(import.meta.url)(process.argv[2]);
let fails = 0; const ok = (c, m) => { console.log((c ? 'PASS ' : 'FAIL ') + m); if (!c) fails++; };
const handlerUrl = new URL('../supabase/functions/route/handler.js', import.meta.url).href;
let src = fs.readFileSync(new URL('../supabase/functions/route/index.ts', import.meta.url), 'utf8')
  .replace(/import \{ createClient \} from '[^']+';/, 'const createClient = globalThis.__createClient;')
  .replace("'./handler.js'", JSON.stringify(handlerUrl)) + '\nglobalThis.__bind = { reserveBudget, settleBudget };\n';
const js = ts.transpileModule(src, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText;
const envv = { SUPABASE_URL: 'https://x.test', SUPABASE_SECRET_KEYS: '{"default":"sk"}' };
globalThis.Deno = { env: { get: k => envv[k] }, serve: () => {} };
let calls = [], answer = null;
globalThis.__createClient = () => ({ rpc: (name, args) => { calls.push({ name, args }); return { abortSignal: async () => answer }; } });
await import('data:text/javascript;base64,' + Buffer.from(js).toString('base64'));
const { settleBudget } = globalThis.__bind;
answer = { data: { recorded: true, extra: 1 }, error: null };
const r = await settleBudget({ provider: 'geoapify', credits: 2, requestId: 'id-1' });
ok(calls[0].name === 'navigation_settle_budget' && JSON.stringify(calls[0].args) === JSON.stringify({ p_provider: 'geoapify', p_request_id: 'id-1', p_total_credits: 2 }),
  'settle RPC called with the call id and the total: ' + JSON.stringify(calls[0]));
ok(r && r.recorded === true, 'answer passed through to the handler (it accepts only recorded:true)');
answer = { data: null, error: { message: 'permission denied' } };
let threw = false; try { await settleBudget({ provider: 'geoapify', credits: 2, requestId: 'id-1' }); } catch { threw = true; }
ok(threw, 'RPC error -> throws (not swallowed)');
envv.SUPABASE_SECRET_KEYS = ''; threw = false; try { await settleBudget({ provider: 'geoapify', credits: 2, requestId: 'id-1' }); } catch { threw = true; }
ok(threw, 'no service key -> throws (not a silent success)');
console.log(`\nNAVIGATION INDEX BINDING CHECK ${fails ? 'FAILS ' + fails : 'OK'}`); process.exit(fails ? 1 : 0);
