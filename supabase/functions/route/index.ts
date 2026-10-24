// TALABOT — Edge Function «route» (batch B). Prepared for review — NOT deployed.
// Deploy only after approval:  supabase secrets set ORS_KEY=... ALLOWED_ORIGINS=https://<site>
//                              supabase functions deploy route
// SUPABASE_URL and the project's public key (SUPABASE_ANON_KEY or SUPABASE_PUBLISHABLE_KEYS) are provided by Supabase.
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.45.4';
import { makeHandler } from './handler.js';

const env = {
  ORS_KEY: Deno.env.get('ORS_KEY') ?? '',
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

Deno.serve(makeHandler({ fetch, env, getUser }));
