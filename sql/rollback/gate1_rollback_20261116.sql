-- TALABOT Gate1 restrictive pre-apply LIVE ACL rollback; schema-only baseline SHA256
-- 4de26eb4c964e595e3b61865ce65772477ae4573c7e9b5817ed3f374bac808cf
-- Scope: public.driver_ping, public.deliver_order, report_driver_cash_short,
-- tickets_one_open_per_order and tickets_one_open_payment_per_order only.
-- This is NOT a rollback of orders, customer data, wallet, or support rows.
-- Run strictly with psql -X -v ON_ERROR_STOP=1 --single-transaction.
-- If 1 payment + 1 unrelated open ticket exists, rebuilding the original
-- single-open-ticket index FAILS; transaction aborts atomically (no silent loss).
DROP FUNCTION IF EXISTS public.report_driver_cash_short(bigint,numeric,text);
DROP FUNCTION IF EXISTS public.driver_ping(boolean);

CREATE OR REPLACE FUNCTION "public"."driver_ping"("p_online" boolean) RETURNS "void"
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$
begin
  if auth.uid() is null then raise exception 'auth'; end if;
  update profiles
     set online = coalesce(p_online, false), last_seen = now(),
         lat = case when coalesce(p_online, false) then lat end,
         lng = case when coalesce(p_online, false) then lng end,
         loc_acc = case when coalesce(p_online, false) then loc_acc end,
         loc_updated = case when coalesce(p_online, false) then loc_updated end
   where id = auth.uid() and role = 'driver' and driver_status = 'approved';
end $$;


ALTER FUNCTION "public"."driver_ping"("p_online" boolean) OWNER TO "postgres";

CREATE OR REPLACE FUNCTION "public"."deliver_order"("p_id" bigint, "p_cash" numeric DEFAULT NULL::numeric, "p_note" "text" DEFAULT NULL::"text", "p_photo" "text" DEFAULT NULL::"text") RETURNS "void"
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $_$
declare o orders; iscash boolean;
begin
  select * into o from orders where id = p_id for update;
  if not found then raise exception 'not_found'; end if;
  if o.driver_id is distinct from auth.uid() or o.status <> 'pickedup' then raise exception 'bad_transition'; end if;
  -- the photo must be in this courier's folder for this order: <courier id>/<order id>/<file>.jpg
  if p_photo is not null and p_photo !~ ('^' || auth.uid()::text || '/' || p_id::text || '/[A-Za-z0-9_-]{8,64}\.jpg$') then raise exception 'bad_value'; end if;
  if coalesce(o.leave_at_door, false) and p_photo is null then raise exception 'photo_required'; end if;
  iscash := o.payment ~ '^(cash|Cash|Наличн)';
  if iscash then
    if p_cash is null or p_cash < 0 then raise exception 'cash_required'; end if;
    if p_cash <> (o.total - coalesce(o.wallet_used, 0)) and coalesce(trim(p_note), '') = '' then raise exception 'note_required'; end if;
  end if;
  update orders set status = 'delivered', done_at = now(),
    cash_collected = case when iscash then p_cash end,
    cash_note = case when iscash then left(p_note, 200) end,
    delivery_photo = p_photo,
    arrived_cust_at = coalesce(arrived_cust_at, now())
  where id = p_id;
end $_$;


ALTER FUNCTION "public"."deliver_order"("p_id" bigint, "p_cash" numeric, "p_note" "text", "p_photo" "text") OWNER TO "postgres";

DROP INDEX IF EXISTS public.tickets_one_open_payment_per_order;
DROP INDEX IF EXISTS public.tickets_one_open_per_order;
CREATE UNIQUE INDEX "tickets_one_open_per_order" ON "public"."support_tickets" USING "btree" ("order_id") WHERE (("order_id" IS NOT NULL) AND ("status" = ANY (ARRAY['open'::"text", 'in_progress'::"text"])));

-- Restore PRE-APPLY LIVE permissions (not the historic baseline's anon grants).
-- Exact original function definitions remain pinned; no anonymous EXECUTE
-- may ever be reintroduced by this rollback.
REVOKE ALL ON FUNCTION public.driver_ping(boolean) FROM PUBLIC, anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.driver_ping(boolean) TO authenticated, service_role;
REVOKE ALL ON FUNCTION public.deliver_order(bigint,numeric,text,text) FROM PUBLIC, anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.deliver_order(bigint,numeric,text,text) TO authenticated, service_role;
