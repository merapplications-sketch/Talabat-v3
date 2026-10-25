// TALABOT navigation facade (same Edge Function name). Prepared, NOT deployed.
// Selected provider: Geoapify. Set policy/key and deploy only in the separately authorized activation step.
// SUPABASE_URL and the project's public key (SUPABASE_ANON_KEY or SUPABASE_PUBLISHABLE_KEYS) are provided by Supabase.
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.45.4';
import { makeHandler } from './handler.js';

// Server-only configuration; defaults keep internal routing disabled until explicitly activated.
const env = {
  NAVIGATION_CONFIG: Deno.env.get('NAVIGATION_CONFIG') ?? '',
  GEOAPIFY_KEY: Deno.env.get('GEOAPIFY_KEY') ?? '',
  ALLOWED_ORIGINS: Deno.env.get('ALLOWED_ORIGINS') ?? '',
};

// The project uses the new publishable key; SUPABASE_ANON_KEY is the legacy name. Use whichever Supabase provides.
function publicKey(): string {
  const legacy = Deno.env.get('SUPABASE_ANON_KEY');
  if (legacy) return legacy;
  const raw = Deno.env.get('SUPABASE_PUBLISHABLE_KEYS') ?? '';
  try { const v = JSON.parse(raw); const first = typeof v === 'string' ? v : Object.values(v ?? {})[0]; if (typeof first === 'string') return first; } catch { /* plain value */ }
  return raw;
}

async function getUser(authorization: string): Promise<string | null> {
  if (!authorization.startsWith('Bearer ')) return null;
  const sb = createClient(Deno.env.get('SUPABASE_URL')!, publicKey(), {
    global: { headers: { Authorization: authorization } },
  });
  const { data, error } = await sb.auth.getUser();
  return error || !data?.user ? null : data.user.id;
}

// Binding point for Claude's separately approved durable, service-only atomic budget RPC.
// No schema/permission change is included. Missing RPC/secret -> tracking-only, never unmetered calls.
async function reserveBudget(v: { provider: string; credits: number; dailyCap: number; rps: number; requestId: string }) {
  const key = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
  if (!key) throw new Error('budget_unavailable');
  const sb = createClient(Deno.env.get('SUPABASE_URL')!, key, { auth: { persistSession: false } });
  const result = await sb.rpc('navigation_reserve_budget', {
    p_provider: v.provider, p_credits: v.credits, p_daily_cap: v.dailyCap, p_rps: v.rps, p_request_id: v.requestId,
  }).abortSignal(AbortSignal.timeout(3000));
  if (result.error) throw new Error('budget_unavailable');
  return result.data;
}
Deno.serve(makeHandler({ fetch, env, getUser, reserveBudget }));
