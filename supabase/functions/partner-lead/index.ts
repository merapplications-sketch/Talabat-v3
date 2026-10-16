// Supabase Edge Function `partner-lead` (Deno). NOT DEPLOYED. Setup: supabase/functions/partner-lead/README.md
import { makeHandler } from './handler.js';

Deno.serve(makeHandler(Deno.env.toObject(), { fetch }));
