// TALABOT — Edge Function «route» (batch B). Prepared for review — NOT deployed.
// Deploy only after approval:  supabase secrets set ORS_KEY=... ALLOWED_ORIGINS=https://<site>
//                              supabase functions deploy route
// SUPABASE_URL and SUPABASE_ANON_KEY are provided by Supabase to every function.
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.45.4';
import { makeHandler } from './handler.js';

const env = {
  ORS_KEY: Deno.env.get('ORS_KEY') ?? '',
  ALLOWED_ORIGINS: Deno.env.get('ALLOWED_ORIGINS') ?? '',
};

async function getUser(authorization: string): Promise<string | null> {
  if (!authorization.startsWith('Bearer ')) return null;
  const sb = createClient(Deno.env.get('SUPABASE_URL')!, Deno.env.get('SUPABASE_ANON_KEY')!, {
    global: { headers: { Authorization: authorization } },
  });
  const { data, error } = await sb.auth.getUser();
  return error || !data?.user ? null : data.user.id;
}

Deno.serve(makeHandler({ fetch, env, getUser }));
