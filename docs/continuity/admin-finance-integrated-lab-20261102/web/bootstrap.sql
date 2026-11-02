create role anon nologin;
create role authenticated nologin;
create role service_role nologin;
create schema auth;
create table auth.users(id uuid primary key,email text,raw_user_meta_data jsonb,phone text);
CREATE OR REPLACE FUNCTION auth.uid()
 RETURNS uuid
 LANGUAGE sql
 STABLE
AS $function$
  select 
  coalesce(
    nullif(current_setting('request.jwt.claim.sub', true), ''),
    (nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'sub')
  )::uuid
$function$
;
grant usage on schema auth to public;
grant execute on function auth.uid() to public;
set check_function_bodies=off;
create type public."order_status" as enum('pending','preparing','ready','pickedup','delivered','rejected','cancelled');
create type public."user_role" as enum('customer','merchant','driver','admin');
create table public."addresses"("id" uuid default gen_random_uuid() not null,"user_id" uuid not null,"label" text default 'home'::text not null,"street" text not null,"details" text,"lat" double precision not null,"lng" double precision not null,"is_default" boolean default false not null,"created_at" timestamp with time zone default now() not null,"house" text,"entrance" text,"floor" text,"apartment" text,"note" text);
create table public."app_pages"("slug" text not null,"body_ru" text default ''::text not null,"body_en" text default ''::text not null,"updated_at" timestamp with time zone default now() not null,"updated_by" uuid);
create table public."app_settings"("key" text not null,"value" numeric not null,"updated_at" timestamp with time zone default now() not null,"updated_by" uuid);
create table public."app_texts"("key" text not null,"value" text default ''::text not null,"updated_at" timestamp with time zone default now() not null,"updated_by" uuid);
create table public."audit_log"("id" bigint generated always as identity not null,"at" timestamp with time zone default now() not null,"user_id" uuid,"action" text not null,"table_name" text not null,"row_id" text,"details" jsonb default '{}'::jsonb not null);
create table public."banners"("id" uuid default gen_random_uuid() not null,"title" text not null,"image_url" text,"link_type" text default 'none'::text not null,"link_value" text,"sort" integer default 0 not null,"is_active" boolean default true not null,"starts_at" timestamp with time zone,"ends_at" timestamp with time zone,"created_at" timestamp with time zone default now() not null,"placement" text default 'top'::text not null);
create table public."brands"("id" uuid default gen_random_uuid() not null,"name" text not null,"owner_id" uuid not null,"created_at" timestamp with time zone default now() not null);
create table public."client_errors"("id" bigint generated always as identity not null,"at" timestamp with time zone default now() not null,"user_id" uuid,"app" text,"message" text,"context" text,"ua" text);
create table public."favorites"("user_id" uuid not null,"store_id" uuid not null,"created_at" timestamp with time zone default now() not null);
create table public."group_items"("id" bigint generated always as identity not null,"group_id" uuid not null,"user_id" uuid not null,"user_name" text not null,"item_id" uuid not null,"qty" integer not null,"options" jsonb default '[]'::jsonb not null,"note" text,"created_at" timestamp with time zone default now() not null);
create table public."group_orders"("id" uuid default gen_random_uuid() not null,"store_id" uuid not null,"host_id" uuid not null,"status" text default 'open'::text not null,"order_id" bigint,"created_at" timestamp with time zone default now() not null,"expires_at" timestamp with time zone default (now() + '03:00:00'::interval) not null,"closed_at" timestamp with time zone);
create table public."happy_hours"("id" bigint generated always as identity not null,"title" text not null,"store_id" uuid,"days" smallint[] default '{1,2,3,4,5,6,7}'::smallint[] not null,"start_time" time without time zone not null,"end_time" time without time zone not null,"discount_pct" integer not null,"active" boolean default true not null,"created_at" timestamp with time zone default now() not null,"created_by" uuid);
create table public."item_option_groups"("id" uuid default gen_random_uuid() not null,"item_id" uuid not null,"name" text not null,"required" boolean default false not null,"max_sel" integer default 1 not null,"sort" integer default 0 not null,"created_at" timestamp with time zone default now() not null);
create table public."item_options"("id" uuid default gen_random_uuid() not null,"group_id" uuid not null,"name" text not null,"price_delta" numeric default 0 not null,"available" boolean default true not null,"sort" integer default 0 not null);
create table public."loyalty_ledger"("id" bigint generated always as identity not null,"user_id" uuid not null,"points" integer not null,"kind" text not null,"order_id" bigint,"created_at" timestamp with time zone default now() not null);
create table public."loyalty_lots"("id" bigint generated always as identity not null,"user_id" uuid not null,"points" integer not null,"points_left" integer not null,"expires_at" timestamp with time zone not null,"order_id" bigint,"kind" text not null,"created_at" timestamp with time zone default now() not null);
create table public."menu_items"("id" uuid default gen_random_uuid() not null,"store_id" uuid not null,"name" text not null,"price" numeric not null,"image_url" text,"popular" boolean default false not null,"available" boolean default true not null,"approved" boolean default true not null,"created_at" timestamp with time zone default now() not null,"section" text,"discount_pct" numeric default 0 not null);
create table public."order_chat"("id" bigint generated always as identity not null,"order_id" bigint not null,"sender_id" uuid not null,"body" text not null,"created_at" timestamp with time zone default now() not null);
create table public."order_customer_phone"("order_id" bigint not null,"phone" text not null);
create table public."order_driver_phone"("order_id" bigint not null,"phone" text not null);
create table public."order_events"("id" bigint generated always as identity not null,"order_id" bigint not null,"kind" text not null,"at" timestamp with time zone default now() not null);
create table public."order_items"("id" uuid default gen_random_uuid() not null,"order_id" bigint not null,"item_id" uuid,"name" text not null,"price" numeric not null,"qty" integer not null,"note" text,"options" jsonb default '[]'::jsonb not null);
create table public."order_offers"("id" bigint generated always as identity not null,"order_id" bigint not null,"driver_id" uuid not null,"state" text default 'pending'::text not null,"mode" text default 'single'::text not null,"rank" integer default 1 not null,"dist_km" numeric,"offered_at" timestamp with time zone default now() not null,"expires_at" timestamp with time zone not null);
create table public."order_recipient"("order_id" bigint not null,"name" text not null,"phone" text not null);
create table public."orders"("id" bigint generated always as identity not null,"store_id" uuid not null,"customer_id" uuid not null,"driver_id" uuid,"customer_name" text,"customer_phone" text,"driver_name" text,"status" order_status default 'pending'::order_status not null,"subtotal" numeric default 0 not null,"discount" numeric default 0 not null,"delivery_fee" numeric default 0 not null,"tip" numeric default 0 not null,"total" numeric default 0 not null,"commission_pct" numeric default 0 not null,"commission" numeric default 0 not null,"driver_payout" numeric default 0 not null,"payment" text,"address" text,"lat" double precision,"lng" double precision,"prep_time" integer default 20 not null,"created_at" timestamp with time zone default now() not null,"done_at" timestamp with time zone,"cash_collected" numeric,"cash_note" text,"cash_settled_at" timestamp with time zone,"promo_code" text,"promo_discount" numeric default 0 not null,"client_key" text,"delivery_base" numeric,"delivery_extra" numeric default 0 not null,"delivery_km" numeric,"wallet_used" numeric default 0 not null,"wallet_returned_at" timestamp with time zone,"hh_discount" numeric default 0 not null,"hh_pct" integer default 0 not null,"points_used" integer default 0 not null,"points_value" numeric default 0 not null,"points_earned" integer default 0 not null,"cashback" numeric default 0 not null,"loyalty_done_at" timestamp with time zone,"points_returned_at" timestamp with time zone,"leave_at_door" boolean default false not null,"substitution" text default 'call'::text not null,"is_gift" boolean default false not null,"fee_waived" numeric default 0 not null,"scheduled_for" timestamp with time zone,"group_id" uuid,"arrived_store_at" timestamp with time zone,"arrived_cust_at" timestamp with time zone,"delivery_photo" text,"cancel_reason" text,"cancel_note" text,"cancelled_by" text);
create table public."profiles"("id" uuid not null,"role" user_role default 'customer'::user_role not null,"name" text,"phone" text,"lang" text default 'ru'::text,"driver_status" text,"cash_limit" numeric default 1000 not null,"created_at" timestamp with time zone default now() not null,"accept_blocked" boolean default false not null,"online" boolean default false not null,"last_seen" timestamp with time zone,"lat" double precision,"lng" double precision,"loc_acc" double precision,"loc_updated" timestamp with time zone,"banned_at" timestamp with time zone,"banned_reason" text,"phone_changed_at" timestamp with time zone);
create table public."promo_attempts"("user_id" uuid not null,"at" timestamp with time zone default now() not null,"ok" boolean default false not null,"code" text);
create table public."promo_codes"("id" uuid default gen_random_uuid() not null,"code" text not null,"kind" text not null,"value" numeric not null,"min_order" numeric default 0 not null,"max_uses" integer,"starts_at" timestamp with time zone,"ends_at" timestamp with time zone,"is_active" boolean default true not null,"created_at" timestamp with time zone default now() not null);
create table public."promo_guess"("id" bigint generated always as identity not null,"user_id" uuid not null,"at" timestamp with time zone default now() not null,"bad" boolean not null);
create table public."ratings"("order_id" bigint not null,"customer_id" uuid not null,"store_id" uuid not null,"driver_id" uuid,"store_stars" smallint,"driver_stars" smallint,"comment" text,"created_at" timestamp with time zone default now() not null,"handled_at" timestamp with time zone,"handled_by" uuid,"handled_note" text);
create table public."staff_members"("user_id" uuid not null,"perms" text[] default '{}'::text[] not null,"active" boolean default true not null,"created_by" uuid,"created_at" timestamp with time zone default now() not null);
create table public."store_requests"("id" uuid default gen_random_uuid() not null,"user_id" uuid not null,"name" text not null,"category" text not null,"phone" text not null,"address" text,"lat" double precision not null,"lng" double precision not null,"note" text,"status" text default 'pending'::text not null,"admin_note" text,"store_id" uuid,"created_at" timestamp with time zone default now() not null,"decided_at" timestamp with time zone,"decided_by" uuid);
create table public."stores"("id" uuid default gen_random_uuid() not null,"owner_id" uuid,"name" text not null,"category" text not null,"description" text,"logo_url" text,"cover_url" text,"address" text,"lat" double precision,"lng" double precision,"commission_pct" numeric default 10 not null,"fee_type" text default 'fixed'::text not null,"fee_base" numeric default 10 not null,"fee_per_km" numeric default 0 not null,"fee_free_km" numeric default 3 not null,"discount_pct" numeric default 0 not null,"is_open" boolean default true not null,"is_active" boolean default true not null,"is_featured" boolean default false not null,"created_at" timestamp with time zone default now() not null,"phone" text,"max_discount_pct" numeric default 30 not null,"free_first_delivery" boolean default false not null,"google_place_id" text,"rating" numeric(2,1),"rating_count" integer,"rating_updated_at" timestamp with time zone,"app_rating" numeric(2,1),"app_rating_count" integer default 0 not null,"brand_id" uuid,"branch_name" text,"points_min_order" numeric,"cashback_pct" numeric,"free_delivery_min" numeric default 0 not null,"earn_per_tjs" numeric);
create table public."support_tickets"("id" bigint generated always as identity not null,"customer_id" uuid not null,"order_id" bigint,"reason" text not null,"status" text default 'open'::text not null,"refund_amount" numeric,"admin_note" text,"created_at" timestamp with time zone default now() not null,"updated_at" timestamp with time zone default now() not null,"last_customer_at" timestamp with time zone default now() not null,"last_staff_at" timestamp with time zone,"customer_seen_at" timestamp with time zone,"closed_at" timestamp with time zone,"handled_by" uuid);
create table public."ticket_messages"("id" bigint generated always as identity not null,"ticket_id" bigint not null,"from_staff" boolean default false not null,"sender_id" uuid not null,"body" text not null,"created_at" timestamp with time zone default now() not null);
create table public."wallet_entries"("id" bigint generated always as identity not null,"user_id" uuid not null,"amount" numeric(12,2) not null,"kind" text not null,"order_id" bigint,"ticket_id" bigint,"note" text,"created_by" uuid,"created_at" timestamp with time zone default now() not null);
alter table "promo_guess" add constraint "promo_guess_pkey" PRIMARY KEY (id);
alter table "loyalty_lots" add constraint "loyalty_lots_kind_check" CHECK ((kind = ANY (ARRAY['earn'::text, 'return'::text, 'reward'::text])));
alter table "loyalty_lots" add constraint "loyalty_lots_pkey" PRIMARY KEY (id);
alter table "loyalty_lots" add constraint "loyalty_lots_points_check" CHECK ((points > 0));
alter table "loyalty_lots" add constraint "loyalty_lots_points_left_check" CHECK ((points_left >= 0));
alter table "loyalty_ledger" add constraint "loyalty_ledger_kind_check" CHECK ((kind = ANY (ARRAY['earn'::text, 'spend'::text, 'return'::text, 'reward'::text])));
alter table "loyalty_ledger" add constraint "loyalty_ledger_pkey" PRIMARY KEY (id);
alter table "loyalty_ledger" add constraint "loyalty_ledger_points_check" CHECK ((points <> 0));
alter table "happy_hours" add constraint "happy_hours_check" CHECK ((end_time <> start_time));
alter table "happy_hours" add constraint "happy_hours_days_check" CHECK ((((array_length(days, 1) >= 1) AND (array_length(days, 1) <= 7)) AND (days <@ '{1,2,3,4,5,6,7}'::smallint[])));
alter table "happy_hours" add constraint "happy_hours_discount_pct_check" CHECK (((discount_pct >= 1) AND (discount_pct <= 90)));
alter table "happy_hours" add constraint "happy_hours_pkey" PRIMARY KEY (id);
alter table "happy_hours" add constraint "happy_hours_title_check" CHECK (((char_length(btrim(title)) >= 1) AND (char_length(btrim(title)) <= 60)));
alter table "brands" add constraint "brands_name_check" CHECK (((char_length(btrim(name)) >= 2) AND (char_length(btrim(name)) <= 60)));
alter table "brands" add constraint "brands_pkey" PRIMARY KEY (id);
alter table "item_option_groups" add constraint "item_option_groups_max_sel_check" CHECK (((max_sel >= 1) AND (max_sel <= 20)));
alter table "item_option_groups" add constraint "item_option_groups_name_check" CHECK (((char_length(btrim(name)) >= 1) AND (char_length(btrim(name)) <= 60)));
alter table "item_option_groups" add constraint "item_option_groups_pkey" PRIMARY KEY (id);
alter table "item_options" add constraint "item_options_name_check" CHECK (((char_length(btrim(name)) >= 1) AND (char_length(btrim(name)) <= 60)));
alter table "item_options" add constraint "item_options_pkey" PRIMARY KEY (id);
alter table "item_options" add constraint "item_options_price_delta_check" CHECK (((price_delta >= (0)::numeric) AND (price_delta <= (100000)::numeric)));
alter table "orders" add constraint "orders_cancel_note_check" CHECK (((cancel_note IS NULL) OR (char_length(cancel_note) <= 200)));
alter table "orders" add constraint "orders_cancel_reason_check" CHECK (((cancel_reason IS NULL) OR (cancel_reason = ANY (ARRAY['out_of_stock'::text, 'too_busy'::text, 'closing'::text, 'other'::text]))));
alter table "orders" add constraint "orders_cancelled_by_check" CHECK (((cancelled_by IS NULL) OR (cancelled_by = ANY (ARRAY['store'::text, 'customer'::text, 'staff'::text]))));
alter table "orders" add constraint "orders_delivery_photo_check" CHECK (((delivery_photo IS NULL) OR (char_length(delivery_photo) <= 300)));
alter table "orders" add constraint "orders_fee_waived_check" CHECK ((fee_waived >= (0)::numeric));
alter table "orders" add constraint "orders_hh_discount_check" CHECK ((hh_discount >= (0)::numeric));
alter table "orders" add constraint "orders_pkey" PRIMARY KEY (id);
alter table "orders" add constraint "orders_points_used_check" CHECK ((points_used >= 0));
alter table "orders" add constraint "orders_points_value_check" CHECK ((points_value >= (0)::numeric));
alter table "orders" add constraint "orders_substitution_check" CHECK ((substitution = ANY (ARRAY['call'::text, 'replace'::text, 'remove'::text])));
alter table "orders" add constraint "orders_wallet_used_check" CHECK ((wallet_used >= (0)::numeric));
alter table "order_chat" add constraint "order_chat_body_check" CHECK ((length(body) <= 200));
alter table "order_chat" add constraint "order_chat_pkey" PRIMARY KEY (id);
alter table "order_recipient" add constraint "order_recipient_name_check" CHECK (((char_length(name) >= 2) AND (char_length(name) <= 60)));
alter table "order_recipient" add constraint "order_recipient_phone_check" CHECK ((char_length(phone) <= 20));
alter table "order_recipient" add constraint "order_recipient_pkey" PRIMARY KEY (order_id);
alter table "profiles" add constraint "profiles_driver_status_check" CHECK ((driver_status = ANY (ARRAY['pending'::text, 'approved'::text, 'suspended'::text])));
alter table "profiles" add constraint "profiles_loc_chk" CHECK ((((lat IS NULL) OR ((lat >= ('-90'::integer)::double precision) AND (lat <= (90)::double precision))) AND ((lng IS NULL) OR ((lng >= ('-180'::integer)::double precision) AND (lng <= (180)::double precision))))) NOT VALID;
alter table "profiles" add constraint "profiles_pkey" PRIMARY KEY (id);
alter table "order_items" add constraint "order_items_options_chk" CHECK (((jsonb_typeof(options) = 'array'::text) AND (jsonb_array_length(options) <= 40))) NOT VALID;
alter table "order_items" add constraint "order_items_pkey" PRIMARY KEY (id);
alter table "order_items" add constraint "order_items_qty_check" CHECK (((qty >= 1) AND (qty <= 50)));
alter table "menu_items" add constraint "menu_items_discount_chk" CHECK (((discount_pct >= (0)::numeric) AND (discount_pct <= (100)::numeric)));
alter table "menu_items" add constraint "menu_items_image_len" CHECK (((image_url IS NULL) OR (char_length(image_url) <= 700000))) NOT VALID;
alter table "menu_items" add constraint "menu_items_name_len" CHECK ((char_length(name) <= 80)) NOT VALID;
alter table "menu_items" add constraint "menu_items_pkey" PRIMARY KEY (id);
alter table "menu_items" add constraint "menu_items_price_check" CHECK ((price >= (0)::numeric));
alter table "menu_items" add constraint "menu_items_section_chk" CHECK (((section IS NULL) OR ((char_length(btrim(section)) >= 1) AND (char_length(btrim(section)) <= 40))));
alter table "banners" add constraint "banners_dates_chk" CHECK (((starts_at IS NULL) OR (ends_at IS NULL) OR (ends_at > starts_at)));
alter table "banners" add constraint "banners_image_len" CHECK (((image_url IS NULL) OR (char_length(image_url) <= 900000))) NOT VALID;
alter table "banners" add constraint "banners_link_type_check" CHECK ((link_type = ANY (ARRAY['none'::text, 'store'::text, 'category'::text])));
alter table "banners" add constraint "banners_pkey" PRIMARY KEY (id);
alter table "banners" add constraint "banners_placement_chk" CHECK ((placement = ANY (ARRAY['top'::text, 'bottom'::text])));
alter table "banners" add constraint "banners_text_len" CHECK (((char_length(title) <= 80) AND ((link_value IS NULL) OR (char_length(link_value) <= 80)))) NOT VALID;
alter table "promo_codes" add constraint "promo_codes_check" CHECK (((kind <> 'percent'::text) OR (value <= (100)::numeric)));
alter table "promo_codes" add constraint "promo_codes_check1" CHECK (((starts_at IS NULL) OR (ends_at IS NULL) OR (ends_at > starts_at)));
alter table "promo_codes" add constraint "promo_codes_code_check" CHECK ((code ~ '^[A-Za-z0-9_-]{3,20}$'::text));
alter table "promo_codes" add constraint "promo_codes_kind_check" CHECK ((kind = ANY (ARRAY['percent'::text, 'fixed'::text])));
alter table "promo_codes" add constraint "promo_codes_max_uses_check" CHECK (((max_uses IS NULL) OR (max_uses > 0)));
alter table "promo_codes" add constraint "promo_codes_min_order_check" CHECK ((min_order >= (0)::numeric));
alter table "promo_codes" add constraint "promo_codes_pkey" PRIMARY KEY (id);
alter table "promo_codes" add constraint "promo_codes_value_check" CHECK ((value > (0)::numeric));
alter table "favorites" add constraint "favorites_pkey" PRIMARY KEY (user_id, store_id);
alter table "order_events" add constraint "order_events_pkey" PRIMARY KEY (id);
alter table "group_orders" add constraint "group_orders_pkey" PRIMARY KEY (id);
alter table "group_orders" add constraint "group_orders_status_check" CHECK ((status = ANY (ARRAY['open'::text, 'closed'::text, 'placed'::text, 'cancelled'::text])));
alter table "group_items" add constraint "group_items_note_check" CHECK (((note IS NULL) OR (char_length(note) <= 120)));
alter table "group_items" add constraint "group_items_pkey" PRIMARY KEY (id);
alter table "group_items" add constraint "group_items_qty_check" CHECK (((qty >= 1) AND (qty <= 20)));
alter table "ratings" add constraint "ratings_check" CHECK (((store_stars IS NOT NULL) OR (driver_stars IS NOT NULL)));
alter table "ratings" add constraint "ratings_comment_check" CHECK (((comment IS NULL) OR (char_length(comment) <= 300)));
alter table "ratings" add constraint "ratings_driver_stars_check" CHECK (((driver_stars >= 1) AND (driver_stars <= 5)));
alter table "ratings" add constraint "ratings_note_chk" CHECK (((handled_note IS NULL) OR (char_length(handled_note) <= 300)));
alter table "ratings" add constraint "ratings_pkey" PRIMARY KEY (order_id);
alter table "ratings" add constraint "ratings_store_stars_check" CHECK (((store_stars >= 1) AND (store_stars <= 5)));
alter table "order_offers" add constraint "order_offers_mode_check" CHECK ((mode = ANY (ARRAY['single'::text, 'broadcast'::text])));
alter table "order_offers" add constraint "order_offers_order_id_driver_id_key" UNIQUE (order_id, driver_id);
alter table "order_offers" add constraint "order_offers_pkey" PRIMARY KEY (id);
alter table "order_offers" add constraint "order_offers_state_check" CHECK ((state = ANY (ARRAY['pending'::text, 'declined'::text, 'expired'::text, 'accepted'::text, 'cancelled'::text])));
alter table "audit_log" add constraint "audit_log_pkey" PRIMARY KEY (id);
alter table "client_errors" add constraint "client_errors_pkey" PRIMARY KEY (id);
alter table "order_customer_phone" add constraint "order_customer_phone_pkey" PRIMARY KEY (order_id);
alter table "order_driver_phone" add constraint "order_driver_phone_pkey" PRIMARY KEY (order_id);
alter table "addresses" add constraint "addresses_details_check" CHECK (((details IS NULL) OR (char_length(details) <= 120)));
alter table "addresses" add constraint "addresses_label_check" CHECK ((label = ANY (ARRAY['home'::text, 'work'::text, 'other'::text])));
alter table "addresses" add constraint "addresses_lat_check" CHECK (((lat >= ('-90'::integer)::double precision) AND (lat <= (90)::double precision)));
alter table "addresses" add constraint "addresses_lng_check" CHECK (((lng >= ('-180'::integer)::double precision) AND (lng <= (180)::double precision)));
alter table "addresses" add constraint "addresses_parts_chk" CHECK ((((house IS NULL) OR ((char_length(btrim(house)) >= 1) AND (char_length(btrim(house)) <= 20))) AND ((entrance IS NULL) OR (char_length(entrance) <= 10)) AND ((floor IS NULL) OR (char_length(floor) <= 10)) AND ((apartment IS NULL) OR (char_length(apartment) <= 10)) AND ((note IS NULL) OR (char_length(note) <= 120)))) NOT VALID;
alter table "addresses" add constraint "addresses_pkey" PRIMARY KEY (id);
alter table "addresses" add constraint "addresses_street_check" CHECK (((char_length(btrim(street)) >= 3) AND (char_length(btrim(street)) <= 120)));
alter table "app_settings" add constraint "app_settings_key_check" CHECK ((key = ANY (ARRAY['delivery_free_km'::text, 'delivery_step_km'::text, 'delivery_step_price'::text, 'delivery_max_km'::text, 'delivery_road_factor'::text, 'loyalty_earn_per_tjs'::text, 'loyalty_points_per_tjs'::text, 'loyalty_min_redeem'::text, 'loyalty_expiry_days'::text, 'cashback_pct'::text, 'loyalty_voucher_points'::text, 'loyalty_min_order'::text, 'loyalty_rate_reward'::text])));
alter table "app_settings" add constraint "app_settings_pkey" PRIMARY KEY (key);
alter table "stores" add constraint "stores_branch_name_len" CHECK (((branch_name IS NULL) OR ((char_length(btrim(branch_name)) >= 1) AND (char_length(btrim(branch_name)) <= 40))));
alter table "stores" add constraint "stores_cashback_pct_check" CHECK (((cashback_pct IS NULL) OR ((cashback_pct >= (0)::numeric) AND (cashback_pct <= (50)::numeric))));
alter table "stores" add constraint "stores_category_check" CHECK ((category = ANY (ARRAY['rest'::text, 'grocery'::text, 'pharmacy'::text, 'beauty'::text, 'flowers'::text, 'gifts'::text, 'shops'::text, 'sweets'::text])));
alter table "stores" add constraint "stores_commission_pct_check" CHECK (((commission_pct >= (0)::numeric) AND (commission_pct <= (50)::numeric)));
alter table "stores" add constraint "stores_earn_per_tjs_check" CHECK (((earn_per_tjs IS NULL) OR (((earn_per_tjs >= (0)::numeric) AND (earn_per_tjs <= (1000)::numeric)) AND (earn_per_tjs = trunc(earn_per_tjs)))));
alter table "stores" add constraint "stores_fee_type_check" CHECK ((fee_type = ANY (ARRAY['fixed'::text, 'distance'::text, 'free'::text])));
alter table "stores" add constraint "stores_free_delivery_min_check" CHECK (((free_delivery_min >= (0)::numeric) AND (free_delivery_min <= (100000)::numeric)));
alter table "stores" add constraint "stores_images_len" CHECK ((((cover_url IS NULL) OR (char_length(cover_url) <= 700000)) AND ((logo_url IS NULL) OR (char_length(logo_url) <= 700000)))) NOT VALID;
alter table "stores" add constraint "stores_pkey" PRIMARY KEY (id);
alter table "stores" add constraint "stores_points_min_order_check" CHECK (((points_min_order IS NULL) OR ((points_min_order >= (0)::numeric) AND (points_min_order <= (10000)::numeric))));
alter table "stores" add constraint "stores_rating_chk" CHECK ((((rating IS NULL) OR ((rating >= (0)::numeric) AND (rating <= (5)::numeric))) AND ((rating_count IS NULL) OR (rating_count >= 0)) AND ((google_place_id IS NULL) OR (google_place_id ~ '^[A-Za-z0-9_-]{10,200}$'::text))));
alter table "stores" add constraint "stores_text_len" CHECK (((char_length(name) <= 80) AND ((description IS NULL) OR (char_length(description) <= 500)) AND ((address IS NULL) OR (char_length(address) <= 200)) AND ((phone IS NULL) OR (char_length(phone) <= 20)))) NOT VALID;
alter table "app_texts" add constraint "app_texts_key_check" CHECK ((key = ANY (ARRAY['support_phone'::text, 'support_hours'::text])));
alter table "app_texts" add constraint "app_texts_pkey" PRIMARY KEY (key);
alter table "app_texts" add constraint "app_texts_value_check" CHECK ((char_length(value) <= 60));
alter table "support_tickets" add constraint "support_tickets_admin_note_check" CHECK (((admin_note IS NULL) OR (char_length(admin_note) <= 300)));
alter table "support_tickets" add constraint "support_tickets_pkey" PRIMARY KEY (id);
alter table "support_tickets" add constraint "support_tickets_reason_check" CHECK ((reason = ANY (ARRAY['not_delivered'::text, 'wrong_order'::text, 'missing_items'::text, 'quality'::text, 'late'::text, 'courier'::text, 'restaurant'::text, 'payment'::text, 'other'::text])));
alter table "support_tickets" add constraint "support_tickets_refund_amount_check" CHECK (((refund_amount IS NULL) OR ((refund_amount >= (0)::numeric) AND (refund_amount <= (100000)::numeric))));
alter table "support_tickets" add constraint "support_tickets_status_check" CHECK ((status = ANY (ARRAY['open'::text, 'in_progress'::text, 'resolved'::text, 'rejected'::text])));
alter table "ticket_messages" add constraint "ticket_messages_body_check" CHECK (((char_length(btrim(body)) >= 1) AND (char_length(btrim(body)) <= 500)));
alter table "ticket_messages" add constraint "ticket_messages_pkey" PRIMARY KEY (id);
alter table "app_pages" add constraint "app_pages_body_en_check" CHECK ((char_length(body_en) <= 20000));
alter table "app_pages" add constraint "app_pages_body_ru_check" CHECK ((char_length(body_ru) <= 20000));
alter table "app_pages" add constraint "app_pages_pkey" PRIMARY KEY (slug);
alter table "app_pages" add constraint "app_pages_slug_check" CHECK ((slug = ANY (ARRAY['about'::text, 'privacy'::text])));
alter table "store_requests" add constraint "store_requests_address_check" CHECK (((address IS NULL) OR (char_length(address) <= 200)));
alter table "store_requests" add constraint "store_requests_admin_note_check" CHECK (((admin_note IS NULL) OR (char_length(admin_note) <= 300)));
alter table "store_requests" add constraint "store_requests_category_check" CHECK ((category = ANY (ARRAY['rest'::text, 'grocery'::text, 'pharmacy'::text, 'beauty'::text, 'flowers'::text, 'gifts'::text, 'shops'::text, 'sweets'::text])));
alter table "store_requests" add constraint "store_requests_lat_check" CHECK (((lat >= ('-90'::integer)::double precision) AND (lat <= (90)::double precision)));
alter table "store_requests" add constraint "store_requests_lng_check" CHECK (((lng >= ('-180'::integer)::double precision) AND (lng <= (180)::double precision)));
alter table "store_requests" add constraint "store_requests_name_check" CHECK (((char_length(btrim(name)) >= 2) AND (char_length(btrim(name)) <= 80)));
alter table "store_requests" add constraint "store_requests_note_check" CHECK (((note IS NULL) OR (char_length(note) <= 500)));
alter table "store_requests" add constraint "store_requests_phone_check" CHECK ((phone ~ '^\+992[0-9]{9}$'::text));
alter table "store_requests" add constraint "store_requests_pkey" PRIMARY KEY (id);
alter table "store_requests" add constraint "store_requests_status_check" CHECK ((status = ANY (ARRAY['pending'::text, 'approved'::text, 'rejected'::text])));
alter table "wallet_entries" add constraint "wallet_entries_amount_check" CHECK ((amount <> (0)::numeric));
alter table "wallet_entries" add constraint "wallet_entries_kind_check" CHECK ((kind = ANY (ARRAY['refund'::text, 'spend'::text, 'return'::text, 'adjust'::text, 'cashback'::text])));
alter table "wallet_entries" add constraint "wallet_entries_note_check" CHECK (((note IS NULL) OR (char_length(note) <= 200)));
alter table "wallet_entries" add constraint "wallet_entries_pkey" PRIMARY KEY (id);
alter table "staff_members" add constraint "staff_members_pkey" PRIMARY KEY (user_id);
alter table "staff_members" add constraint "staff_perms_valid" CHECK ((perms <@ ARRAY['orders'::text, 'support'::text, 'finance'::text, 'stores'::text, 'content'::text]));
alter table "loyalty_lots" add constraint "loyalty_lots_order_id_fkey" FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE SET NULL;
alter table "loyalty_lots" add constraint "loyalty_lots_user_id_fkey" FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE;
alter table "loyalty_ledger" add constraint "loyalty_ledger_order_id_fkey" FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE SET NULL;
alter table "loyalty_ledger" add constraint "loyalty_ledger_user_id_fkey" FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE;
alter table "happy_hours" add constraint "happy_hours_store_id_fkey" FOREIGN KEY (store_id) REFERENCES stores(id) ON DELETE CASCADE;
alter table "brands" add constraint "brands_owner_id_fkey" FOREIGN KEY (owner_id) REFERENCES profiles(id);
alter table "item_option_groups" add constraint "item_option_groups_item_id_fkey" FOREIGN KEY (item_id) REFERENCES menu_items(id) ON DELETE CASCADE;
alter table "item_options" add constraint "item_options_group_id_fkey" FOREIGN KEY (group_id) REFERENCES item_option_groups(id) ON DELETE CASCADE;
alter table "orders" add constraint "orders_customer_id_fkey" FOREIGN KEY (customer_id) REFERENCES profiles(id);
alter table "orders" add constraint "orders_driver_id_fkey" FOREIGN KEY (driver_id) REFERENCES profiles(id);
alter table "orders" add constraint "orders_group_id_fkey" FOREIGN KEY (group_id) REFERENCES group_orders(id) ON DELETE SET NULL;
alter table "orders" add constraint "orders_store_id_fkey" FOREIGN KEY (store_id) REFERENCES stores(id);
alter table "order_chat" add constraint "order_chat_order_id_fkey" FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE;
alter table "order_chat" add constraint "order_chat_sender_id_fkey" FOREIGN KEY (sender_id) REFERENCES profiles(id);
alter table "order_recipient" add constraint "order_recipient_order_id_fkey" FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE;
alter table "profiles" add constraint "profiles_id_fkey" FOREIGN KEY (id) REFERENCES auth.users(id) ON DELETE CASCADE;
alter table "order_items" add constraint "order_items_order_id_fkey" FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE;
alter table "menu_items" add constraint "menu_items_store_id_fkey" FOREIGN KEY (store_id) REFERENCES stores(id) ON DELETE CASCADE;
alter table "favorites" add constraint "favorites_store_id_fkey" FOREIGN KEY (store_id) REFERENCES stores(id) ON DELETE CASCADE;
alter table "favorites" add constraint "favorites_user_id_fkey" FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE;
alter table "order_events" add constraint "order_events_order_id_fkey" FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE;
alter table "group_orders" add constraint "group_orders_host_id_fkey" FOREIGN KEY (host_id) REFERENCES profiles(id) ON DELETE CASCADE;
alter table "group_orders" add constraint "group_orders_order_id_fkey" FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE SET NULL;
alter table "group_orders" add constraint "group_orders_store_id_fkey" FOREIGN KEY (store_id) REFERENCES stores(id) ON DELETE CASCADE;
alter table "group_items" add constraint "group_items_group_id_fkey" FOREIGN KEY (group_id) REFERENCES group_orders(id) ON DELETE CASCADE;
alter table "group_items" add constraint "group_items_item_id_fkey" FOREIGN KEY (item_id) REFERENCES menu_items(id) ON DELETE CASCADE;
alter table "group_items" add constraint "group_items_user_id_fkey" FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE;
alter table "ratings" add constraint "ratings_customer_id_fkey" FOREIGN KEY (customer_id) REFERENCES profiles(id);
alter table "ratings" add constraint "ratings_driver_id_fkey" FOREIGN KEY (driver_id) REFERENCES profiles(id);
alter table "ratings" add constraint "ratings_handled_by_fkey" FOREIGN KEY (handled_by) REFERENCES profiles(id);
alter table "ratings" add constraint "ratings_order_id_fkey" FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE;
alter table "ratings" add constraint "ratings_store_id_fkey" FOREIGN KEY (store_id) REFERENCES stores(id);
alter table "order_offers" add constraint "order_offers_driver_id_fkey" FOREIGN KEY (driver_id) REFERENCES profiles(id) ON DELETE CASCADE;
alter table "order_offers" add constraint "order_offers_order_id_fkey" FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE;
alter table "order_customer_phone" add constraint "order_customer_phone_order_id_fkey" FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE;
alter table "order_driver_phone" add constraint "order_driver_phone_order_id_fkey" FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE;
alter table "addresses" add constraint "addresses_user_id_fkey" FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE;
alter table "stores" add constraint "stores_brand_id_fkey" FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE SET NULL;
alter table "stores" add constraint "stores_owner_id_fkey" FOREIGN KEY (owner_id) REFERENCES profiles(id);
alter table "support_tickets" add constraint "support_tickets_customer_id_fkey" FOREIGN KEY (customer_id) REFERENCES profiles(id) ON DELETE CASCADE;
alter table "support_tickets" add constraint "support_tickets_handled_by_fkey" FOREIGN KEY (handled_by) REFERENCES profiles(id);
alter table "support_tickets" add constraint "support_tickets_order_id_fkey" FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE SET NULL;
alter table "ticket_messages" add constraint "ticket_messages_sender_id_fkey" FOREIGN KEY (sender_id) REFERENCES profiles(id);
alter table "ticket_messages" add constraint "ticket_messages_ticket_id_fkey" FOREIGN KEY (ticket_id) REFERENCES support_tickets(id) ON DELETE CASCADE;
alter table "store_requests" add constraint "store_requests_decided_by_fkey" FOREIGN KEY (decided_by) REFERENCES profiles(id);
alter table "store_requests" add constraint "store_requests_store_id_fkey" FOREIGN KEY (store_id) REFERENCES stores(id) ON DELETE SET NULL;
alter table "store_requests" add constraint "store_requests_user_id_fkey" FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE;
alter table "wallet_entries" add constraint "wallet_entries_order_id_fkey" FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE SET NULL;
alter table "wallet_entries" add constraint "wallet_entries_ticket_id_fkey" FOREIGN KEY (ticket_id) REFERENCES support_tickets(id) ON DELETE SET NULL;
alter table "wallet_entries" add constraint "wallet_entries_user_id_fkey" FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE;
alter table "staff_members" add constraint "staff_members_created_by_fkey" FOREIGN KEY (created_by) REFERENCES profiles(id);
alter table "staff_members" add constraint "staff_members_user_id_fkey" FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE;
CREATE OR REPLACE FUNCTION public.active_contacts()
 RETURNS TABLE(order_id bigint, customer_phone text, driver_phone text)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  select o.id,
         case when o.driver_id = auth.uid() then cp.phone end,
         case when o.driver_id is not null and (o.customer_id = auth.uid() or owns_store(o.store_id)) then dp.phone end
    from orders o
    left join order_customer_phone cp on cp.order_id = o.id
    left join order_driver_phone dp on dp.order_id = o.id
   where o.status in ('preparing', 'ready', 'pickedup')
     and (o.driver_id = auth.uid() or o.customer_id = auth.uid() or owns_store(o.store_id))
$function$
;
CREATE OR REPLACE FUNCTION public.addr_after_delete()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if old.is_default then
    update addresses set is_default = true
     where id = (select a.id from addresses a where a.user_id = old.user_id order by a.created_at desc limit 1);
  end if;
  return old;
end $function$
;
CREATE OR REPLACE FUNCTION public.addr_before_insert()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if (select count(*) from addresses where user_id = new.user_id) >= 10 then raise exception 'bad_value'; end if;
  if not exists (select 1 from addresses where user_id = new.user_id) then new.is_default := true; end if;
  if new.is_default then update addresses set is_default = false where user_id = new.user_id and is_default; end if;
  return new;
end $function$
;
CREATE OR REPLACE FUNCTION public.admin_assign_driver(p_order bigint, p_driver uuid)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_name text; v_phone text;
begin
  if not has_perm('orders') then raise exception 'not_allowed'; end if;
  select name, phone into v_name, v_phone from profiles where id = p_driver and role = 'driver' and driver_status = 'approved';
  if not found then raise exception 'not_approved'; end if;
  if norm_phone(v_phone) is null then raise exception 'phone_required'; end if;
  update orders set driver_id = p_driver, driver_name = v_name
   where id = p_order and driver_id is null and status in ('preparing', 'ready');
  if not found then raise exception 'bad_transition'; end if;
  update order_offers set state = case when driver_id = p_driver then 'accepted' else 'cancelled' end
   where order_id = p_order and state = 'pending';
  insert into order_driver_phone(order_id, phone) values (p_order, norm_phone(v_phone))
    on conflict (order_id) do update set phone = excluded.phone;
end $function$
;
CREATE OR REPLACE FUNCTION public.admin_customers(p_q text DEFAULT NULL::text, p_limit integer DEFAULT 30, p_offset integer DEFAULT 0)
 RETURNS TABLE(id uuid, name text, phone text, email text, created_at timestamp with time zone, orders_count bigint, total_spent numeric, last_order_at timestamp with time zone, banned_at timestamp with time zone, banned_reason text)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  select p.id, p.name, p.phone, u.email::text, p.created_at, coalesce(o.cnt, 0), coalesce(o.spent, 0), o.last_at, p.banned_at, p.banned_reason
    from profiles p
    left join auth.users u on u.id = p.id
    left join lateral (select count(*) filter (where x.status = 'delivered') as cnt,
                              coalesce(sum(x.total) filter (where x.status = 'delivered'), 0) as spent,
                              max(x.created_at) as last_at
                         from orders x where x.customer_id = p.id) o on true
   where has_perm('support') and p.role = 'customer'
     and (coalesce(btrim(p_q), '') = '' or p.name ilike '%' || btrim(p_q) || '%' or p.phone ilike '%' || btrim(p_q) || '%' or u.email ilike '%' || btrim(p_q) || '%')
   order by p.created_at desc
   limit least(greatest(coalesce(p_limit, 30), 1), 50) offset greatest(coalesce(p_offset, 0), 0)
$function$
;
CREATE OR REPLACE FUNCTION public.admin_set_customer_phone(p_user uuid, p_phone text, p_reason text)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_p text := norm_phone(p_phone); v_why text := btrim(coalesce(p_reason, ''));
begin
  if not is_admin() then raise exception 'not_allowed'; end if;
  if v_p is null then raise exception 'bad_phone'; end if;
  if char_length(v_why) < 3 or char_length(v_why) > 200 then raise exception 'note_required'; end if;
  perform 1 from profiles where id = p_user and role = 'customer' for update;
  if not found then raise exception 'not_found'; end if;
  update profiles set phone = v_p where id = p_user;      -- the trigger lets the admin through and logs the change (from / to)
  insert into audit_log(user_id, action, table_name, row_id, details)
  values (auth.uid(), 'ADMIN_SET_PHONE', 'profiles', p_user::text, jsonb_build_object('reason', v_why));
end $function$
;
CREATE OR REPLACE FUNCTION public.apply_as_driver()
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  perform set_config('app.bypass', '1', true);
  update profiles set role = 'driver', driver_status = 'pending' where id = auth.uid() and role = 'customer';
end $function$
;
CREATE OR REPLACE FUNCTION public.assign_owner(p_store uuid, p_email text)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare u uuid;
begin
  if not is_admin() then raise exception 'not_allowed'; end if;
  select id into u from auth.users where lower(email) = lower(p_email);
  if u is null then raise exception 'user_not_found'; end if;
  perform set_config('app.bypass', '1', true);
  update profiles set role = 'merchant' where id = u and role = 'customer';
  update stores set owner_id = u where id = p_store;
end $function$
;
CREATE OR REPLACE FUNCTION public.audit_changes()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_n jsonb; v_o jsonb; v_d jsonb := '{}'::jsonb; v_k text; v_id text;
begin
  if tg_op = 'INSERT' then v_n := to_jsonb(new); v_id := v_n->>coalesce(tg_argv[0], 'id');
    insert into audit_log(user_id, action, table_name, row_id, details) values (auth.uid(), 'INSERT', tg_table_name, v_id, '{}'::jsonb);
    return new;
  elsif tg_op = 'DELETE' then v_o := to_jsonb(old); v_id := v_o->>coalesce(tg_argv[0], 'id');
    insert into audit_log(user_id, action, table_name, row_id, details) values (auth.uid(), 'DELETE', tg_table_name, v_id, '{}'::jsonb);
    return old;
  end if;
  v_n := to_jsonb(new); v_o := to_jsonb(old); v_id := v_n->>coalesce(tg_argv[0], 'id');
  foreach v_k in array tg_argv[1:] loop
    if (v_n->v_k) is distinct from (v_o->v_k) then v_d := v_d || jsonb_build_object(v_k, jsonb_build_object('from', v_o->v_k, 'to', v_n->v_k)); end if;
  end loop;
  if v_d <> '{}'::jsonb then
    insert into audit_log(user_id, action, table_name, row_id, details) values (auth.uid(), 'UPDATE', tg_table_name, v_id, v_d);
  end if;
  return new;
end $function$
;
CREATE OR REPLACE FUNCTION public.best_dishes(p_store uuid DEFAULT NULL::uuid, p_limit integer DEFAULT 20)
 RETURNS TABLE(item_id uuid, store_id uuid, cnt bigint)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  select oi.item_id, o.store_id, sum(oi.qty)::bigint as cnt
    from order_items oi join orders o on o.id = oi.order_id
    join menu_items m on m.id = oi.item_id and m.available and m.approved
    join stores s on s.id = o.store_id and s.is_active
   where o.status = 'delivered' and o.created_at > now() - interval '30 days' and (p_store is null or o.store_id = p_store)
   group by oi.item_id, o.store_id
  having sum(oi.qty) >= 3
   order by cnt desc
   limit least(greatest(coalesce(p_limit, 20), 1), 50)
$function$
;
CREATE OR REPLACE FUNCTION public.branch_create(p_brand uuid, p_branch text, p_address text, p_lat double precision, p_lng double precision, p_phone text)
 RETURNS uuid
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare b brands; t stores; v_id uuid := gen_random_uuid(); v_br text := btrim(coalesce(p_branch, '')); v_name text; v_ph text := norm_phone(p_phone); v_addr text := nullif(btrim(coalesce(p_address, '')), '');
begin
  select * into b from brands where id = p_brand;
  if not found then raise exception 'not_found'; end if;
  if not (b.owner_id = auth.uid() or is_admin()) then raise exception 'not_allowed'; end if;
  if char_length(v_br) < 1 or char_length(v_br) > 40 then raise exception 'bad_value'; end if;
  if v_addr is not null and char_length(v_addr) > 200 then raise exception 'bad_value'; end if;
  if p_lat is null or p_lng is null or p_lat not between -90 and 90 or p_lng not between -180 and 180 then raise exception 'bad_value'; end if;
  if v_ph is null then raise exception 'bad_phone'; end if;
  v_name := b.name || ' · ' || v_br;
  if char_length(v_name) > 80 then raise exception 'bad_value'; end if;
  if exists(select 1 from stores where lower(name) = lower(v_name)) then raise exception 'name_taken'; end if;
  if (select count(*) from stores where brand_id = p_brand) >= 25 then raise exception 'too_many'; end if;
  if (select count(*) from stores where brand_id = p_brand and created_at > now() - interval '1 day') >= 5 then raise exception 'too_many'; end if;
  select * into t from stores where brand_id = p_brand order by created_at limit 1;
  if not found then raise exception 'no_template'; end if;   -- attach at least one existing store first

  insert into stores(id, owner_id, name, category, description, logo_url, cover_url, address, lat, lng, commission_pct, fee_type, fee_base, fee_per_km, fee_free_km,
                     discount_pct, max_discount_pct, free_first_delivery, is_open, is_active, is_featured, phone, brand_id, branch_name)
  values (v_id, b.owner_id, v_name, t.category, t.description, t.logo_url, t.cover_url, v_addr, p_lat, p_lng, t.commission_pct, t.fee_type, t.fee_base, t.fee_per_km, t.fee_free_km,
          t.discount_pct, t.max_discount_pct, t.free_first_delivery, false, true, false, v_ph, p_brand, v_br);

  perform copy_menu(t.id, v_id, false);
  insert into audit_log(user_id, action, table_name, row_id, details) values (auth.uid(), 'BRANCH_CREATE', 'stores', v_id::text, jsonb_build_object('brand', p_brand, 'name', v_name, 'from', t.id));
  return v_id;
end $function$
;
CREATE OR REPLACE FUNCTION public.brand_attach(p_store uuid, p_brand uuid, p_branch text DEFAULT NULL::text)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare b brands; s stores; v_br text := nullif(btrim(coalesce(p_branch, '')), '');
begin
  if not is_admin() then raise exception 'not_allowed'; end if;
  select * into b from brands where id = p_brand;  if not found then raise exception 'not_found'; end if;
  select * into s from stores where id = p_store;  if not found then raise exception 'not_found'; end if;
  if s.owner_id is distinct from b.owner_id then raise exception 'owner_mismatch'; end if;
  if v_br is not null and char_length(v_br) > 40 then raise exception 'bad_value'; end if;
  update stores set brand_id = p_brand, branch_name = v_br where id = p_store;
  insert into audit_log(user_id, action, table_name, row_id, details) values (auth.uid(), 'BRAND_ATTACH', 'stores', p_store::text, jsonb_build_object('brand', p_brand, 'branch', v_br));
end $function$
;
CREATE OR REPLACE FUNCTION public.brand_create(p_name text, p_owner_email text)
 RETURNS uuid
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare u uuid; v_id uuid; v_name text := btrim(coalesce(p_name, ''));
begin
  if not is_admin() then raise exception 'not_allowed'; end if;
  if char_length(v_name) < 2 or char_length(v_name) > 60 then raise exception 'bad_value'; end if;
  select id into u from auth.users where lower(email) = lower(btrim(coalesce(p_owner_email, '')));
  if u is null or not exists(select 1 from profiles where id = u) then raise exception 'user_not_found'; end if;
  insert into brands(name, owner_id) values (v_name, u) returning id into v_id;
  insert into audit_log(user_id, action, table_name, row_id, details) values (auth.uid(), 'BRAND_CREATE', 'brands', v_id::text, jsonb_build_object('name', v_name, 'owner', u));
  return v_id;
end $function$
;
CREATE OR REPLACE FUNCTION public.brand_detach(p_store uuid)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if not is_admin() then raise exception 'not_allowed'; end if;
  update stores set brand_id = null, branch_name = null where id = p_store and brand_id is not null;
  if not found then raise exception 'not_found'; end if;
  insert into audit_log(user_id, action, table_name, row_id, details) values (auth.uid(), 'BRAND_DETACH', 'stores', p_store::text, '{}'::jsonb);
end $function$
;
CREATE OR REPLACE FUNCTION public.brand_route(p_brand uuid, p_lat double precision, p_lng double precision, p_names text[] DEFAULT '{}'::text[])
 RETURNS TABLE(store_id uuid, name text, branch_name text, dist_km numeric, is_open boolean, missing text[])
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  with want as (select distinct lower(btrim(x)) as n from unnest(coalesce(p_names, '{}')) x where btrim(x) <> '' limit 60),
  b as (
    select s.id, s.name, s.branch_name, s.is_open,
           case when p_lat is null or p_lng is null or s.lat is null or s.lng is null then null else round(dist_km(p_lat, p_lng, s.lat, s.lng)::numeric, 2) end as d,
           array(select w.n from want w where not exists(select 1 from menu_items i where i.store_id = s.id and i.available and i.approved and lower(btrim(i.name)) = w.n)) as miss
      from stores s where s.brand_id = p_brand and s.is_active and auth.uid() is not null)
  select id, name, branch_name, d, is_open, miss from b
   order by (is_open and cardinality(miss) = 0) desc, is_open desc, cardinality(miss), d nulls last, name
$function$
;
CREATE OR REPLACE FUNCTION public.brand_stats(p_brand uuid, p_days integer DEFAULT 30)
 RETURNS TABLE(store_id uuid, name text, branch_name text, orders bigint, delivered bigint, cancelled bigint, revenue numeric)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  select s.id, s.name, s.branch_name,
         count(o.id), count(o.id) filter (where o.status = 'delivered'), count(o.id) filter (where o.status in ('cancelled', 'rejected')),
         coalesce(sum(o.total) filter (where o.status = 'delivered'), 0)::numeric
    from stores s
    join brands b on b.id = s.brand_id
    left join orders o on o.store_id = s.id and o.created_at > now() - make_interval(days => least(greatest(coalesce(p_days, 30), 1), 365))
   where s.brand_id = p_brand and (b.owner_id = auth.uid() or is_admin())
   group by s.id, s.name, s.branch_name order by s.name
$function$
;
CREATE OR REPLACE FUNCTION public.brand_sync_menu(p_from uuid, p_to uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare a stores; b stores; br brands; r jsonb;
begin
  select * into a from stores where id = p_from;  select * into b from stores where id = p_to;
  if a.id is null or b.id is null or p_from = p_to then raise exception 'not_found'; end if;
  if a.brand_id is null or a.brand_id is distinct from b.brand_id then raise exception 'bad_value'; end if;
  select * into br from brands where id = a.brand_id;
  if not (br.owner_id = auth.uid() or is_admin()) then raise exception 'not_allowed'; end if;
  r := copy_menu(p_from, p_to, true);
  insert into audit_log(user_id, action, table_name, row_id, details) values (auth.uid(), 'BRANCH_SYNC', 'stores', p_to::text, r || jsonb_build_object('from', p_from));
  return r;
end $function$
;
CREATE OR REPLACE FUNCTION public.can_see_order(o bigint)
 RETURNS boolean
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$ select exists(select 1 from orders r where r.id = o and (
     r.customer_id = auth.uid() or r.driver_id = auth.uid() or owns_store(r.store_id) or (has_perm('orders') or has_perm('support'))
     or (r.driver_id is null and r.status in ('preparing', 'ready') and exists(
          select 1 from order_offers f where f.order_id = r.id and f.driver_id = auth.uid()
             and f.state = 'pending' and f.expires_at > now())))) $function$
;
CREATE OR REPLACE FUNCTION public.cap_options()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if tg_table_name = 'item_option_groups' then
    if (select count(*) from item_option_groups where item_id = new.item_id) >= 10 then raise exception 'bad_value'; end if;
  else
    if (select count(*) from item_options where group_id = new.group_id) >= 30 then raise exception 'bad_value'; end if;
  end if;
  return new;
end $function$
;
CREATE OR REPLACE FUNCTION public.cash_balances()
 RETURNS TABLE(driver_id uuid, balance numeric)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  select o.driver_id, coalesce(sum(o.cash_collected), 0)::numeric
    from orders o
   where o.status = 'delivered' and o.cash_collected is not null and o.cash_settled_at is null
     and o.driver_id is not null and (has_perm('finance') or o.driver_id = auth.uid())
   group by o.driver_id
$function$
;
CREATE OR REPLACE FUNCTION public.check_image_url(u text)
 RETURNS boolean
 LANGUAGE sql
 IMMUTABLE
AS $function$
  select u is null or u = '' or u like 'data:image/%'
         or u like 'https://dzydscryrnahnneydnry.supabase.co/storage/v1/object/public/media/%'
$function$
;
CREATE OR REPLACE FUNCTION public.check_promo(p_code text, p_store uuid, p_items jsonb)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare
  v_uid uuid := auth.uid();
  v_bad int; v_all int; v_hh int := 0;
  v_res jsonb; v_err text; v_key text; v_ok boolean;
begin
  if v_uid is null then raise exception 'auth'; end if;
  perform pg_advisory_xact_lock(hashtext('promo_guess:' || v_uid::text));

  select count(*) filter (where bad), count(*) into v_bad, v_all
    from promo_guess where user_id = v_uid and at > now() - interval '10 minutes';
  if v_bad >= 10 or v_all >= 60 then raise exception 'too_many'; end if;

  -- during a happy hour (patch 29) every dish already has a discount: promo codes never apply then
  if to_regproc('public.happy_hour_pct') is not null then
    execute 'select happy_hour_pct($1)' into v_hh using p_store;
    if coalesce(v_hh, 0) > 0 then return jsonb_build_object('ok', false, 'error', 'promo_offer'); end if;
  end if;

  begin
    v_res := to_jsonb(check_promo_base(p_code, p_store, p_items));
  exception when others then
    v_err := sqlerrm;
  end;
  if v_err is not null then
    if v_err ~* 'too_many' then raise exception 'too_many'; end if;
    v_key := coalesce(substring(v_err from '([a-z]+_[a-z_]+)'), substring(v_err from '([a-z_]+)'), 'promo_invalid');
    v_res := jsonb_build_object('ok', false, 'error', v_key);       -- answered, not thrown: the attempt below is kept
  end if;

  v_ok := coalesce((v_res->>'ok')::boolean, false);
  v_key := lower(coalesce(v_res->>'error', ''));
  insert into promo_guess(user_id, bad)
  values (v_uid, not v_ok and v_key !~ '^(promo_min|promo_used|promo_limit|promo_offer|promo_expired|closed|store_unavailable|unavailable|bad_options|empty|account_blocked|phone_required|auth)$');
  delete from promo_guess where user_id = v_uid and at < now() - interval '1 day';
  return v_res;
end $function$
;
CREATE OR REPLACE FUNCTION public.check_promo_base(p_code text, p_store uuid, p_items jsonb)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare s stores; it record; v_item menu_items; pl jsonb; lt numeric; e numeric; v_sub numeric := 0; v_disc numeric := 0; v_base numeric := 0; v_gate numeric; tries int; v numeric; mn numeric;
begin
  if auth.uid() is null then raise exception 'auth'; end if;
  delete from promo_attempts where at < now() - interval '1 day';
  select count(*) into tries from promo_attempts where user_id = auth.uid() and not ok and at > now() - interval '10 minutes';
  if tries >= 10 then raise exception 'too_many'; end if;
  select * into s from stores where id = p_store and is_active;
  if not found then raise exception 'store_unavailable'; end if;
  if jsonb_typeof(p_items) <> 'array' or jsonb_array_length(p_items) = 0 or jsonb_array_length(p_items) > 60 then raise exception 'empty'; end if;
  begin
    for it in select (x->>'item_id')::uuid as item_id, least(50, greatest(1, (x->>'qty')::int)) as qty,
                     case when jsonb_typeof(x->'options') = 'array' then x->'options' else '[]'::jsonb end as opts
                from jsonb_array_elements(p_items) x loop
      select * into v_item from menu_items where id = it.item_id and store_id = p_store and available and approved;
      if not found then continue; end if;
      pl := price_line(it.item_id, it.opts);
      lt := (pl->>'unit')::numeric * it.qty;
      e := greatest(s.discount_pct, v_item.discount_pct);
      v_sub := v_sub + lt;
      v_disc := v_disc + round(lt * e / 100, 2);
      if e = 0 then v_base := v_base + lt; end if;
    end loop;
  exception when others then
    return jsonb_build_object('ok', false, 'error', 'bad_options');
  end;
  if v_sub > 0 and v_base = 0 then
    return jsonb_build_object('ok', false, 'error', 'promo_offer');
  end if;
  v_gate := v_sub - v_disc;
  begin
    v := promo_eval(p_code, v_base, auth.uid(), false, v_gate);
  exception when others then
    insert into promo_attempts(user_id, ok) values (auth.uid(), false);
    if sqlerrm = 'promo_min' then
      select min_order into mn from promo_codes where upper(code) = upper(trim(p_code));
      return jsonb_build_object('ok', false, 'error', 'promo_min', 'min', mn, 'have', v_gate);
    end if;
    return jsonb_build_object('ok', false, 'error',
      case when sqlerrm in ('promo_invalid', 'promo_used', 'promo_limit') then sqlerrm else 'promo_invalid' end);
  end;
  insert into promo_attempts(user_id, ok, code) values (auth.uid(), true, upper(trim(p_code)));
  return jsonb_build_object('ok', true, 'discount', v, 'base', v_base);
end $function$
;
CREATE OR REPLACE FUNCTION public.contacts_for(p_ids bigint[])
 RETURNS TABLE(order_id bigint, customer_phone text, driver_phone text)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  select t.i, cp.phone, dp.phone
    from unnest(case when cardinality(p_ids) > 200 then p_ids[1:200] else p_ids end) as t(i)
    left join order_customer_phone cp on cp.order_id = t.i
    left join order_driver_phone dp on dp.order_id = t.i
   where (has_perm('orders') or has_perm('support'))
$function$
;
CREATE OR REPLACE FUNCTION public.copy_menu(p_from uuid, p_to uuid, p_update boolean)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_add int := 0; v_upd int := 0;
begin
  if p_update then
    update menu_items d set price = s.price, discount_pct = s.discount_pct, available = s.available, section = s.section, popular = s.popular,
           image_url = coalesce(s.image_url, d.image_url)
      from menu_items s
     where s.store_id = p_from and d.store_id = p_to and lower(btrim(d.name)) = lower(btrim(s.name))
       and (d.price, d.discount_pct, d.available, d.section, d.popular) is distinct from (s.price, s.discount_pct, s.available, s.section, s.popular);
    get diagnostics v_upd = row_count;
  end if;
  with m as (
    select i.id as old_id, gen_random_uuid() as new_id from menu_items i
     where i.store_id = p_from and i.approved
       and not exists(select 1 from menu_items x where x.store_id = p_to and lower(btrim(x.name)) = lower(btrim(i.name)))),
  ins as (
    insert into menu_items(id, store_id, name, price, image_url, popular, available, section, discount_pct)
    select m.new_id, p_to, i.name, i.price, i.image_url, i.popular, i.available, i.section, i.discount_pct
      from menu_items i join m on m.old_id = i.id returning 1),
  g as (select og.id as old_g, gen_random_uuid() as new_g, m.new_id as item, og.name, og.required, og.max_sel, og.sort
          from item_option_groups og join m on m.old_id = og.item_id),
  insg as (insert into item_option_groups(id, item_id, name, required, max_sel, sort) select new_g, item, name, required, max_sel, sort from g returning 1),
  inso as (insert into item_options(group_id, name, price_delta, available, sort)
           select g.new_g, o.name, o.price_delta, o.available, o.sort from item_options o join g on g.old_g = o.group_id returning 1)
  select (select count(*) from ins) into v_add;
  return jsonb_build_object('added', v_add, 'updated', v_upd);
end $function$
;
CREATE OR REPLACE FUNCTION public.courier_steps_version()
 RETURNS integer
 LANGUAGE sql
 IMMUTABLE
AS $function$ select 34 $function$
;
CREATE OR REPLACE FUNCTION public.create_ticket(p_order bigint, p_reason text, p_message text)
 RETURNS bigint
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_o orders; v_id bigint; v_msg text := btrim(coalesce(p_message, ''));
begin
  if auth.uid() is null then raise exception 'auth'; end if;
  if p_reason is null or p_reason not in ('not_delivered', 'wrong_order', 'missing_items', 'quality', 'late', 'courier', 'restaurant', 'payment', 'other') then
    raise exception 'bad_value';
  end if;
  -- the message is optional when a reason is chosen; only "other" needs a real description
  if char_length(v_msg) < (case when p_reason = 'other' then 5 else 1 end) or char_length(v_msg) > 500 then raise exception 'bad_value'; end if;
  if (select count(*) from support_tickets where customer_id = auth.uid() and status in ('open', 'in_progress')) >= 5
     or (select count(*) from support_tickets where customer_id = auth.uid() and created_at > now() - interval '1 day') >= 10 then
    raise exception 'too_many';
  end if;
  if p_order is not null then
    select * into v_o from orders where id = p_order and customer_id = auth.uid();
    if not found then raise exception 'not_allowed'; end if;
    if v_o.status in ('delivered', 'rejected', 'cancelled') and coalesce(v_o.done_at, v_o.created_at) < now() - interval '48 hours' then
      raise exception 'ticket_expired';                    -- reports are accepted for 48 hours after the order ends
    end if;
    if not ticket_reason_ok(v_o.status::text, p_reason, true) then raise exception 'bad_value'; end if;   -- reasons must fit the stage of the order
  elsif not ticket_reason_ok('', p_reason, false) then
    raise exception 'bad_value';
  end if;
  begin
    insert into support_tickets(customer_id, order_id, reason) values (auth.uid(), p_order, p_reason) returning id into v_id;
  exception when unique_violation then
    raise exception 'ticket_exists';                       -- one open ticket per order
  end;
  insert into ticket_messages(ticket_id, from_staff, sender_id, body) values (v_id, false, auth.uid(), v_msg);
  return v_id;
end $function$
;
CREATE OR REPLACE FUNCTION public.decide_store_request(p_id uuid, p_approve boolean, p_note text DEFAULT NULL::text)
 RETURNS uuid
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_r store_requests; v_store uuid; v_note text := nullif(left(btrim(coalesce(p_note, '')), 300), '');
begin
  if not is_admin() then raise exception 'not_allowed'; end if;
  select * into v_r from store_requests where id = p_id and status = 'pending' for update;
  if not found then raise exception 'bad_transition'; end if;
  if coalesce(p_approve, false) then
    insert into stores(name, category, phone, address, lat, lng, owner_id, commission_pct, fee_type, fee_base, is_active, is_open)
    values (v_r.name, v_r.category, v_r.phone, v_r.address, v_r.lat, v_r.lng, v_r.user_id, 10, 'fixed', 10, false, false)
    returning id into v_store;
  elsif v_note is null then
    raise exception 'note_required';
  end if;
  update store_requests set status = case when coalesce(p_approve, false) then 'approved' else 'rejected' end,
         admin_note = v_note, store_id = v_store, decided_at = now(), decided_by = auth.uid() where id = p_id;
  return v_store;
end $function$
;
CREATE OR REPLACE FUNCTION public.deliver_order(p_id bigint, p_cash numeric DEFAULT NULL::numeric, p_note text DEFAULT NULL::text, p_photo text DEFAULT NULL::text)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
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
end $function$
;
CREATE OR REPLACE FUNCTION public.delivery_calc(p_store uuid, p_lat double precision, p_lng double precision, p_uid uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_s stores; v_free numeric; v_step numeric; v_price numeric; v_max numeric; v_fac numeric;
        v_straight float8; v_road numeric; v_steps int := 0; v_extra numeric := 0; v_base numeric; v_full numeric; v_fee numeric; v_first boolean := false;
begin
  if p_lat is null or p_lng is null or p_lat not between -90 and 90 or p_lng not between -180 and 180 then raise exception 'bad_value'; end if;
  select * into v_s from stores where id = p_store and is_active;
  if not found then raise exception 'store_unavailable'; end if;
  select coalesce((select value from app_settings where key = 'delivery_free_km'), 3) into v_free;
  select coalesce((select value from app_settings where key = 'delivery_step_km'), 0.5) into v_step;
  select coalesce((select value from app_settings where key = 'delivery_step_price'), 2) into v_price;
  select coalesce((select value from app_settings where key = 'delivery_max_km'), 15) into v_max;
  select coalesce((select value from app_settings where key = 'delivery_road_factor'), 1.3) into v_fac;
  v_base := case v_s.fee_type when 'free' then 0 else v_s.fee_base end;
  if v_s.lat is not null and v_s.lng is not null then
    v_straight := dist_km(v_s.lat, v_s.lng, p_lat, p_lng);
    v_road := round((v_straight * v_fac)::numeric, 2);
    if v_road > v_max then raise exception 'too_far'; end if;
    if v_s.fee_type = 'distance' then
      v_steps := ceil(round(greatest(0, v_road - v_free) / v_step, 6));
      v_extra := v_steps * v_price;
    end if;
  end if;
  v_full := v_base + v_extra;
  v_fee := v_full;
  if v_s.free_first_delivery and v_s.fee_type <> 'free' and p_uid is not null
     and not exists (select 1 from orders where customer_id = p_uid and store_id = p_store and status not in ('rejected', 'cancelled')) then
    v_first := true; v_fee := 0;
  end if;
  return jsonb_build_object('fee', v_fee, 'fee_full', v_full, 'base', v_base, 'extra', v_extra, 'steps', v_steps,
    'km', v_road, 'km_straight', round(v_straight::numeric, 2), 'free_km', v_free, 'step_km', v_step, 'step_price', v_price,
    'max_km', v_max, 'first_free', v_first, 'fee_type', v_s.fee_type);
end $function$
;
CREATE OR REPLACE FUNCTION public.delivery_quote(p_store uuid, p_lat double precision, p_lng double precision)
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if auth.uid() is null then raise exception 'auth'; end if;
  return delivery_calc(p_store, p_lat, p_lng, auth.uid());
end $function$
;
CREATE OR REPLACE FUNCTION public.dispatch_next(p_order bigint)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare o orders; v_timer int := 30; v_rounds int := 3; v_radius float8 := 10; v_bcast boolean; v_single int; c record;
begin
  select * into o from orders where id = p_order for update skip locked;
  if not found or o.driver_id is not null or o.status not in ('preparing', 'ready') then return; end if;
  select coalesce(bool_or(mode = 'broadcast'), false), count(*) filter (where mode = 'single')
    into v_bcast, v_single from order_offers where order_id = p_order;
  if exists (select 1 from order_offers where order_id = p_order and state = 'pending' and expires_at > now()) and not v_bcast then
    return;                                    -- a single offer is still waiting for an answer
  end if;
  if not v_bcast and v_single < v_rounds then
    select e.id, e.dist into c from eligible_couriers(p_order, false) e
     where e.fresh and e.dist is not null and e.dist <= v_radius order by e.dist limit 1;
    if found then
      insert into order_offers(order_id, driver_id, state, mode, rank, dist_km, expires_at)
      values (p_order, c.id, 'pending', 'single', v_single + 1, round(c.dist::numeric, 2), now() + make_interval(secs => v_timer));
      return;
    end if;
  end if;
  -- broadcast (also used when nobody is near or the nearest couriers did not answer)
  insert into order_offers(order_id, driver_id, state, mode, rank, dist_km, expires_at)
  select p_order, e.id, 'pending', 'broadcast', 0, round(e.dist::numeric, 2), now() + interval '10 minutes'
    from eligible_couriers(p_order, true) e
  on conflict (order_id, driver_id) do update
     set state = 'pending', mode = 'broadcast', offered_at = now(), expires_at = excluded.expires_at, dist_km = excluded.dist_km
   where order_offers.state = 'expired';
end $function$
;
CREATE OR REPLACE FUNCTION public.dispatch_tick()
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare r record;
begin
  if auth.uid() is null or not exists (select 1 from profiles where id = auth.uid() and role in ('driver', 'admin', 'merchant')) then return; end if;
  if not pg_try_advisory_xact_lock(hashtext('dispatch_tick')) then return; end if;
  update order_offers set state = 'expired' where state = 'pending' and expires_at <= now();
  for r in select id from orders
            where driver_id is null and status in ('preparing', 'ready') and created_at > now() - interval '12 hours'
            order by created_at loop
    perform dispatch_next(r.id);
  end loop;
end $function$
;
CREATE OR REPLACE FUNCTION public.dist_km(a1 double precision, o1 double precision, a2 double precision, o2 double precision)
 RETURNS double precision
 LANGUAGE sql
 IMMUTABLE
AS $function$ select 2*6371*asin(sqrt(power(sin(radians(a2-a1)/2),2) + cos(radians(a1))*cos(radians(a2))*power(sin(radians(o2-o1)/2),2))) $function$
;
CREATE OR REPLACE FUNCTION public.driver_accept(p_id bigint)
 RETURNS boolean
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_id bigint; v_name text; v_blocked boolean; v_phone text;
begin
  select name, accept_blocked, phone into v_name, v_blocked, v_phone from profiles
   where id = auth.uid() and role = 'driver' and driver_status = 'approved';
  if not found then raise exception 'not_approved'; end if;
  if v_blocked then raise exception 'blocked'; end if;
  if norm_phone(v_phone) is null then raise exception 'phone_required'; end if;
  if exists (select 1 from orders x where x.driver_id = auth.uid() and x.status in ('preparing', 'ready', 'pickedup')) then
    raise exception 'busy';
  end if;
  if not exists (select 1 from order_offers where order_id = p_id and driver_id = auth.uid() and state = 'pending' and expires_at > now()) then
    raise exception 'no_offer';
  end if;
  update orders set driver_id = auth.uid(), driver_name = v_name
   where id = p_id and driver_id is null and status in ('preparing', 'ready') returning id into v_id;
  if v_id is not null then
    update order_offers set state = case when driver_id = auth.uid() then 'accepted' else 'cancelled' end
     where order_id = p_id and state = 'pending';
    insert into order_driver_phone(order_id, phone) values (p_id, norm_phone(v_phone))
      on conflict (order_id) do update set phone = excluded.phone;
  end if;
  return v_id is not null;
end $function$
;
CREATE OR REPLACE FUNCTION public.driver_arrived(p_id bigint, p_where text)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare o orders;
begin
  select * into o from orders where id = p_id for update;
  if not found then raise exception 'not_found'; end if;
  if o.driver_id is distinct from auth.uid() then raise exception 'not_allowed'; end if;
  if p_where = 'store' then
    if o.status not in ('preparing', 'ready') then raise exception 'bad_transition'; end if;
    update orders set arrived_store_at = coalesce(arrived_store_at, now()) where id = p_id;
  elsif p_where = 'customer' then
    if o.status <> 'pickedup' then raise exception 'bad_transition'; end if;
    update orders set arrived_cust_at = coalesce(arrived_cust_at, now()) where id = p_id;
  else
    raise exception 'bad_value';
  end if;
  -- also in the order timeline when the existing events table accepts it (its kinds are not known here)
  begin
    insert into order_events(order_id, kind) values (p_id, case p_where when 'store' then 'at_store' else 'at_customer' end);
  exception when others then null;
  end;
end $function$
;
CREATE OR REPLACE FUNCTION public.driver_decline(p_id bigint)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if auth.uid() is null then raise exception 'auth'; end if;
  update order_offers set state = 'declined' where order_id = p_id and driver_id = auth.uid() and state = 'pending';
  if found then perform dispatch_next(p_id); end if;
end $function$
;
CREATE OR REPLACE FUNCTION public.driver_location(p_lat double precision, p_lng double precision, p_acc double precision DEFAULT NULL::double precision)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if auth.uid() is null then raise exception 'auth'; end if;
  if p_lat is null or p_lng is null or p_lat not between -90 and 90 or p_lng not between -180 and 180 then
    raise exception 'bad_value';
  end if;
  update profiles
     set lat = p_lat, lng = p_lng,
         loc_acc = case when p_acc between 0 and 100000 then p_acc end,
         loc_updated = now(), last_seen = now()
   where id = auth.uid() and role = 'driver' and driver_status = 'approved' and online
     and (loc_updated is null or loc_updated < now() - interval '3 seconds');   -- at most one point per 3 s
end $function$
;
CREATE OR REPLACE FUNCTION public.driver_ping(p_online boolean)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if auth.uid() is null then raise exception 'auth'; end if;
  update profiles
     set online = coalesce(p_online, false), last_seen = now(),
         lat = case when coalesce(p_online, false) then lat end,
         lng = case when coalesce(p_online, false) then lng end,
         loc_acc = case when coalesce(p_online, false) then loc_acc end,
         loc_updated = case when coalesce(p_online, false) then loc_updated end
   where id = auth.uid() and role = 'driver' and driver_status = 'approved';
end $function$
;
CREATE OR REPLACE FUNCTION public.eligible_couriers(p_order bigint, p_reoffer boolean DEFAULT false)
 RETURNS TABLE(id uuid, dist double precision, fresh boolean)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  select p.id,
         case when st.lat is not null and p.lat is not null and p.loc_updated > now() - interval '3 minutes'
              then dist_km(st.lat, st.lng, p.lat, p.lng) end,
         coalesce(p.loc_updated > now() - interval '3 minutes', false)
    from orders o
    join stores st on st.id = o.store_id
    join profiles p on p.role = 'driver' and p.driver_status = 'approved' and not p.accept_blocked and p.online
                   and p.last_seen > now() - interval '2 minutes'
   where o.id = p_order
     and not exists (select 1 from orders b where b.driver_id = p.id and b.status in ('preparing', 'ready', 'pickedup'))
     and not exists (select 1 from order_offers f
                      where f.order_id = p_order and f.driver_id = p.id
                        and not (p_reoffer and f.state = 'expired'))
$function$
;
CREATE OR REPLACE FUNCTION public.group_add(p_id uuid, p_item uuid, p_qty integer, p_options jsonb DEFAULT '[]'::jsonb, p_note text DEFAULT NULL::text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare g group_orders; v_name text;
begin
  if auth.uid() is null then raise exception 'auth'; end if;
  select * into g from group_orders where id = p_id for update;
  if not found or g.status <> 'open' or g.expires_at < now() then raise exception 'group_closed'; end if;
  if p_qty is null or p_qty not between 1 and 20 then raise exception 'bad_value'; end if;
  if not exists (select 1 from menu_items where id = p_item and store_id = g.store_id and available and approved) then raise exception 'unavailable'; end if;
  perform price_line(p_item, coalesce(p_options, '[]'::jsonb));          -- the same option rules as a normal order
  if (select count(*) from group_items where group_id = p_id) >= 60 or (select count(*) from group_items where group_id = p_id and user_id = auth.uid()) >= 20 then
    raise exception 'too_many';
  end if;
  select coalesce(nullif(btrim(name), ''), 'Гость') into v_name from profiles where id = auth.uid();
  insert into group_items(group_id, user_id, user_name, item_id, qty, options, note)
  values (p_id, auth.uid(), left(v_name, 40), p_item, p_qty, coalesce(p_options, '[]'::jsonb), nullif(left(btrim(coalesce(p_note, '')), 120), ''));
  return group_json(p_id);
end $function$
;
CREATE OR REPLACE FUNCTION public.group_create(p_store uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_id uuid;
begin
  if auth.uid() is null then raise exception 'auth'; end if;
  if not exists (select 1 from stores where id = p_store and is_active) then raise exception 'store_unavailable'; end if;
  if (select count(*) from group_orders where host_id = auth.uid() and created_at > now() - interval '1 day') >= 10 then raise exception 'too_many'; end if;
  update group_orders set status = 'cancelled' where host_id = auth.uid() and status in ('open', 'closed');   -- one open group per host
  insert into group_orders(store_id, host_id) values (p_store, auth.uid()) returning id into v_id;
  return group_json(v_id);
end $function$
;
CREATE OR REPLACE FUNCTION public.group_get(p_id uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if auth.uid() is null then raise exception 'auth'; end if;
  update group_orders set status = 'cancelled' where id = p_id and status = 'open' and expires_at < now();
  return group_json(p_id);
end $function$
;
CREATE OR REPLACE FUNCTION public.group_json(p_id uuid)
 RETURNS jsonb
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  select jsonb_build_object('id', g.id, 'store_id', g.store_id, 'host_id', g.host_id, 'is_host', g.host_id = auth.uid(),
    'host_name', (select name from profiles where id = g.host_id), 'status', g.status, 'expires_at', g.expires_at, 'order_id', g.order_id,
    'items', coalesce((select jsonb_agg(jsonb_build_object('id', i.id, 'user_name', i.user_name, 'mine', i.user_id = auth.uid(),
        'item_id', i.item_id, 'qty', i.qty, 'options', i.options, 'note', i.note) order by i.created_at) from group_items i where i.group_id = g.id), '[]'::jsonb))
  from group_orders g where g.id = p_id
$function$
;
CREATE OR REPLACE FUNCTION public.group_remove(p_line bigint)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_g uuid;
begin
  select i.group_id into v_g from group_items i join group_orders g on g.id = i.group_id
   where i.id = p_line and g.status = 'open' and (i.user_id = auth.uid() or g.host_id = auth.uid());
  if v_g is null then raise exception 'not_allowed'; end if;
  delete from group_items where id = p_line;
  return group_json(v_g);
end $function$
;
CREATE OR REPLACE FUNCTION public.group_set(p_id uuid, p_status text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if p_status not in ('open', 'closed', 'cancelled') then raise exception 'bad_value'; end if;
  update group_orders set status = p_status, closed_at = case when p_status = 'closed' then now() else closed_at end,
         expires_at = case when p_status = 'open' then greatest(expires_at, now() + interval '1 hour') else expires_at end
   where id = p_id and host_id = auth.uid() and status in ('open', 'closed');
  if not found then raise exception 'not_allowed'; end if;
  return group_json(p_id);
end $function$
;
CREATE OR REPLACE FUNCTION public.guard_item_approval()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if new.approved and not old.approved and auth.uid() is not null and not has_perm('stores')
     and current_setting('app.bypass', true) is distinct from '1' then
    raise exception 'not_allowed';
  end if;
  return new;
end $function$
;
CREATE OR REPLACE FUNCTION public.guard_profile()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if auth.uid() is null or current_setting('app.bypass', true) = '1' or is_admin() then return new; end if;
  if new.role <> old.role or new.driver_status is distinct from old.driver_status
     or new.cash_limit <> old.cash_limit or new.accept_blocked <> old.accept_blocked
     or new.banned_at is distinct from old.banned_at or new.banned_reason is distinct from old.banned_reason
     or new.phone_changed_at is distinct from old.phone_changed_at then
    raise exception 'not_allowed';
  end if;
  return new;
end $function$
;
CREATE OR REPLACE FUNCTION public.handle_new_user()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  insert into profiles(id, name, phone)
  values (new.id, left(btrim(coalesce(new.raw_user_meta_data->>'name', '')), 80),
          coalesce(norm_phone(new.raw_user_meta_data->>'phone'), norm_phone(new.phone)));
  return new;
end $function$
;
CREATE OR REPLACE FUNCTION public.happy_hour_pct(p_store uuid, p_at timestamp with time zone DEFAULT now())
 RETURNS integer
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  with l as (select (p_at at time zone 'Asia/Dushanbe') as t)
  select coalesce(max(h.discount_pct), 0)::int
    from happy_hours h, l
   where h.active and (h.store_id is null or h.store_id = p_store)
     and (
       (h.start_time < h.end_time and extract(isodow from l.t)::smallint = any(h.days) and l.t::time >= h.start_time and l.t::time < h.end_time)
       or (h.start_time > h.end_time and (
            (extract(isodow from l.t)::smallint = any(h.days) and l.t::time >= h.start_time)
         or (extract(isodow from (l.t - interval '1 day'))::smallint = any(h.days) and l.t::time < h.end_time)))
     )
$function$
;
CREATE OR REPLACE FUNCTION public.has_perm(p text)
 RETURNS boolean
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  select auth.uid() is not null and (
    exists(select 1 from profiles where id = auth.uid() and role = 'admin')
    or exists(select 1 from staff_members s where s.user_id = auth.uid() and s.active and p = any(s.perms)))
$function$
;
CREATE OR REPLACE FUNCTION public.is_admin()
 RETURNS boolean
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$ select exists(select 1 from profiles where id = auth.uid() and role = 'admin') $function$
;
CREATE OR REPLACE FUNCTION public.item_approval()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if auth.uid() is not null and not has_perm('stores')
     and exists(select 1 from stores where id = new.store_id and category = 'pharmacy') then
    new.approved := false;   -- pharmacy items appear only after admin approval
  end if;
  return new;
end $function$
;
CREATE OR REPLACE FUNCTION public.log_order_event()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if tg_op = 'INSERT' then
    insert into order_events(order_id, kind) values (new.id, 'pending');
  else
    if new.status is distinct from old.status then
      insert into order_events(order_id, kind) values (new.id, new.status::text);
    end if;
    if old.driver_id is null and new.driver_id is not null then
      insert into order_events(order_id, kind) values (new.id, 'driver_assigned');
    end if;
  end if;
  return null;
end $function$
;
CREATE OR REPLACE FUNCTION public.loyalty_balance(p_user uuid)
 RETURNS integer
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  select coalesce(sum(points_left), 0)::int from loyalty_lots where user_id = p_user and points_left > 0 and expires_at > now()
$function$
;
CREATE OR REPLACE FUNCTION public.loyalty_setting(p_key text)
 RETURNS numeric
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  select coalesce((select value from app_settings where key = p_key),
    case p_key when 'loyalty_earn_per_tjs' then 10 when 'loyalty_points_per_tjs' then 1000 when 'loyalty_min_redeem' then 1000
               when 'loyalty_expiry_days' then 90 when 'loyalty_voucher_points' then 1000 when 'loyalty_min_order' then 30
               when 'loyalty_rate_reward' then 10 else 0 end)
$function$
;
CREATE OR REPLACE FUNCTION public.loyalty_spend(p_user uuid, p_points integer, p_order bigint)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare l record; v_left int := p_points; v_take int;
begin
  for l in select id, points_left from loyalty_lots where user_id = p_user and points_left > 0 and expires_at > now()
            order by expires_at, id for update loop
    exit when v_left <= 0;
    v_take := least(l.points_left, v_left);
    update loyalty_lots set points_left = points_left - v_take where id = l.id;
    v_left := v_left - v_take;
  end loop;
  if v_left > 0 then raise exception 'points_changed'; end if;
  insert into loyalty_ledger(user_id, points, kind, order_id) values (p_user, -p_points, 'spend', p_order);
end $function$
;
CREATE OR REPLACE FUNCTION public.loyalty_summary()
 RETURNS jsonb
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  select jsonb_build_object(
    'balance', loyalty_balance(auth.uid()),
    'next_exp_at', (select min(expires_at) from loyalty_lots where user_id = auth.uid() and points_left > 0 and expires_at > now()),
    'next_exp_pts', (select coalesce(sum(points_left), 0) from loyalty_lots where user_id = auth.uid() and points_left > 0 and expires_at > now()
                       and expires_at < (select min(expires_at) from loyalty_lots where user_id = auth.uid() and points_left > 0 and expires_at > now()) + interval '1 day'),
    'earn_per_tjs', loyalty_setting('loyalty_earn_per_tjs'), 'points_per_tjs', loyalty_setting('loyalty_points_per_tjs'),
    'min_redeem', loyalty_setting('loyalty_min_redeem'), 'expiry_days', loyalty_setting('loyalty_expiry_days'), 'cashback_pct', loyalty_setting('cashback_pct'),
    'voucher_points', loyalty_setting('loyalty_voucher_points'), 'min_order', loyalty_setting('loyalty_min_order'), 'rate_reward', loyalty_setting('loyalty_rate_reward'))
  where auth.uid() is not null
$function$
;
CREATE OR REPLACE FUNCTION public.my_offers()
 RETURNS TABLE(order_id bigint, mode text, rank integer, dist_km numeric, secs_left integer)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  select f.order_id, f.mode, f.rank, f.dist_km, greatest(0, extract(epoch from (f.expires_at - now()))::int)
    from order_offers f join orders o on o.id = f.order_id
   where f.driver_id = auth.uid() and f.state = 'pending' and f.expires_at > now()
     and o.driver_id is null and o.status in ('preparing', 'ready')
   order by f.offered_at
$function$
;
CREATE OR REPLACE FUNCTION public.my_perms()
 RETURNS text[]
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  select case
    when auth.uid() is null then null
    when exists(select 1 from profiles where id = auth.uid() and role = 'admin') then array['orders','support','finance','stores','content']
    else (select s.perms from staff_members s where s.user_id = auth.uid() and s.active and cardinality(s.perms) > 0)
  end
$function$
;
CREATE OR REPLACE FUNCTION public.my_rating()
 RETURNS jsonb
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  select jsonb_build_object('avg', round(avg(driver_stars)::numeric, 1), 'count', count(driver_stars))
    from ratings where driver_id = auth.uid()
$function$
;
CREATE OR REPLACE FUNCTION public.norm_phone(p text)
 RETURNS text
 LANGUAGE sql
 IMMUTABLE
AS $function$
  select case
    when d ~ '^992[0-9]{9}$' then '+' || d
    when d ~ '^[0-9]{9}$' then '+992' || d
    when d ~ '^0[0-9]{9}$' then '+992' || substr(d, 2)
    else null end
  from (select regexp_replace(coalesce(p, ''), '[^0-9]', '', 'g') as d) x
$function$
;
CREATE OR REPLACE FUNCTION public.order_contacts(p_order bigint)
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_o orders; v_cp text; v_dp text; v_active boolean;
begin
  if auth.uid() is null then raise exception 'auth'; end if;
  select * into v_o from orders where id = p_order;
  if not found then return '{}'::jsonb; end if;
  v_active := v_o.status in ('preparing', 'ready', 'pickedup');
  select phone into v_cp from order_customer_phone where order_id = p_order;
  select phone into v_dp from order_driver_phone where order_id = p_order;
  if (has_perm('orders') or has_perm('support')) then return jsonb_build_object('customer_phone', v_cp, 'driver_phone', v_dp); end if;
  return jsonb_build_object(
    'customer_phone', case when v_active and v_o.driver_id = auth.uid() then v_cp end,
    'driver_phone', case when v_active and v_o.driver_id is not null and (v_o.customer_id = auth.uid() or owns_store(v_o.store_id)) then v_dp end);
end $function$
;
CREATE OR REPLACE FUNCTION public.order_courier_position(p_order bigint)
 RETURNS TABLE(lat double precision, lng double precision, acc double precision, updated_at timestamp with time zone)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  select p.lat, p.lng, p.loc_acc, p.loc_updated
  from public.orders o
  join public.profiles p on p.id = o.driver_id
  where o.id = p_order
    and o.customer_id = auth.uid()
    and o.status = 'pickedup'
    and p.lat is not null and p.lng is not null;
$function$
;
CREATE OR REPLACE FUNCTION public.owns_store(s uuid)
 RETURNS boolean
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$ select exists(select 1 from stores where id = s and owner_id = auth.uid()) $function$
;
CREATE OR REPLACE FUNCTION public.place_order(p_store uuid, p_items jsonb, p_tip numeric DEFAULT 0, p_payment text DEFAULT 'cash'::text, p_address text DEFAULT ''::text, p_lat double precision DEFAULT NULL::double precision, p_lng double precision DEFAULT NULL::double precision, p_promo text DEFAULT NULL::text, p_key text DEFAULT NULL::text, p_fee numeric DEFAULT NULL::numeric, p_wallet numeric DEFAULT NULL::numeric, p_points integer DEFAULT NULL::integer, p_extra jsonb DEFAULT NULL::jsonb)
 RETURNS bigint
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare s stores; pr profiles; it record; v_item menu_items; pl jsonb; v_id bigint; v_sub numeric; v_fee numeric; v_pay numeric; v_disc numeric; v_base numeric; v_gate numeric;
        v_promo numeric := 0; v_tip numeric; v_km float8; v_code text := null; v_dq jsonb; v_cphone text; v_total numeric; v_bal numeric; v_w numeric;
        v_hh int := 0; v_all numeric; v_hdisc numeric := 0; v_rate numeric; v_min numeric; v_lb int; v_pts int := 0; v_pval numeric := 0; v_cap numeric;
        v_step numeric; v_mo numeric; v_subst text; v_door boolean; v_gn text; v_gp text;
        v_at timestamptz; v_waived numeric := 0; v_gid uuid; g group_orders;
begin
  if p_wallet is not null and p_wallet < 0 then raise exception 'bad_value'; end if;
  if p_points is not null and (p_points < 0 or p_points > 100000000) then raise exception 'bad_value'; end if;
  -- order options (v50): leave at the door, what to do if a dish is missing, a gift for someone else
  v_door := coalesce((p_extra->>'door')::boolean, false);
  v_subst := coalesce(p_extra->>'subst', 'call');
  if v_subst not in ('call', 'replace', 'remove') then raise exception 'bad_value'; end if;
  -- scheduled delivery time (v51): from 45 minutes (with a little slack for the screen) to 3 days ahead
  if nullif(p_extra->>'at', '') is not null then
    begin v_at := (p_extra->>'at')::timestamptz; exception when others then raise exception 'bad_time'; end;
    if v_at < now() + interval '40 minutes' or v_at > now() + interval '3 days' then raise exception 'bad_time'; end if;
  end if;
  -- office / group order (v51): only its host can place it, once
  if nullif(p_extra->>'group', '') is not null then
    begin v_gid := (p_extra->>'group')::uuid; exception when others then raise exception 'bad_group'; end;
    select * into g from group_orders where id = v_gid for update;
    if not found or g.host_id <> auth.uid() or g.status not in ('open', 'closed') or g.store_id <> p_store then raise exception 'bad_group'; end if;
  end if;
  if p_extra ? 'gift' and jsonb_typeof(p_extra->'gift') = 'object' then
    v_gn := btrim(coalesce(p_extra->'gift'->>'name', '')); v_gp := norm_phone(p_extra->'gift'->>'phone');
    if char_length(v_gn) not between 2 and 60 or v_gp is null then raise exception 'bad_gift'; end if;
  end if;   -- a negative amount would mean ADDING money: refuse it
  if auth.uid() is null then raise exception 'auth'; end if;
  -- idempotency: a retry of the SAME attempt (bad network, double tap) returns the order that already exists
  if p_key is not null then
    if p_key !~ '^[A-Za-z0-9_-]{8,64}$' then raise exception 'bad_value'; end if;
    select o.id into v_id from orders o where o.customer_id = auth.uid() and o.client_key = p_key;
    if found then return v_id; end if;
  end if;
  -- abuse guard: at most 20 orders per hour per customer
  if (select count(*) from orders where customer_id = auth.uid() and created_at > now() - interval '1 hour') >= 20 then
    raise exception 'too_many_orders';
  end if;
  -- spam / abuse guard: at most 5 unfinished orders per customer
  if (select count(*) from orders where customer_id = auth.uid() and status in ('pending', 'preparing', 'ready', 'pickedup')) >= 5 then
    raise exception 'too_many_orders';
  end if;
  if (p_lat is not null and (p_lat < -90 or p_lat > 90)) or (p_lng is not null and (p_lng < -180 or p_lng > 180)) then
    raise exception 'bad_value';
  end if;
  -- a delivery address (text + map point) is mandatory
  if p_lat is null or p_lng is null or char_length(btrim(coalesce(p_address, ''))) < 3 then
    raise exception 'address_required';
  end if;
  select * into s from stores where id = p_store and is_active;
  if not found then raise exception 'store_unavailable'; end if;
  if not s.is_open then raise exception 'closed'; end if;
  v_hh := happy_hour_pct(p_store);                                -- admin-scheduled happy hour (paid by the platform)
  if jsonb_typeof(p_items) <> 'array' or jsonb_array_length(p_items) = 0 then raise exception 'empty'; end if;
  if jsonb_array_length(p_items) > 60 then raise exception 'bad_value'; end if;
  select * into pr from profiles where id = auth.uid();

  -- the customer phone is required (stored privately, see order_customer_phone) and the fee is calculated here, never by the app
  if pr.banned_at is not null then raise exception 'account_blocked'; end if;   -- a suspended account cannot order
  v_cphone := norm_phone(pr.phone);
  if v_cphone is null then raise exception 'phone_required'; end if;
  v_dq := delivery_calc(p_store, p_lat, p_lng, auth.uid());
  v_fee := (v_dq->>'fee')::numeric;
  v_pay := case s.fee_type when 'free' then s.fee_base else (v_dq->>'fee_full')::numeric end;   -- courier is always paid; the platform covers free delivery
  v_tip := case when p_tip in (0,3,5,10) then p_tip else 0 end;

  begin
    insert into orders(store_id, customer_id, customer_name, payment, address, lat, lng, client_key, leave_at_door, substitution, is_gift, scheduled_for, group_id)
    values (p_store, auth.uid(), pr.name, left(p_payment,40), left(p_address,200), p_lat, p_lng, p_key, v_door, v_subst, v_gn is not null, v_at, v_gid)
    returning id into v_id;
  exception when unique_violation then
    -- two taps raced: the other attempt won, return its order
    select o.id into v_id from orders o where o.customer_id = auth.uid() and o.client_key = p_key;
    return v_id;
  end;
  insert into order_customer_phone(order_id, phone) values (v_id, v_cphone);
  if v_gn is not null then insert into order_recipient(order_id, name, phone) values (v_id, v_gn, v_gp); end if;

  -- every line is priced by the DATABASE: base price + the chosen options (validated against the item's own option groups)
  for it in select (x->>'item_id')::uuid as item_id,
                   least(50, greatest(1, (x->>'qty')::int)) as qty,
                   left(coalesce(x->>'note', ''), 120) as note,
                   case when jsonb_typeof(x->'options') = 'array' then x->'options' else '[]'::jsonb end as opts
              from jsonb_array_elements(p_items) x loop
    select * into v_item from menu_items where id = it.item_id and store_id = p_store and available and approved;
    if not found then raise exception 'unavailable'; end if;
    pl := price_line(it.item_id, it.opts);
    insert into order_items(order_id, item_id, name, price, qty, note, options)
    values (v_id, v_item.id, v_item.name, (pl->>'unit')::numeric, it.qty, it.note, pl->'snap');
  end loop;

  -- each line gets the better of the store discount and its own item discount (they do not stack; paid by the restaurant).
  -- A happy hour can only make it better. Owner decision (v48): the RESTAURANT pays it too, like its own offers: it is part of
  -- orders.discount (so revenue and commission are on what the customer pays); orders.hh_discount says how much of it came from the happy hour.
  select sum(oi.price * oi.qty),
         coalesce(sum(round(oi.price * oi.qty * greatest(s.discount_pct, coalesce(m.discount_pct, 0)) / 100, 2)), 0),
         coalesce(sum(round(oi.price * oi.qty * greatest(s.discount_pct, coalesce(m.discount_pct, 0), v_hh) / 100, 2)), 0),
         coalesce(sum(oi.price * oi.qty) filter (where greatest(s.discount_pct, coalesce(m.discount_pct, 0), v_hh) = 0), 0)
    into v_sub, v_disc, v_all, v_base
    from order_items oi left join menu_items m on m.id = oi.item_id
   where oi.order_id = v_id;
  v_hdisc := v_all - v_disc;
  -- free delivery above the restaurant's own threshold (v51): the restaurant pays the waived fee (orders.fee_waived)
  if coalesce(s.free_delivery_min, 0) > 0 and v_sub - v_disc - v_hdisc >= s.free_delivery_min and v_fee > 0 then
    v_waived := v_fee; v_fee := 0;
  end if;
  if p_fee is not null and abs(p_fee - v_fee) > 0.009 then raise exception 'fee_changed'; end if;   -- the price shown to the customer must be the price charged

  if p_promo is not null and length(trim(p_promo)) > 0 then
    if v_base <= 0 then raise exception 'promo_offer'; end if;     -- promo codes never apply to lines that already have an offer
    if not exists (select 1 from promo_attempts where user_id = auth.uid() and ok and code = upper(trim(p_promo))
                    and at > now() - interval '2 hours') then
      raise exception 'promo_invalid';                             -- must be validated (rate-limited) in check_promo first
    end if;
    v_gate := v_sub - v_disc - v_hdisc;                                       -- the minimum order is checked on what the customer pays for items
    v_promo := promo_eval(p_promo, v_base, auth.uid(), true, v_gate);
    if v_promo > 0 then v_code := upper(trim(p_promo)); end if;
  end if;

  update orders set subtotal = v_sub, discount = v_disc + v_hdisc, delivery_fee = v_fee, fee_waived = v_waived, tip = v_tip,
    delivery_base = (v_dq->>'base')::numeric, delivery_extra = (v_dq->>'extra')::numeric, delivery_km = (v_dq->>'km')::numeric,
    promo_code = v_code, promo_discount = v_promo, hh_discount = v_hdisc, hh_pct = v_hh,
    total = greatest(5, v_sub - v_disc - v_hdisc - v_promo + v_fee + v_tip),
    commission_pct = s.commission_pct, commission = round((v_sub - v_disc - v_hdisc) * s.commission_pct / 100, 2),
    driver_payout = v_pay + v_tip
  where id = v_id;

  -- POINTS: the customer may pay part of the items with loyalty points (all he can use, decided here, never by the app)
  if coalesce(p_points, 0) > 0 then
    v_rate := loyalty_setting('loyalty_points_per_tjs'); v_min := loyalty_setting('loyalty_min_redeem');
    v_step := greatest(1, loyalty_setting('loyalty_voucher_points'));
    v_mo := coalesce(s.points_min_order, loyalty_setting('loyalty_min_order'));
    perform 1 from profiles where id = auth.uid() for update;          -- two orders at the same moment cannot spend the same points
    v_lb := loyalty_balance(auth.uid());
    if v_lb < v_min then raise exception 'points_min'; end if;
    v_cap := v_sub - v_disc - v_hdisc - v_promo;                       -- points never pay for delivery or the tip
    if v_cap < v_mo then raise exception 'points_min_order'; end if;  -- the order (dishes) must reach the minimum to use points
    v_pts := (floor(least(v_lb, floor(greatest(v_cap, 0) * v_rate)) / v_step) * v_step)::int;   -- whole vouchers only (1000, 2000 ...)
    if v_pts <= 0 or v_pts <> p_points then raise exception 'points_changed'; end if;   -- the customer saw another amount: ask again
    v_pval := round(v_pts / v_rate, 2);
    perform loyalty_spend(auth.uid(), v_pts, v_id);
    update orders set points_used = v_pts, points_value = v_pval,
      total = greatest(5, v_sub - v_disc - v_hdisc - v_promo - v_pval + v_fee + v_tip) where id = v_id;
  end if;

  -- WALLET: the customer may pay all or part of the order from his refund balance (the server decides the amount, never the app)
  if coalesce(p_wallet, 0) > 0 then
    select total into v_total from orders where id = v_id;
    perform 1 from profiles where id = auth.uid() for update;           -- two orders at the same moment cannot spend the same money
    v_bal := wallet_balance();
    v_w := round(least(p_wallet, v_bal, v_total), 2);
    if v_w <= 0 or abs(v_w - round(p_wallet, 2)) > 0.009 then raise exception 'wallet_changed'; end if;   -- the customer saw another amount: ask again
    insert into wallet_entries(user_id, amount, kind, order_id) values (auth.uid(), -v_w, 'spend', v_id);
    update orders set wallet_used = v_w, payment = case when v_w >= v_total then 'wallet' else payment end where id = v_id;
  end if;
  if v_gid is not null then update group_orders set status = 'placed', order_id = v_id, closed_at = coalesce(closed_at, now()) where id = v_gid; end if;
  return v_id;
end $function$
;
CREATE OR REPLACE FUNCTION public.price_line(p_item uuid, p_opts jsonb)
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_item menu_items; ids uuid[]; g record; o record; n int; total numeric := 0; snap jsonb := '[]'::jsonb;
begin
  select * into v_item from menu_items where id = p_item;
  if not found then raise exception 'unavailable'; end if;
  begin
    ids := array(select distinct t.x::uuid from jsonb_array_elements_text(coalesce(p_opts, '[]'::jsonb)) as t(x));
  exception when others then raise exception 'bad_options';
  end;
  if cardinality(ids) > 40 then raise exception 'bad_options'; end if;
  if exists (select 1 from unnest(ids) u(id)
              where not exists (select 1 from item_options op join item_option_groups gr on gr.id = op.group_id
                                 where op.id = u.id and gr.item_id = p_item and op.available)) then
    raise exception 'bad_options';
  end if;
  for g in select * from item_option_groups where item_id = p_item loop
    select count(*) into n from item_options op where op.group_id = g.id and op.id = any(ids);
    if n > g.max_sel or (g.required and n < 1) then raise exception 'bad_options'; end if;
  end loop;
  for o in select op.id, op.name, op.price_delta, gr.name as gname
             from item_options op join item_option_groups gr on gr.id = op.group_id
            where gr.item_id = p_item and op.id = any(ids) order by gr.sort, gr.created_at, op.sort, op.name loop
    total := total + o.price_delta;
    snap := snap || jsonb_build_array(jsonb_build_object('id', o.id, 'g', o.gname, 'n', o.name, 'p', o.price_delta));
  end loop;
  return jsonb_build_object('unit', v_item.price + total, 'snap', snap);
end $function$
;
CREATE OR REPLACE FUNCTION public.promo_eval(p_code text, p_base numeric, p_uid uuid, p_lock boolean DEFAULT false, p_gate numeric DEFAULT NULL::numeric)
 RETURNS numeric
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare c promo_codes; k text := upper(trim(coalesce(p_code, ''))); d numeric; n int;
begin
  if k !~ '^[A-Z0-9_-]{3,20}$' then raise exception 'promo_invalid'; end if;
  if p_lock then perform pg_advisory_xact_lock(hashtext('promo:' || k)); end if;
  select * into c from promo_codes
   where upper(code) = k and is_active
     and (starts_at is null or starts_at <= now()) and (ends_at is null or ends_at > now());
  if not found then raise exception 'promo_invalid'; end if;
  if coalesce(p_gate, p_base) < c.min_order then raise exception 'promo_min'; end if;
  if exists (select 1 from orders where customer_id = p_uid and promo_code = k and status not in ('rejected', 'cancelled')) then
    raise exception 'promo_used';
  end if;
  if c.max_uses is not null then
    select count(*) into n from orders where promo_code = k and status not in ('rejected', 'cancelled');
    if n >= c.max_uses then raise exception 'promo_limit'; end if;
  end if;
  d := case c.kind when 'percent' then round(p_base * c.value / 100, 2) else least(c.value, p_base) end;
  return greatest(0, least(d, p_base));
end $function$
;
CREATE OR REPLACE FUNCTION public.promo_guard_version()
 RETURNS integer
 LANGUAGE sql
 STABLE
AS $function$ select 30 $function$
;
CREATE OR REPLACE FUNCTION public.rate_order(p_order bigint, p_store integer, p_driver integer, p_comment text DEFAULT NULL::text)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare o orders;
begin
  if auth.uid() is null then raise exception 'auth'; end if;
  select * into o from orders where id = p_order and customer_id = auth.uid() and status = 'delivered';
  if not found then raise exception 'not_allowed'; end if;
  if (p_store is not null and p_store not between 1 and 5) or (p_driver is not null and p_driver not between 1 and 5)
     or (p_store is null and p_driver is null) then raise exception 'bad_value'; end if;
  if o.driver_id is null then p_driver := null; end if;
  insert into ratings(order_id, customer_id, store_id, driver_id, store_stars, driver_stars, comment)
  values (p_order, auth.uid(), o.store_id, o.driver_id, p_store, p_driver, nullif(left(btrim(coalesce(p_comment, '')), 300), ''));
exception when unique_violation then
  raise exception 'already_rated';
end $function$
;
CREATE OR REPLACE FUNCTION public.reject_order(p_id bigint, p_reason text, p_note text DEFAULT NULL::text)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare o orders;
begin
  if p_reason is null or p_reason not in ('out_of_stock', 'too_busy', 'closing', 'other') then raise exception 'bad_value'; end if;
  if p_reason = 'other' and char_length(btrim(coalesce(p_note, ''))) < 3 then raise exception 'note_required'; end if;
  select * into o from orders where id = p_id for update;
  if not found then raise exception 'not_found'; end if;
  if not owns_store(o.store_id) then raise exception 'not_allowed'; end if;
  if o.status not in ('pending', 'preparing') then raise exception 'bad_transition'; end if;
  update orders set status = 'rejected', done_at = now(), cancel_reason = p_reason,
    cancel_note = nullif(left(btrim(coalesce(p_note, '')), 200), ''), cancelled_by = 'store'
  where id = p_id;
end $function$
;
CREATE OR REPLACE FUNCTION public.reopen_rating(p_order bigint)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if not has_perm('support') then raise exception 'not_allowed'; end if;
  update ratings set handled_at = null, handled_by = null, handled_note = null where order_id = p_order;
end $function$
;
CREATE OR REPLACE FUNCTION public.report_client_error(p_app text, p_message text, p_context text DEFAULT NULL::text, p_ua text DEFAULT NULL::text)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if auth.uid() is null then return; end if;
  if (select count(*) from client_errors where user_id = auth.uid() and at > now() - interval '1 hour') >= 10 then return; end if;
  delete from client_errors where at < now() - interval '30 days';
  insert into client_errors(user_id, app, message, context, ua)
  values (auth.uid(), left(coalesce(p_app, ''), 20), left(coalesce(p_message, ''), 300), left(coalesce(p_context, ''), 300), left(coalesce(p_ua, ''), 160));
end $function$
;
CREATE OR REPLACE FUNCTION public.request_store(p_name text, p_category text, p_phone text, p_address text, p_lat double precision, p_lng double precision, p_note text DEFAULT NULL::text)
 RETURNS uuid
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_id uuid; v_ph text := norm_phone(p_phone); v_name text := btrim(coalesce(p_name, ''));
begin
  if auth.uid() is null then raise exception 'auth'; end if;
  if not exists (select 1 from profiles where id = auth.uid() and role = 'merchant') then raise exception 'not_allowed'; end if;
  if char_length(v_name) < 2 or char_length(v_name) > 80 or p_category not in ('rest','grocery','pharmacy','beauty','flowers','gifts','shops','sweets') then raise exception 'bad_value'; end if;
  if v_ph is null then raise exception 'bad_phone'; end if;
  if p_lat is null or p_lng is null or p_lat not between -90 and 90 or p_lng not between -180 and 180 then raise exception 'bad_value'; end if;
  if char_length(coalesce(p_address, '')) > 200 or char_length(coalesce(p_note, '')) > 500 then raise exception 'bad_value'; end if;
  if (select count(*) from store_requests where user_id = auth.uid() and status = 'pending') >= 3
     or (select count(*) from store_requests where user_id = auth.uid() and created_at > now() - interval '1 day') >= 5 then
    raise exception 'too_many';
  end if;
  insert into store_requests(user_id, name, category, phone, address, lat, lng, note)
  values (auth.uid(), v_name, p_category, v_ph, nullif(btrim(coalesce(p_address, '')), ''), p_lat, p_lng, nullif(btrim(coalesce(p_note, '')), ''))
  returning id into v_id;
  return v_id;
end $function$
;
CREATE OR REPLACE FUNCTION public.resolve_rating(p_order bigint, p_note text DEFAULT NULL::text)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if not has_perm('support') then raise exception 'not_allowed'; end if;
  update ratings set handled_at = now(), handled_by = auth.uid(), handled_note = nullif(left(btrim(coalesce(p_note, '')), 300), '')
   where order_id = p_order and handled_at is null;
  if not found then raise exception 'not_found'; end if;
end $function$
;
CREATE OR REPLACE FUNCTION public.set_customer_ban(p_id uuid, p_banned boolean, p_reason text DEFAULT NULL::text)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_reason text := nullif(left(btrim(coalesce(p_reason, '')), 200), '');
begin
  if not has_perm('support') then raise exception 'not_allowed'; end if;
  if not exists (select 1 from profiles where id = p_id and role = 'customer') then raise exception 'not_found'; end if;
  if coalesce(p_banned, false) and (v_reason is null or char_length(v_reason) < 3) then raise exception 'note_required'; end if;
  perform set_config('app.bypass', '1', true);   -- guard_profile blocks non-admins; this function has already checked the permission and the target
  update profiles set banned_at = case when coalesce(p_banned, false) then now() end,
                      banned_reason = case when coalesce(p_banned, false) then v_reason end where id = p_id;
  perform set_config('app.bypass', '', true);
end $function$
;
CREATE OR REPLACE FUNCTION public.set_default_address(p_id uuid)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if auth.uid() is null then raise exception 'auth'; end if;
  if not exists (select 1 from addresses where id = p_id and user_id = auth.uid()) then raise exception 'not_allowed'; end if;
  update addresses set is_default = false where user_id = auth.uid() and is_default and id <> p_id;
  update addresses set is_default = true where id = p_id and user_id = auth.uid();
end $function$
;
CREATE OR REPLACE FUNCTION public.set_my_cashback(p_store uuid, p_pct numeric)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if not exists (select 1 from stores where id = p_store and owner_id = auth.uid()) then raise exception 'not_allowed'; end if;
  if p_pct is null or p_pct not between 0 and 50 then raise exception 'bad_value'; end if;
  update stores set cashback_pct = round(p_pct, 1) where id = p_store;
end $function$
;
CREATE OR REPLACE FUNCTION public.set_my_discount(p_store text, p_pct numeric)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare mx numeric;
begin
  if auth.uid() is null then raise exception 'auth'; end if;
  select max_discount_pct into mx from stores
   where id::text = p_store and owner_id = auth.uid() for update;
  if not found then raise exception 'not_allowed'; end if;
  if p_pct is null or p_pct < 0 or p_pct > 100 then raise exception 'bad_value'; end if;
  if p_pct > mx then raise exception 'discount_over_max'; end if;
  perform set_config('app.bypass', '1', true);
  update stores set discount_pct = p_pct where id::text = p_store and owner_id = auth.uid();
  perform set_config('app.bypass', '', true);
end $function$
;
CREATE OR REPLACE FUNCTION public.set_my_free_delivery(p_store uuid, p_min numeric)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if not exists (select 1 from stores where id = p_store and owner_id = auth.uid()) then raise exception 'not_allowed'; end if;
  if p_min is null or p_min not between 0 and 100000 then raise exception 'bad_value'; end if;
  update stores set free_delivery_min = round(p_min, 2) where id = p_store;
end $function$
;
CREATE OR REPLACE FUNCTION public.set_my_phone(p_phone text)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_p text := norm_phone(p_phone);
begin
  if auth.uid() is null then raise exception 'auth'; end if;
  if v_p is null then raise exception 'bad_phone'; end if;
  update profiles set phone = v_p where id = auth.uid();
end $function$
;
CREATE OR REPLACE FUNCTION public.set_order_status(p_id bigint, p_to order_status)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare o orders; ok boolean := false;
begin
  select * into o from orders where id = p_id for update;
  if not found then raise exception 'not_found'; end if;
  if is_admin() then ok := true;
  elsif has_perm('orders') and p_to in ('cancelled','rejected') then ok := o.status in ('pending','preparing','ready','pickedup');
  elsif o.customer_id = auth.uid() then ok := (o.status = 'pending' and p_to = 'cancelled');
  elsif owns_store(o.store_id) then
    ok := (o.status = 'pending' and p_to in ('preparing','rejected')) or (o.status = 'preparing' and p_to = 'ready');
    -- a scheduled order is prepared at most 60 minutes before its time (v51)
    if ok and p_to = 'preparing' and o.scheduled_for is not null and now() < o.scheduled_for - interval '60 minutes' then raise exception 'too_early'; end if;
  elsif o.driver_id = auth.uid() then
    ok := (o.status = 'ready' and p_to = 'pickedup');
  end if;
  if not ok then raise exception 'bad_transition'; end if;
  update orders set status = p_to,
    done_at = case when p_to in ('delivered','rejected','cancelled') then now() else null end where id = p_id;
end $function$
;
CREATE OR REPLACE FUNCTION public.set_page(p_slug text, p_lang text, p_body text)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_b text := coalesce(p_body, '');
begin
  if not has_perm('content') then raise exception 'not_allowed'; end if;
  if p_slug not in ('about', 'privacy') or p_lang not in ('ru', 'en') or char_length(v_b) > 20000 then raise exception 'bad_value'; end if;
  if p_lang = 'ru' then
    update app_pages set body_ru = v_b, updated_at = now(), updated_by = auth.uid() where slug = p_slug;
  else
    update app_pages set body_en = v_b, updated_at = now(), updated_by = auth.uid() where slug = p_slug;
  end if;
end $function$
;
CREATE OR REPLACE FUNCTION public.set_prep_time(p_id bigint, p_min integer)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if not exists(select 1 from orders o where o.id = p_id and o.status in ('pending','preparing')
                and (owns_store(o.store_id) or has_perm('orders'))) then
    raise exception 'not_allowed';
  end if;
  update orders set prep_time = least(90, greatest(5, p_min)) where id = p_id;
end $function$
;
CREATE OR REPLACE FUNCTION public.set_setting(p_key text, p_value numeric)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if not is_admin() then raise exception 'not_allowed'; end if;
  if p_value is null
     or (p_key = 'delivery_free_km' and p_value not between 0 and 50)
     or (p_key = 'delivery_step_km' and p_value not between 0.1 and 5)
     or (p_key = 'delivery_step_price' and p_value not between 0 and 1000)
     or (p_key = 'delivery_max_km' and p_value not between 1 and 100)
     or (p_key = 'delivery_road_factor' and p_value not between 1 and 3)
     or (p_key = 'loyalty_earn_per_tjs' and (p_value not between 0 and 1000 or p_value <> trunc(p_value)))
     or (p_key = 'loyalty_points_per_tjs' and (p_value not between 1 and 100000 or p_value <> trunc(p_value)))
     or (p_key = 'loyalty_min_redeem' and (p_value not between 0 and 1000000 or p_value <> trunc(p_value)))
     or (p_key = 'loyalty_expiry_days' and (p_value not between 1 and 3650 or p_value <> trunc(p_value)))
     or (p_key = 'cashback_pct' and p_value not between 0 and 50)
     or (p_key = 'loyalty_voucher_points' and (p_value not between 1 and 1000000 or p_value <> trunc(p_value)))
     or (p_key = 'loyalty_min_order' and p_value not between 0 and 10000)
     or (p_key = 'loyalty_rate_reward' and (p_value not between 0 and 10000 or p_value <> trunc(p_value))) then
    raise exception 'bad_value';
  end if;
  update app_settings set value = p_value, updated_at = now(), updated_by = auth.uid() where key = p_key;
  if not found then raise exception 'bad_value'; end if;
end $function$
;
CREATE OR REPLACE FUNCTION public.set_store_earn(p_store uuid, p_earn numeric)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if not (is_admin() or has_perm('stores')) then raise exception 'not_allowed'; end if;
  if p_earn is not null and (p_earn not between 0 and 1000 or p_earn <> trunc(p_earn)) then raise exception 'bad_value'; end if;
  update stores set earn_per_tjs = p_earn where id = p_store;
  if not found then raise exception 'not_found'; end if;
end $function$
;
CREATE OR REPLACE FUNCTION public.set_store_free_delivery(p_store uuid, p_min numeric)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if not (is_admin() or has_perm('stores')) then raise exception 'not_allowed'; end if;
  if p_min is null or p_min not between 0 and 100000 then raise exception 'bad_value'; end if;
  update stores set free_delivery_min = round(p_min, 2) where id = p_store;
  if not found then raise exception 'not_found'; end if;
end $function$
;
CREATE OR REPLACE FUNCTION public.set_store_loyalty(p_store uuid, p_min_order numeric, p_cashback numeric)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if not (is_admin() or has_perm('stores')) then raise exception 'not_allowed'; end if;
  if (p_min_order is not null and p_min_order not between 0 and 10000) or (p_cashback is not null and p_cashback not between 0 and 50) then raise exception 'bad_value'; end if;
  update stores set points_min_order = p_min_order, cashback_pct = p_cashback where id = p_store;
  if not found then raise exception 'not_found'; end if;
end $function$
;
CREATE OR REPLACE FUNCTION public.set_store_open(p_store uuid, p_open boolean)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if not (owns_store(p_store) or has_perm('stores')) then raise exception 'not_allowed'; end if;
  update stores set is_open = p_open where id = p_store;
end $function$
;
CREATE OR REPLACE FUNCTION public.set_text_setting(p_key text, p_value text)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_v text := btrim(coalesce(p_value, ''));
begin
  if not has_perm('content') then raise exception 'not_allowed'; end if;
  if p_key = 'support_phone' then
    if v_v <> '' then v_v := norm_phone(v_v); if v_v is null then raise exception 'bad_phone'; end if; end if;
  elsif p_key = 'support_hours' then
    if char_length(v_v) > 60 then raise exception 'bad_value'; end if;
  else raise exception 'bad_value';
  end if;
  update app_texts set value = v_v, updated_at = now(), updated_by = auth.uid() where key = p_key;
end $function$
;
CREATE OR REPLACE FUNCTION public.settle_driver_cash(p_driver uuid)
 RETURNS numeric
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare tot numeric;
begin
  if not has_perm('finance') then raise exception 'not_allowed'; end if;
  select coalesce(sum(cash_collected), 0) into tot from orders
   where driver_id = p_driver and status = 'delivered' and cash_collected is not null and cash_settled_at is null;
  update orders set cash_settled_at = now()
   where driver_id = p_driver and status = 'delivered' and cash_collected is not null and cash_settled_at is null;
  return tot;
end $function$
;
CREATE OR REPLACE FUNCTION public.staff_list()
 RETURNS TABLE(user_id uuid, email text, name text, perms text[], active boolean, created_at timestamp with time zone)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  select s.user_id, u.email::text, p.name, s.perms, s.active, s.created_at
    from staff_members s join profiles p on p.id = s.user_id left join auth.users u on u.id = s.user_id
   where is_admin() order by s.created_at
$function$
;
CREATE OR REPLACE FUNCTION public.staff_remove(p_user uuid)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if not is_admin() then raise exception 'not_allowed'; end if;
  delete from staff_members where user_id = p_user;
  if not found then raise exception 'not_found'; end if;
  insert into audit_log(user_id, action, table_name, row_id, details) values (auth.uid(), 'STAFF_REMOVE', 'staff_members', p_user::text, '{}'::jsonb);
end $function$
;
CREATE OR REPLACE FUNCTION public.staff_set(p_email text, p_perms text[], p_active boolean DEFAULT true)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare u uuid; v_role user_role; v_perms text[];
begin
  if not is_admin() then raise exception 'not_allowed'; end if;
  if coalesce(btrim(p_email), '') = '' or char_length(p_email) > 120 or p_email !~ '^[^@\s]+@[^@\s]+\.[^@\s]+$' then raise exception 'bad_value'; end if;
  select array(select distinct x from unnest(coalesce(p_perms, '{}')) x order by x) into v_perms;
  if not (v_perms <@ array['orders','support','finance','stores','content']::text[]) then raise exception 'bad_value'; end if;
  if cardinality(v_perms) = 0 and coalesce(p_active, true) then raise exception 'bad_value'; end if;
  select id into u from auth.users where lower(email) = lower(btrim(p_email));
  if u is null then raise exception 'user_not_found'; end if;
  select role into v_role from profiles where id = u;
  if v_role is null then raise exception 'user_not_found'; end if;
  if v_role = 'admin' then raise exception 'bad_value'; end if;                      -- admins already have everything
  if u = auth.uid() then raise exception 'bad_value'; end if;
  if (select count(*) from staff_members) >= 30 and not exists(select 1 from staff_members where user_id = u) then raise exception 'too_many'; end if;
  insert into staff_members(user_id, perms, active, created_by) values (u, v_perms, coalesce(p_active, true), auth.uid())
  on conflict (user_id) do update set perms = excluded.perms, active = excluded.active;
  insert into audit_log(user_id, action, table_name, row_id, details)
  values (auth.uid(), 'STAFF_SET', 'staff_members', u::text, jsonb_build_object('perms', v_perms, 'active', coalesce(p_active, true)));
end $function$
;
CREATE OR REPLACE FUNCTION public.store_owner_info(p_store uuid)
 RETURNS TABLE(owner_id uuid, name text, email text)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  select p.id, p.name, u.email::text
    from stores s join profiles p on p.id = s.owner_id join auth.users u on u.id = p.id
   where s.id = p_store and is_admin()
$function$
;
CREATE OR REPLACE FUNCTION public.store_private()
 RETURNS TABLE(id uuid, owner_id uuid, commission_pct numeric, max_discount_pct numeric)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  select s.id, s.owner_id, s.commission_pct, s.max_discount_pct
    from stores s where has_perm('stores') or s.owner_id = auth.uid()
$function$
;
CREATE OR REPLACE FUNCTION public.store_speed()
 RETURNS TABLE(store_id uuid, avg_min numeric, n integer)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  select o.store_id, round(avg(extract(epoch from r.at - p.at) / 60)::numeric, 1), count(*)::int
    from orders o
    join lateral (select min(at) as at from order_events e where e.order_id = o.id and e.kind = 'preparing') p on p.at is not null
    join lateral (select min(at) as at from order_events e where e.order_id = o.id and e.kind = 'ready') r on r.at is not null
   where o.created_at > now() - interval '30 days' and r.at > p.at
   group by o.store_id
$function$
;
CREATE OR REPLACE FUNCTION public.ticket_reason_ok(p_status text, p_reason text, p_has_order boolean)
 RETURNS boolean
 LANGUAGE sql
 IMMUTABLE
AS $function$
  select case
    when not p_has_order then p_reason in ('courier', 'restaurant', 'payment', 'other')
    when p_status in ('pending', 'preparing', 'ready', 'pickedup') then p_reason in ('late', 'courier', 'restaurant', 'payment', 'other')
    when p_status = 'delivered' then p_reason in ('not_delivered', 'wrong_order', 'missing_items', 'quality', 'late', 'courier', 'restaurant', 'payment', 'other')
    else p_reason in ('restaurant', 'payment', 'other')
  end
$function$
;
CREATE OR REPLACE FUNCTION public.ticket_refund_room(p_ticket bigint)
 RETURNS TABLE(order_total numeric, refunded numeric, room numeric)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  select o.total,
         coalesce(w.sum_refunded, 0),
         greatest(0, o.total - coalesce(w.sum_refunded, 0))
    from support_tickets t
    join orders o on o.id = t.order_id
    left join lateral (select sum(x.amount) as sum_refunded from wallet_entries x where x.order_id = o.id and x.kind = 'refund') w on true
   where t.id = p_ticket and has_perm('support')
$function$
;
CREATE OR REPLACE FUNCTION public.ticket_reply(p_ticket bigint, p_body text)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_t support_tickets; v_body text := btrim(coalesce(p_body, ''));
begin
  if auth.uid() is null then raise exception 'auth'; end if;
  if char_length(v_body) < 1 or char_length(v_body) > 500 then raise exception 'bad_value'; end if;
  select * into v_t from support_tickets where id = p_ticket and customer_id = auth.uid();
  if not found then raise exception 'not_allowed'; end if;
  if v_t.status in ('resolved', 'rejected') then raise exception 'ticket_closed'; end if;
  if (select count(*) from ticket_messages where ticket_id = p_ticket and sender_id = auth.uid() and created_at > now() - interval '1 hour') >= 20 then
    raise exception 'too_many';
  end if;
  insert into ticket_messages(ticket_id, from_staff, sender_id, body) values (p_ticket, false, auth.uid(), v_body);
  update support_tickets set updated_at = now(), last_customer_at = now(), customer_seen_at = now() where id = p_ticket;
end $function$
;
CREATE OR REPLACE FUNCTION public.ticket_seen(p_ticket bigint)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if auth.uid() is null then raise exception 'auth'; end if;
  update support_tickets set customer_seen_at = now() where id = p_ticket and customer_id = auth.uid();
end $function$
;
CREATE OR REPLACE FUNCTION public.ticket_set_status(p_ticket bigint, p_status text, p_note text DEFAULT NULL::text, p_refund numeric DEFAULT NULL::numeric)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_t support_tickets; v_max numeric; v_cred numeric; v_prev numeric; v_ref numeric := case when p_refund is null then null else round(p_refund, 2) end;
begin
  if not has_perm('support') then raise exception 'not_allowed'; end if;
  if p_status not in ('open', 'in_progress', 'resolved', 'rejected') then raise exception 'bad_value'; end if;
  if p_status = 'rejected' and char_length(btrim(coalesce(p_note, ''))) < 3 then raise exception 'note_required'; end if;   -- the customer must be told why
  select * into v_t from support_tickets where id = p_ticket;
  if not found then raise exception 'not_found'; end if;
  select amount into v_cred from wallet_entries where ticket_id = p_ticket and kind = 'refund';
  if v_ref is not null then
    if p_status <> 'resolved' or v_ref < 0 then raise exception 'bad_value'; end if;
    if v_ref > 0 and v_cred is not null then raise exception 'already_refunded'; end if;   -- one refund per ticket
    if v_ref > 0 and v_t.order_id is null then raise exception 'refund_needs_order'; end if;  -- a refund needs an order to be measured against
    if v_t.order_id is not null then
      select total into v_max from orders where id = v_t.order_id;
      select coalesce(sum(amount), 0) into v_prev from wallet_entries where order_id = v_t.order_id and kind = 'refund';
      if v_ref + v_prev > coalesce(v_max, 0) then raise exception 'refund_too_high'; end if;   -- never more than the order was worth, over all its tickets
    end if;
  end if;
  update support_tickets set status = p_status,
         admin_note = nullif(left(btrim(coalesce(p_note, '')), 300), ''),
         refund_amount = coalesce(v_cred, case when p_status = 'resolved' and v_ref > 0 then v_ref end),
         updated_at = now(), last_staff_at = now(), handled_by = auth.uid(),
         closed_at = case when p_status in ('resolved', 'rejected') then now() else null end
   where id = p_ticket;
  -- the approved refund goes to the customer's wallet in the same moment (atomic with closing the ticket)
  if v_ref > 0 and v_cred is null then
    insert into wallet_entries(user_id, amount, kind, ticket_id, order_id, note, created_by)
    values (v_t.customer_id, v_ref, 'refund', p_ticket, v_t.order_id, left(coalesce(p_note, ''), 200), auth.uid());
  end if;
end $function$
;
CREATE OR REPLACE FUNCTION public.ticket_staff_reply(p_ticket bigint, p_body text)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_t support_tickets; v_body text := btrim(coalesce(p_body, ''));
begin
  if not has_perm('support') then raise exception 'not_allowed'; end if;
  if char_length(v_body) < 1 or char_length(v_body) > 500 then raise exception 'bad_value'; end if;
  select * into v_t from support_tickets where id = p_ticket;
  if not found then raise exception 'not_found'; end if;
  if v_t.status in ('resolved', 'rejected') then raise exception 'ticket_closed'; end if;
  insert into ticket_messages(ticket_id, from_staff, sender_id, body) values (p_ticket, true, auth.uid(), v_body);
  update support_tickets set updated_at = now(), last_staff_at = now(), handled_by = auth.uid(),
         status = case when status = 'open' then 'in_progress' else status end where id = p_ticket;
end $function$
;
CREATE OR REPLACE FUNCTION public.trg_chat_limit()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if (select count(*) from order_chat where sender_id = new.sender_id and created_at > now() - interval '1 minute') >= 20 then
    raise exception 'too_many';
  end if;
  return new;
end $function$
;
CREATE OR REPLACE FUNCTION public.trg_check_images()
 RETURNS trigger
 LANGUAGE plpgsql
 SET search_path TO 'public'
AS $function$
declare v_n jsonb := to_jsonb(new); v_o jsonb := case when tg_op = 'UPDATE' then to_jsonb(old) else '{}'::jsonb end; v_k text;
begin
  foreach v_k in array array['image_url', 'cover_url', 'logo_url'] loop
    if v_n ? v_k and (v_n->>v_k) is distinct from (v_o->>v_k) and not check_image_url(v_n->>v_k) then
      raise exception 'bad_value';
    end if;
  end loop;
  return new;
end $function$
;
CREATE OR REPLACE FUNCTION public.trg_dispatch()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if new.status = 'preparing' and old.status is distinct from 'preparing' and new.driver_id is null then
    perform dispatch_next(new.id);
  elsif new.status in ('rejected', 'cancelled', 'delivered') then
    update order_offers set state = 'cancelled' where order_id = new.id and state = 'pending';
  end if;
  return new;
end $function$
;
CREATE OR REPLACE FUNCTION public.trg_fav_limit()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if (select count(*) from favorites where user_id = new.user_id) >= 200 then raise exception 'bad_value'; end if;
  return new;
end $function$
;
CREATE OR REPLACE FUNCTION public.trg_loyalty()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_paid numeric; v_pts int; v_cb numeric;
begin
  if new.status = 'delivered' and old.status <> 'delivered' and new.loyalty_done_at is null then
    v_paid := greatest(0, coalesce(new.subtotal, 0) - coalesce(new.discount, 0) - coalesce(new.promo_discount, 0) - coalesce(new.points_value, 0));
    v_pts := ceil(v_paid * coalesce((select earn_per_tjs from stores where id = new.store_id), loyalty_setting('loyalty_earn_per_tjs')) - 0.000001)::int;   -- fractions in favour of the customer
    if v_pts > 0 then
      insert into loyalty_lots(user_id, points, points_left, expires_at, order_id, kind)
      values (new.customer_id, v_pts, v_pts, now() + make_interval(days => loyalty_setting('loyalty_expiry_days')::int), new.id, 'earn')
      on conflict (order_id) where kind = 'earn' do nothing;
      insert into loyalty_ledger(user_id, points, kind, order_id) values (new.customer_id, v_pts, 'earn', new.id);
    end if;
    v_cb := round(v_paid * coalesce((select cashback_pct from stores where id = new.store_id), loyalty_setting('cashback_pct')) / 100, 2);   -- the restaurant's own % (it pays it)
    if v_cb > 0 then
      insert into wallet_entries(user_id, amount, kind, order_id, note) values (new.customer_id, v_cb, 'cashback', new.id, null)
      on conflict (order_id) where kind = 'cashback' do nothing;
    end if;
    new.points_earned := greatest(v_pts, 0); new.cashback := greatest(v_cb, 0); new.loyalty_done_at := now();
  end if;
  if new.status in ('rejected', 'cancelled') and old.status not in ('rejected', 'cancelled')
     and coalesce(new.points_used, 0) > 0 and new.points_returned_at is null then
    insert into loyalty_lots(user_id, points, points_left, expires_at, order_id, kind)
    values (new.customer_id, new.points_used, new.points_used, now() + make_interval(days => loyalty_setting('loyalty_expiry_days')::int), new.id, 'return')
    on conflict (order_id) where kind = 'return' do nothing;
    insert into loyalty_ledger(user_id, points, kind, order_id) values (new.customer_id, new.points_used, 'return', new.id);
    new.points_returned_at := now();
  end if;
  return new;
end $function$
;
CREATE OR REPLACE FUNCTION public.trg_profile_phone()
 RETURNS trigger
 LANGUAGE plpgsql
 SET search_path TO 'public'
AS $function$
declare v_p text;
  -- NULL-safe on purpose: current_setting(..., true) is NULL when the setting was never set, and (false OR NULL OR false) is NULL,
  -- which made "not v_free" NULL and silently switched every rule below OFF.
  v_free boolean := (auth.uid() is null) or (coalesce(current_setting('app.bypass', true), '') = '1') or coalesce(is_admin(), false);
begin
  if new.phone is distinct from old.phone then
    if new.phone is null or btrim(new.phone) = '' then
      if old.phone is not null and not v_free then raise exception 'bad_phone'; end if;   -- cannot erase the number to dodge the rules
      new.phone := null; return new;
    end if;
    v_p := norm_phone(new.phone);
    if v_p is null then raise exception 'bad_phone'; end if;
    new.phone := v_p;
    if v_p is distinct from old.phone and old.phone is not null and not v_free and new.role = 'customer' then
      if exists (select 1 from orders where customer_id = new.id and status in ('pending', 'preparing', 'ready', 'pickedup')) then
        raise exception 'phone_locked';
      end if;
      if old.phone_changed_at is not null and old.phone_changed_at > now() - interval '30 days' then
        raise exception 'phone_cooldown';
      end if;
      new.phone_changed_at := now();
    end if;
  end if;
  return new;
end $function$
;
CREATE OR REPLACE FUNCTION public.trg_rating_aggregate()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  perform set_config('app.bypass', '1', true);
  update stores set
    app_rating = (select round(avg(r.store_stars)::numeric, 1) from ratings r where r.store_id = new.store_id and r.store_stars is not null),
    app_rating_count = (select count(r.store_stars) from ratings r where r.store_id = new.store_id)
  where id = new.store_id;
  return new;
end $function$
;
CREATE OR REPLACE FUNCTION public.trg_rating_reward()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_pts int := loyalty_setting('loyalty_rate_reward')::int; v_id bigint;
begin
  if v_pts > 0 and new.customer_id is not null and new.order_id is not null then
    insert into loyalty_lots(user_id, points, points_left, expires_at, order_id, kind)
    values (new.customer_id, v_pts, v_pts, now() + make_interval(days => loyalty_setting('loyalty_expiry_days')::int), new.order_id, 'reward')
    on conflict (order_id) where kind = 'reward' do nothing returning id into v_id;
    if v_id is not null then insert into loyalty_ledger(user_id, points, kind, order_id) values (new.customer_id, v_pts, 'reward', new.order_id); end if;
  end if;
  return new;
end $function$
;
CREATE OR REPLACE FUNCTION public.trg_store_phone()
 RETURNS trigger
 LANGUAGE plpgsql
 SET search_path TO 'public'
AS $function$
declare v_p text;
begin
  if new.phone is null or btrim(new.phone) = '' then new.phone := null; return new; end if;
  if tg_op = 'INSERT' or new.phone is distinct from old.phone then
    v_p := norm_phone(new.phone);
    if v_p is null then raise exception 'bad_phone'; end if;
    new.phone := v_p;
  end if;
  return new;
end $function$
;
CREATE OR REPLACE FUNCTION public.trg_wallet_immutable()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
begin
  raise exception 'ledger_immutable';
end $function$
;
CREATE OR REPLACE FUNCTION public.trg_wallet_return()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if new.status in ('rejected', 'cancelled') and old.status not in ('rejected', 'cancelled')
     and coalesce(new.wallet_used, 0) > 0 and new.wallet_returned_at is null then
    insert into wallet_entries(user_id, amount, kind, order_id) values (new.customer_id, new.wallet_used, 'return', new.id)
    on conflict (order_id) where kind = 'return' do nothing;
    new.wallet_returned_at := now();
  end if;
  return new;
end $function$
;
CREATE OR REPLACE FUNCTION public.update_my_store(p_store uuid, p_description text, p_cover text, p_logo text DEFAULT NULL::text)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if not (owns_store(p_store) or has_perm('stores')) then raise exception 'not_allowed'; end if;
  if (p_cover is not null and char_length(p_cover) > 700000) or (p_logo is not null and char_length(p_logo) > 700000) then
    raise exception 'bad_value';
  end if;
  update stores
     set description = left(coalesce(p_description, description), 300),
         cover_url   = coalesce(p_cover, cover_url),
         logo_url    = coalesce(p_logo, logo_url)
   where id = p_store;
end $function$
;
CREATE OR REPLACE FUNCTION public.validate_item()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare mx numeric;
begin
  if char_length(new.name) > 80 then raise exception 'bad_value'; end if;
  if new.discount_pct > 0 then
    select max_discount_pct into mx from stores where id = new.store_id;
    if mx is null or new.discount_pct > mx then raise exception 'discount_over_max'; end if;
  end if;
  return new;
end $function$
;
CREATE OR REPLACE FUNCTION public.validate_store()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if new.commission_pct is not null and (new.commission_pct < 0 or new.commission_pct > 100) then raise exception 'bad_value'; end if;
  if coalesce(new.discount_pct, 0) < 0 or coalesce(new.discount_pct, 0) > 100 then raise exception 'bad_value'; end if;
  if new.max_discount_pct < 0 or new.max_discount_pct > 100 then raise exception 'bad_value'; end if;
  if coalesce(new.fee_base, 0) < 0 or coalesce(new.fee_per_km, 0) < 0 then raise exception 'bad_value'; end if;
  if (new.lat is null) <> (new.lng is null) then raise exception 'bad_value'; end if;
  if new.lat is not null and (new.lat < -90 or new.lat > 90 or new.lng < -180 or new.lng > 180) then raise exception 'bad_value'; end if;
  if coalesce(new.discount_pct, 0) > new.max_discount_pct then raise exception 'discount_over_max'; end if;

  -- Only the admin (or the set_my_discount function below) may change discount / cap / commission
  if tg_op = 'UPDATE' and auth.uid() is not null and not is_admin()
     and current_setting('app.bypass', true) is distinct from '1' then
    if new.discount_pct is distinct from old.discount_pct
       or new.max_discount_pct is distinct from old.max_discount_pct
       or new.commission_pct is distinct from old.commission_pct then
      raise exception 'not_allowed';
    end if;
  end if;
  return new;
end $function$
;
CREATE OR REPLACE FUNCTION public.wallet_adjust(p_user uuid, p_amount numeric, p_note text)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_a numeric := round(coalesce(p_amount, 0), 2); v_note text := btrim(coalesce(p_note, ''));
begin
  if not has_perm('finance') then raise exception 'not_allowed'; end if;
  if v_a = 0 or abs(v_a) > 100000 or char_length(v_note) < 3 or char_length(v_note) > 200 then raise exception 'bad_value'; end if;
  perform 1 from profiles where id = p_user and role = 'customer' for update;
  if not found then raise exception 'not_found'; end if;
  if v_a < 0 and wallet_balance(p_user) + v_a < 0 then raise exception 'insufficient_funds'; end if;
  insert into wallet_entries(user_id, amount, kind, note, created_by) values (p_user, v_a, 'adjust', v_note, auth.uid());
end $function$
;
CREATE OR REPLACE FUNCTION public.wallet_balance(p_user uuid DEFAULT NULL::uuid)
 RETURNS numeric
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  select coalesce(sum(w.amount), 0)::numeric
    from wallet_entries w
   where w.user_id = coalesce(p_user, auth.uid())
     and (coalesce(p_user, auth.uid()) = auth.uid() or (has_perm('support') or has_perm('finance')))
$function$
;
CREATE UNIQUE INDEX IF NOT EXISTS promo_guess_pkey ON public.promo_guess USING btree (id);
CREATE INDEX IF NOT EXISTS promo_guess_user_at_idx ON public.promo_guess USING btree (user_id, at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS loyalty_lots_pkey ON public.loyalty_lots USING btree (id);
CREATE INDEX IF NOT EXISTS loyalty_lots_user_idx ON public.loyalty_lots USING btree (user_id, expires_at) WHERE (points_left > 0);
CREATE UNIQUE INDEX IF NOT EXISTS loyalty_one_earn_per_order ON public.loyalty_lots USING btree (order_id) WHERE (kind = 'earn'::text);
CREATE UNIQUE INDEX IF NOT EXISTS loyalty_one_return_per_order ON public.loyalty_lots USING btree (order_id) WHERE (kind = 'return'::text);
CREATE UNIQUE INDEX IF NOT EXISTS loyalty_one_reward_per_order ON public.loyalty_lots USING btree (order_id) WHERE (kind = 'reward'::text);
CREATE UNIQUE INDEX IF NOT EXISTS loyalty_ledger_pkey ON public.loyalty_ledger USING btree (id);
CREATE INDEX IF NOT EXISTS loyalty_ledger_user_idx ON public.loyalty_ledger USING btree (user_id, created_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS happy_hours_pkey ON public.happy_hours USING btree (id);
CREATE INDEX IF NOT EXISTS happy_hours_active_idx ON public.happy_hours USING btree (active, store_id);
CREATE UNIQUE INDEX IF NOT EXISTS brands_pkey ON public.brands USING btree (id);
CREATE UNIQUE INDEX IF NOT EXISTS item_option_groups_pkey ON public.item_option_groups USING btree (id);
CREATE INDEX IF NOT EXISTS iog_item_idx ON public.item_option_groups USING btree (item_id);
CREATE UNIQUE INDEX IF NOT EXISTS item_options_pkey ON public.item_options USING btree (id);
CREATE INDEX IF NOT EXISTS io_group_idx ON public.item_options USING btree (group_id);
CREATE UNIQUE INDEX IF NOT EXISTS orders_pkey ON public.orders USING btree (id);
CREATE INDEX IF NOT EXISTS orders_customer_idx ON public.orders USING btree (customer_id, created_at DESC);
CREATE INDEX IF NOT EXISTS orders_driver_idx ON public.orders USING btree (driver_id, created_at DESC);
CREATE INDEX IF NOT EXISTS orders_store_idx ON public.orders USING btree (store_id, created_at DESC);
CREATE INDEX IF NOT EXISTS orders_created_idx ON public.orders USING btree (created_at DESC);
CREATE INDEX IF NOT EXISTS orders_open_idx ON public.orders USING btree (created_at) WHERE ((driver_id IS NULL) AND (status = ANY (ARRAY['preparing'::order_status, 'ready'::order_status])));
CREATE INDEX IF NOT EXISTS orders_active_idx ON public.orders USING btree (status) WHERE (status = ANY (ARRAY['pending'::order_status, 'preparing'::order_status, 'ready'::order_status, 'pickedup'::order_status]));
CREATE INDEX IF NOT EXISTS orders_promo_idx ON public.orders USING btree (promo_code) WHERE (promo_code IS NOT NULL);
CREATE UNIQUE INDEX IF NOT EXISTS orders_client_key_uq ON public.orders USING btree (customer_id, client_key) WHERE (client_key IS NOT NULL);
CREATE UNIQUE INDEX IF NOT EXISTS order_chat_pkey ON public.order_chat USING btree (id);
CREATE INDEX IF NOT EXISTS order_chat_order_idx ON public.order_chat USING btree (order_id, created_at);
CREATE UNIQUE INDEX IF NOT EXISTS order_recipient_pkey ON public.order_recipient USING btree (order_id);
CREATE UNIQUE INDEX IF NOT EXISTS profiles_pkey ON public.profiles USING btree (id);
CREATE INDEX IF NOT EXISTS profiles_role_idx ON public.profiles USING btree (role, driver_status);
CREATE INDEX IF NOT EXISTS profiles_online_idx ON public.profiles USING btree (online, last_seen) WHERE (role = 'driver'::user_role);
CREATE INDEX IF NOT EXISTS profiles_created_idx ON public.profiles USING btree (created_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS order_items_pkey ON public.order_items USING btree (id);
CREATE INDEX IF NOT EXISTS order_items_order_idx ON public.order_items USING btree (order_id);
CREATE UNIQUE INDEX IF NOT EXISTS menu_items_pkey ON public.menu_items USING btree (id);
CREATE INDEX IF NOT EXISTS menu_items_store_idx ON public.menu_items USING btree (store_id, available);
CREATE UNIQUE INDEX IF NOT EXISTS banners_pkey ON public.banners USING btree (id);
CREATE INDEX IF NOT EXISTS banners_sort_idx ON public.banners USING btree (sort, created_at);
CREATE UNIQUE INDEX IF NOT EXISTS promo_codes_pkey ON public.promo_codes USING btree (id);
CREATE UNIQUE INDEX IF NOT EXISTS promo_codes_code_uq ON public.promo_codes USING btree (upper(code));
CREATE UNIQUE INDEX IF NOT EXISTS favorites_pkey ON public.favorites USING btree (user_id, store_id);
CREATE INDEX IF NOT EXISTS favorites_user_idx ON public.favorites USING btree (user_id);
CREATE UNIQUE INDEX IF NOT EXISTS order_events_pkey ON public.order_events USING btree (id);
CREATE INDEX IF NOT EXISTS order_events_order_idx ON public.order_events USING btree (order_id);
CREATE INDEX IF NOT EXISTS promo_attempts_idx ON public.promo_attempts USING btree (user_id, at);
CREATE INDEX IF NOT EXISTS promo_attempts_code_idx ON public.promo_attempts USING btree (code) WHERE ok;
CREATE UNIQUE INDEX IF NOT EXISTS group_orders_pkey ON public.group_orders USING btree (id);
CREATE INDEX IF NOT EXISTS group_orders_host_idx ON public.group_orders USING btree (host_id, created_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS group_items_pkey ON public.group_items USING btree (id);
CREATE INDEX IF NOT EXISTS group_items_group_idx ON public.group_items USING btree (group_id);
CREATE UNIQUE INDEX IF NOT EXISTS ratings_pkey ON public.ratings USING btree (order_id);
CREATE INDEX IF NOT EXISTS ratings_store_idx ON public.ratings USING btree (store_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ratings_driver_idx ON public.ratings USING btree (driver_id, created_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS order_offers_pkey ON public.order_offers USING btree (id);
CREATE UNIQUE INDEX IF NOT EXISTS order_offers_order_id_driver_id_key ON public.order_offers USING btree (order_id, driver_id);
CREATE INDEX IF NOT EXISTS order_offers_driver_idx ON public.order_offers USING btree (driver_id, state);
CREATE INDEX IF NOT EXISTS order_offers_order_idx ON public.order_offers USING btree (order_id, state);
CREATE UNIQUE INDEX IF NOT EXISTS audit_log_pkey ON public.audit_log USING btree (id);
CREATE INDEX IF NOT EXISTS audit_log_at_idx ON public.audit_log USING btree (at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS client_errors_pkey ON public.client_errors USING btree (id);
CREATE INDEX IF NOT EXISTS client_errors_at_idx ON public.client_errors USING btree (at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS order_customer_phone_pkey ON public.order_customer_phone USING btree (order_id);
CREATE UNIQUE INDEX IF NOT EXISTS order_driver_phone_pkey ON public.order_driver_phone USING btree (order_id);
CREATE UNIQUE INDEX IF NOT EXISTS addresses_pkey ON public.addresses USING btree (id);
CREATE INDEX IF NOT EXISTS addresses_user_idx ON public.addresses USING btree (user_id);
CREATE UNIQUE INDEX IF NOT EXISTS addresses_one_default ON public.addresses USING btree (user_id) WHERE is_default;
CREATE UNIQUE INDEX IF NOT EXISTS app_settings_pkey ON public.app_settings USING btree (key);
CREATE UNIQUE INDEX IF NOT EXISTS stores_pkey ON public.stores USING btree (id);
CREATE INDEX IF NOT EXISTS stores_owner_idx ON public.stores USING btree (owner_id);
CREATE INDEX IF NOT EXISTS stores_brand_idx ON public.stores USING btree (brand_id) WHERE (brand_id IS NOT NULL);
CREATE UNIQUE INDEX IF NOT EXISTS app_texts_pkey ON public.app_texts USING btree (key);
CREATE UNIQUE INDEX IF NOT EXISTS support_tickets_pkey ON public.support_tickets USING btree (id);
CREATE INDEX IF NOT EXISTS tickets_customer_idx ON public.support_tickets USING btree (customer_id, created_at DESC);
CREATE INDEX IF NOT EXISTS tickets_status_idx ON public.support_tickets USING btree (status, updated_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS tickets_one_open_per_order ON public.support_tickets USING btree (order_id) WHERE ((order_id IS NOT NULL) AND (status = ANY (ARRAY['open'::text, 'in_progress'::text])));
CREATE UNIQUE INDEX IF NOT EXISTS ticket_messages_pkey ON public.ticket_messages USING btree (id);
CREATE INDEX IF NOT EXISTS ticket_msgs_idx ON public.ticket_messages USING btree (ticket_id, created_at);
CREATE UNIQUE INDEX IF NOT EXISTS app_pages_pkey ON public.app_pages USING btree (slug);
CREATE UNIQUE INDEX IF NOT EXISTS store_requests_pkey ON public.store_requests USING btree (id);
CREATE INDEX IF NOT EXISTS store_req_user_idx ON public.store_requests USING btree (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS store_req_status_idx ON public.store_requests USING btree (status, created_at);
CREATE UNIQUE INDEX IF NOT EXISTS wallet_entries_pkey ON public.wallet_entries USING btree (id);
CREATE INDEX IF NOT EXISTS wallet_user_idx ON public.wallet_entries USING btree (user_id, created_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS wallet_one_refund_per_ticket ON public.wallet_entries USING btree (ticket_id) WHERE (kind = 'refund'::text);
CREATE UNIQUE INDEX IF NOT EXISTS wallet_one_spend_per_order ON public.wallet_entries USING btree (order_id) WHERE (kind = 'spend'::text);
CREATE UNIQUE INDEX IF NOT EXISTS wallet_one_return_per_order ON public.wallet_entries USING btree (order_id) WHERE (kind = 'return'::text);
CREATE UNIQUE INDEX IF NOT EXISTS wallet_one_cashback_per_order ON public.wallet_entries USING btree (order_id) WHERE (kind = 'cashback'::text);
CREATE UNIQUE INDEX IF NOT EXISTS staff_members_pkey ON public.staff_members USING btree (user_id);
create policy "stores_admin" on "stores" as PERMISSIVE for ALL to PUBLIC using (is_admin()) with check (is_admin());
create policy "orders_read" on "orders" as PERMISSIVE for SELECT to PUBLIC using (can_see_order(id));
create policy "order_items_read" on "order_items" as PERMISSIVE for SELECT to PUBLIC using (can_see_order(order_id));
create policy "chat_read" on "order_chat" as PERMISSIVE for SELECT to PUBLIC using (can_see_order(order_id));
create policy "profiles_admin_ins" on "profiles" as PERMISSIVE for INSERT to PUBLIC with check (is_admin());
create policy "profiles_admin_del" on "profiles" as PERMISSIVE for DELETE to PUBLIC using (is_admin());
create policy "iog_read" on "item_option_groups" as PERMISSIVE for SELECT to PUBLIC using ((auth.uid() IS NOT NULL));
create policy "io_read" on "item_options" as PERMISSIVE for SELECT to PUBLIC using ((auth.uid() IS NOT NULL));
create policy "chat_insert" on "order_chat" as PERMISSIVE for INSERT to PUBLIC with check (((sender_id = auth.uid()) AND (EXISTS ( SELECT 1
   FROM orders o
  WHERE ((o.id = order_chat.order_id) AND (o.driver_id IS NOT NULL) AND (o.status = ANY (ARRAY['preparing'::order_status, 'ready'::order_status, 'pickedup'::order_status])) AND ((o.customer_id = auth.uid()) OR (o.driver_id = auth.uid())))))));
create policy "hh_read" on "happy_hours" as PERMISSIVE for SELECT to PUBLIC using ((auth.uid() IS NOT NULL));
create policy "hh_write" on "happy_hours" as PERMISSIVE for ALL to PUBLIC using (is_admin()) with check (is_admin());
create policy "favorites_own" on "favorites" as PERMISSIVE for ALL to PUBLIC using ((user_id = auth.uid())) with check ((user_id = auth.uid()));
create policy "events_read" on "order_events" as PERMISSIVE for SELECT to PUBLIC using (can_see_order(order_id));
create policy "loyalty_lots_read" on "loyalty_lots" as PERMISSIVE for SELECT to PUBLIC using (((user_id = auth.uid()) OR is_admin()));
create policy "profiles_select" on "profiles" as PERMISSIVE for SELECT to PUBLIC using (((id = auth.uid()) OR is_admin()));
create policy "profiles_update" on "profiles" as PERMISSIVE for UPDATE to PUBLIC using (((id = auth.uid()) OR is_admin())) with check (((id = auth.uid()) OR is_admin()));
create policy "loyalty_ledger_read" on "loyalty_ledger" as PERMISSIVE for SELECT to PUBLIC using (((user_id = auth.uid()) OR is_admin()));
create policy "addr_own" on "addresses" as PERMISSIVE for ALL to PUBLIC using ((user_id = auth.uid())) with check ((user_id = auth.uid()));
create policy "addr_admin_read" on "addresses" as PERMISSIVE for SELECT to PUBLIC using (is_admin());
create policy "audit_read" on "audit_log" as PERMISSIVE for SELECT to PUBLIC using (is_admin());
create policy "client_errors_read" on "client_errors" as PERMISSIVE for SELECT to PUBLIC using (is_admin());
create policy "settings_read" on "app_settings" as PERMISSIVE for SELECT to PUBLIC using ((auth.uid() IS NOT NULL));
create policy "recipient_read" on "order_recipient" as PERMISSIVE for SELECT to PUBLIC using ((is_admin() OR has_perm('orders'::text) OR has_perm('support'::text) OR (EXISTS ( SELECT 1
   FROM orders o
  WHERE ((o.id = order_recipient.order_id) AND ((o.customer_id = auth.uid()) OR (o.driver_id = auth.uid())))))));
create policy "texts_read" on "app_texts" as PERMISSIVE for SELECT to PUBLIC using ((auth.uid() IS NOT NULL));
create policy "brands_read" on "brands" as PERMISSIVE for SELECT to PUBLIC using ((auth.uid() IS NOT NULL));
create policy "pages_read" on "app_pages" as PERMISSIVE for SELECT to PUBLIC using ((auth.uid() IS NOT NULL));
create policy "offers_read" on "order_offers" as PERMISSIVE for SELECT to PUBLIC using (((driver_id = auth.uid()) OR has_perm('orders'::text)));
create policy "staff_read" on "staff_members" as PERMISSIVE for SELECT to PUBLIC using (((user_id = auth.uid()) OR is_admin()));
create policy "tickets_read" on "support_tickets" as PERMISSIVE for SELECT to PUBLIC using (((customer_id = auth.uid()) OR has_perm('support'::text)));
create policy "ticket_msgs_read" on "ticket_messages" as PERMISSIVE for SELECT to PUBLIC using ((has_perm('support'::text) OR (EXISTS ( SELECT 1
   FROM support_tickets t
  WHERE ((t.id = ticket_messages.ticket_id) AND (t.customer_id = auth.uid()))))));
create policy "ratings_read" on "ratings" as PERMISSIVE for SELECT to PUBLIC using (((customer_id = auth.uid()) OR has_perm('support'::text)));
create policy "stores_read" on "stores" as PERMISSIVE for SELECT to PUBLIC using ((is_active OR (owner_id = auth.uid()) OR has_perm('stores'::text)));
create policy "items_read" on "menu_items" as PERMISSIVE for SELECT to PUBLIC using (((available AND approved AND (EXISTS ( SELECT 1
   FROM stores s
  WHERE ((s.id = menu_items.store_id) AND s.is_active)))) OR owns_store(store_id) OR has_perm('stores'::text)));
create policy "items_write" on "menu_items" as PERMISSIVE for ALL to PUBLIC using ((owns_store(store_id) OR has_perm('stores'::text))) with check ((owns_store(store_id) OR has_perm('stores'::text)));
create policy "iog_write" on "item_option_groups" as PERMISSIVE for ALL to PUBLIC using ((EXISTS ( SELECT 1
   FROM menu_items m
  WHERE ((m.id = item_option_groups.item_id) AND (owns_store(m.store_id) OR has_perm('stores'::text)))))) with check ((EXISTS ( SELECT 1
   FROM menu_items m
  WHERE ((m.id = item_option_groups.item_id) AND (owns_store(m.store_id) OR has_perm('stores'::text))))));
create policy "io_write" on "item_options" as PERMISSIVE for ALL to PUBLIC using ((EXISTS ( SELECT 1
   FROM (item_option_groups g
     JOIN menu_items m ON ((m.id = g.item_id)))
  WHERE ((g.id = item_options.group_id) AND (owns_store(m.store_id) OR has_perm('stores'::text)))))) with check ((EXISTS ( SELECT 1
   FROM (item_option_groups g
     JOIN menu_items m ON ((m.id = g.item_id)))
  WHERE ((g.id = item_options.group_id) AND (owns_store(m.store_id) OR has_perm('stores'::text))))));
create policy "store_req_read" on "store_requests" as PERMISSIVE for SELECT to PUBLIC using (((user_id = auth.uid()) OR has_perm('stores'::text)));
create policy "banners_read" on "banners" as PERMISSIVE for SELECT to PUBLIC using (((is_active AND ((starts_at IS NULL) OR (starts_at <= now())) AND ((ends_at IS NULL) OR (ends_at >= now()))) OR has_perm('content'::text)));
create policy "banners_admin" on "banners" as PERMISSIVE for ALL to PUBLIC using (has_perm('content'::text)) with check (has_perm('content'::text));
create policy "promo_admin" on "promo_codes" as PERMISSIVE for ALL to PUBLIC using (has_perm('content'::text)) with check (has_perm('content'::text));
create policy "wallet_read" on "wallet_entries" as PERMISSIVE for SELECT to PUBLIC using (((user_id = auth.uid()) OR (has_perm('support'::text) OR has_perm('finance'::text))));
create policy "profiles_staff_read" on "profiles" as PERMISSIVE for SELECT to PUBLIC using ((((role = 'customer'::user_role) AND has_perm('support'::text)) OR ((role = 'driver'::user_role) AND (has_perm('orders'::text) OR has_perm('finance'::text)))));
create policy "stores_staff_ins" on "stores" as PERMISSIVE for INSERT to PUBLIC with check (has_perm('stores'::text));
create policy "stores_staff_upd" on "stores" as PERMISSIVE for UPDATE to PUBLIC using (has_perm('stores'::text)) with check (has_perm('stores'::text));
revoke all on table "addresses" from public,anon,authenticated,service_role;
grant INSERT on table "addresses" to authenticated;
grant SELECT on table "addresses" to authenticated;
grant UPDATE on table "addresses" to authenticated;
grant DELETE on table "addresses" to authenticated;
grant TRUNCATE on table "addresses" to authenticated;
grant REFERENCES on table "addresses" to authenticated;
grant TRIGGER on table "addresses" to authenticated;
grant MAINTAIN on table "addresses" to authenticated;
grant INSERT on table "addresses" to service_role;
grant SELECT on table "addresses" to service_role;
grant UPDATE on table "addresses" to service_role;
grant DELETE on table "addresses" to service_role;
grant TRUNCATE on table "addresses" to service_role;
grant REFERENCES on table "addresses" to service_role;
grant TRIGGER on table "addresses" to service_role;
grant MAINTAIN on table "addresses" to service_role;
alter table "addresses" enable row level security;
revoke all on table "app_pages" from public,anon,authenticated,service_role;
grant SELECT on table "app_pages" to authenticated;
grant TRUNCATE on table "app_pages" to authenticated;
grant REFERENCES on table "app_pages" to authenticated;
grant TRIGGER on table "app_pages" to authenticated;
grant MAINTAIN on table "app_pages" to authenticated;
grant INSERT on table "app_pages" to service_role;
grant SELECT on table "app_pages" to service_role;
grant UPDATE on table "app_pages" to service_role;
grant DELETE on table "app_pages" to service_role;
grant TRUNCATE on table "app_pages" to service_role;
grant REFERENCES on table "app_pages" to service_role;
grant TRIGGER on table "app_pages" to service_role;
grant MAINTAIN on table "app_pages" to service_role;
alter table "app_pages" enable row level security;
revoke all on table "app_settings" from public,anon,authenticated,service_role;
grant INSERT on table "app_settings" to authenticated;
grant SELECT on table "app_settings" to authenticated;
grant UPDATE on table "app_settings" to authenticated;
grant DELETE on table "app_settings" to authenticated;
grant TRUNCATE on table "app_settings" to authenticated;
grant REFERENCES on table "app_settings" to authenticated;
grant TRIGGER on table "app_settings" to authenticated;
grant MAINTAIN on table "app_settings" to authenticated;
grant INSERT on table "app_settings" to service_role;
grant SELECT on table "app_settings" to service_role;
grant UPDATE on table "app_settings" to service_role;
grant DELETE on table "app_settings" to service_role;
grant TRUNCATE on table "app_settings" to service_role;
grant REFERENCES on table "app_settings" to service_role;
grant TRIGGER on table "app_settings" to service_role;
grant MAINTAIN on table "app_settings" to service_role;
alter table "app_settings" enable row level security;
revoke all on table "app_texts" from public,anon,authenticated,service_role;
grant INSERT on table "app_texts" to authenticated;
grant SELECT on table "app_texts" to authenticated;
grant UPDATE on table "app_texts" to authenticated;
grant DELETE on table "app_texts" to authenticated;
grant TRUNCATE on table "app_texts" to authenticated;
grant REFERENCES on table "app_texts" to authenticated;
grant TRIGGER on table "app_texts" to authenticated;
grant MAINTAIN on table "app_texts" to authenticated;
grant INSERT on table "app_texts" to service_role;
grant SELECT on table "app_texts" to service_role;
grant UPDATE on table "app_texts" to service_role;
grant DELETE on table "app_texts" to service_role;
grant TRUNCATE on table "app_texts" to service_role;
grant REFERENCES on table "app_texts" to service_role;
grant TRIGGER on table "app_texts" to service_role;
grant MAINTAIN on table "app_texts" to service_role;
alter table "app_texts" enable row level security;
revoke all on table "audit_log" from public,anon,authenticated,service_role;
grant INSERT on table "audit_log" to authenticated;
grant SELECT on table "audit_log" to authenticated;
grant UPDATE on table "audit_log" to authenticated;
grant DELETE on table "audit_log" to authenticated;
grant TRUNCATE on table "audit_log" to authenticated;
grant REFERENCES on table "audit_log" to authenticated;
grant TRIGGER on table "audit_log" to authenticated;
grant MAINTAIN on table "audit_log" to authenticated;
grant INSERT on table "audit_log" to service_role;
grant SELECT on table "audit_log" to service_role;
grant UPDATE on table "audit_log" to service_role;
grant DELETE on table "audit_log" to service_role;
grant TRUNCATE on table "audit_log" to service_role;
grant REFERENCES on table "audit_log" to service_role;
grant TRIGGER on table "audit_log" to service_role;
grant MAINTAIN on table "audit_log" to service_role;
alter table "audit_log" enable row level security;
revoke all on sequence "audit_log_id_seq" from public,anon,authenticated,service_role;
grant SELECT on sequence "audit_log_id_seq" to anon;
grant UPDATE on sequence "audit_log_id_seq" to anon;
grant USAGE on sequence "audit_log_id_seq" to anon;
grant SELECT on sequence "audit_log_id_seq" to authenticated;
grant UPDATE on sequence "audit_log_id_seq" to authenticated;
grant USAGE on sequence "audit_log_id_seq" to authenticated;
grant SELECT on sequence "audit_log_id_seq" to service_role;
grant UPDATE on sequence "audit_log_id_seq" to service_role;
grant USAGE on sequence "audit_log_id_seq" to service_role;
revoke all on table "banners" from public,anon,authenticated,service_role;
grant INSERT on table "banners" to authenticated;
grant SELECT on table "banners" to authenticated;
grant UPDATE on table "banners" to authenticated;
grant DELETE on table "banners" to authenticated;
grant TRUNCATE on table "banners" to authenticated;
grant REFERENCES on table "banners" to authenticated;
grant TRIGGER on table "banners" to authenticated;
grant MAINTAIN on table "banners" to authenticated;
grant INSERT on table "banners" to service_role;
grant SELECT on table "banners" to service_role;
grant UPDATE on table "banners" to service_role;
grant DELETE on table "banners" to service_role;
grant TRUNCATE on table "banners" to service_role;
grant REFERENCES on table "banners" to service_role;
grant TRIGGER on table "banners" to service_role;
grant MAINTAIN on table "banners" to service_role;
alter table "banners" enable row level security;
revoke all on table "brands" from public,anon,authenticated,service_role;
grant SELECT on table "brands" to authenticated;
grant TRUNCATE on table "brands" to authenticated;
grant REFERENCES on table "brands" to authenticated;
grant TRIGGER on table "brands" to authenticated;
grant MAINTAIN on table "brands" to authenticated;
grant INSERT on table "brands" to service_role;
grant SELECT on table "brands" to service_role;
grant UPDATE on table "brands" to service_role;
grant DELETE on table "brands" to service_role;
grant TRUNCATE on table "brands" to service_role;
grant REFERENCES on table "brands" to service_role;
grant TRIGGER on table "brands" to service_role;
grant MAINTAIN on table "brands" to service_role;
alter table "brands" enable row level security;
revoke all on table "client_errors" from public,anon,authenticated,service_role;
grant INSERT on table "client_errors" to authenticated;
grant SELECT on table "client_errors" to authenticated;
grant UPDATE on table "client_errors" to authenticated;
grant DELETE on table "client_errors" to authenticated;
grant TRUNCATE on table "client_errors" to authenticated;
grant REFERENCES on table "client_errors" to authenticated;
grant TRIGGER on table "client_errors" to authenticated;
grant MAINTAIN on table "client_errors" to authenticated;
grant INSERT on table "client_errors" to service_role;
grant SELECT on table "client_errors" to service_role;
grant UPDATE on table "client_errors" to service_role;
grant DELETE on table "client_errors" to service_role;
grant TRUNCATE on table "client_errors" to service_role;
grant REFERENCES on table "client_errors" to service_role;
grant TRIGGER on table "client_errors" to service_role;
grant MAINTAIN on table "client_errors" to service_role;
alter table "client_errors" enable row level security;
revoke all on sequence "client_errors_id_seq" from public,anon,authenticated,service_role;
grant SELECT on sequence "client_errors_id_seq" to anon;
grant UPDATE on sequence "client_errors_id_seq" to anon;
grant USAGE on sequence "client_errors_id_seq" to anon;
grant SELECT on sequence "client_errors_id_seq" to authenticated;
grant UPDATE on sequence "client_errors_id_seq" to authenticated;
grant USAGE on sequence "client_errors_id_seq" to authenticated;
grant SELECT on sequence "client_errors_id_seq" to service_role;
grant UPDATE on sequence "client_errors_id_seq" to service_role;
grant USAGE on sequence "client_errors_id_seq" to service_role;
revoke all on table "favorites" from public,anon,authenticated,service_role;
grant INSERT on table "favorites" to authenticated;
grant SELECT on table "favorites" to authenticated;
grant UPDATE on table "favorites" to authenticated;
grant DELETE on table "favorites" to authenticated;
grant TRUNCATE on table "favorites" to authenticated;
grant REFERENCES on table "favorites" to authenticated;
grant TRIGGER on table "favorites" to authenticated;
grant MAINTAIN on table "favorites" to authenticated;
grant INSERT on table "favorites" to service_role;
grant SELECT on table "favorites" to service_role;
grant UPDATE on table "favorites" to service_role;
grant DELETE on table "favorites" to service_role;
grant TRUNCATE on table "favorites" to service_role;
grant REFERENCES on table "favorites" to service_role;
grant TRIGGER on table "favorites" to service_role;
grant MAINTAIN on table "favorites" to service_role;
alter table "favorites" enable row level security;
revoke all on table "group_items" from public,anon,authenticated,service_role;
grant INSERT on table "group_items" to service_role;
grant SELECT on table "group_items" to service_role;
grant UPDATE on table "group_items" to service_role;
grant DELETE on table "group_items" to service_role;
grant TRUNCATE on table "group_items" to service_role;
grant REFERENCES on table "group_items" to service_role;
grant TRIGGER on table "group_items" to service_role;
grant MAINTAIN on table "group_items" to service_role;
alter table "group_items" enable row level security;
revoke all on sequence "group_items_id_seq" from public,anon,authenticated,service_role;
grant SELECT on sequence "group_items_id_seq" to anon;
grant UPDATE on sequence "group_items_id_seq" to anon;
grant USAGE on sequence "group_items_id_seq" to anon;
grant SELECT on sequence "group_items_id_seq" to authenticated;
grant UPDATE on sequence "group_items_id_seq" to authenticated;
grant USAGE on sequence "group_items_id_seq" to authenticated;
grant SELECT on sequence "group_items_id_seq" to service_role;
grant UPDATE on sequence "group_items_id_seq" to service_role;
grant USAGE on sequence "group_items_id_seq" to service_role;
revoke all on table "group_orders" from public,anon,authenticated,service_role;
grant INSERT on table "group_orders" to service_role;
grant SELECT on table "group_orders" to service_role;
grant UPDATE on table "group_orders" to service_role;
grant DELETE on table "group_orders" to service_role;
grant TRUNCATE on table "group_orders" to service_role;
grant REFERENCES on table "group_orders" to service_role;
grant TRIGGER on table "group_orders" to service_role;
grant MAINTAIN on table "group_orders" to service_role;
alter table "group_orders" enable row level security;
revoke all on table "happy_hours" from public,anon,authenticated,service_role;
grant INSERT on table "happy_hours" to authenticated;
grant SELECT on table "happy_hours" to authenticated;
grant UPDATE on table "happy_hours" to authenticated;
grant DELETE on table "happy_hours" to authenticated;
grant TRUNCATE on table "happy_hours" to authenticated;
grant REFERENCES on table "happy_hours" to authenticated;
grant TRIGGER on table "happy_hours" to authenticated;
grant MAINTAIN on table "happy_hours" to authenticated;
grant INSERT on table "happy_hours" to service_role;
grant SELECT on table "happy_hours" to service_role;
grant UPDATE on table "happy_hours" to service_role;
grant DELETE on table "happy_hours" to service_role;
grant TRUNCATE on table "happy_hours" to service_role;
grant REFERENCES on table "happy_hours" to service_role;
grant TRIGGER on table "happy_hours" to service_role;
grant MAINTAIN on table "happy_hours" to service_role;
alter table "happy_hours" enable row level security;
revoke all on sequence "happy_hours_id_seq" from public,anon,authenticated,service_role;
grant SELECT on sequence "happy_hours_id_seq" to anon;
grant UPDATE on sequence "happy_hours_id_seq" to anon;
grant USAGE on sequence "happy_hours_id_seq" to anon;
grant SELECT on sequence "happy_hours_id_seq" to authenticated;
grant UPDATE on sequence "happy_hours_id_seq" to authenticated;
grant USAGE on sequence "happy_hours_id_seq" to authenticated;
grant SELECT on sequence "happy_hours_id_seq" to service_role;
grant UPDATE on sequence "happy_hours_id_seq" to service_role;
grant USAGE on sequence "happy_hours_id_seq" to service_role;
revoke all on table "item_option_groups" from public,anon,authenticated,service_role;
grant INSERT on table "item_option_groups" to authenticated;
grant SELECT on table "item_option_groups" to authenticated;
grant UPDATE on table "item_option_groups" to authenticated;
grant DELETE on table "item_option_groups" to authenticated;
grant TRUNCATE on table "item_option_groups" to authenticated;
grant REFERENCES on table "item_option_groups" to authenticated;
grant TRIGGER on table "item_option_groups" to authenticated;
grant MAINTAIN on table "item_option_groups" to authenticated;
grant INSERT on table "item_option_groups" to service_role;
grant SELECT on table "item_option_groups" to service_role;
grant UPDATE on table "item_option_groups" to service_role;
grant DELETE on table "item_option_groups" to service_role;
grant TRUNCATE on table "item_option_groups" to service_role;
grant REFERENCES on table "item_option_groups" to service_role;
grant TRIGGER on table "item_option_groups" to service_role;
grant MAINTAIN on table "item_option_groups" to service_role;
alter table "item_option_groups" enable row level security;
revoke all on table "item_options" from public,anon,authenticated,service_role;
grant INSERT on table "item_options" to authenticated;
grant SELECT on table "item_options" to authenticated;
grant UPDATE on table "item_options" to authenticated;
grant DELETE on table "item_options" to authenticated;
grant TRUNCATE on table "item_options" to authenticated;
grant REFERENCES on table "item_options" to authenticated;
grant TRIGGER on table "item_options" to authenticated;
grant MAINTAIN on table "item_options" to authenticated;
grant INSERT on table "item_options" to service_role;
grant SELECT on table "item_options" to service_role;
grant UPDATE on table "item_options" to service_role;
grant DELETE on table "item_options" to service_role;
grant TRUNCATE on table "item_options" to service_role;
grant REFERENCES on table "item_options" to service_role;
grant TRIGGER on table "item_options" to service_role;
grant MAINTAIN on table "item_options" to service_role;
alter table "item_options" enable row level security;
revoke all on table "loyalty_ledger" from public,anon,authenticated,service_role;
grant SELECT on table "loyalty_ledger" to authenticated;
grant TRUNCATE on table "loyalty_ledger" to authenticated;
grant REFERENCES on table "loyalty_ledger" to authenticated;
grant TRIGGER on table "loyalty_ledger" to authenticated;
grant MAINTAIN on table "loyalty_ledger" to authenticated;
grant INSERT on table "loyalty_ledger" to service_role;
grant SELECT on table "loyalty_ledger" to service_role;
grant UPDATE on table "loyalty_ledger" to service_role;
grant DELETE on table "loyalty_ledger" to service_role;
grant TRUNCATE on table "loyalty_ledger" to service_role;
grant REFERENCES on table "loyalty_ledger" to service_role;
grant TRIGGER on table "loyalty_ledger" to service_role;
grant MAINTAIN on table "loyalty_ledger" to service_role;
alter table "loyalty_ledger" enable row level security;
revoke all on sequence "loyalty_ledger_id_seq" from public,anon,authenticated,service_role;
grant SELECT on sequence "loyalty_ledger_id_seq" to anon;
grant UPDATE on sequence "loyalty_ledger_id_seq" to anon;
grant USAGE on sequence "loyalty_ledger_id_seq" to anon;
grant SELECT on sequence "loyalty_ledger_id_seq" to authenticated;
grant UPDATE on sequence "loyalty_ledger_id_seq" to authenticated;
grant USAGE on sequence "loyalty_ledger_id_seq" to authenticated;
grant SELECT on sequence "loyalty_ledger_id_seq" to service_role;
grant UPDATE on sequence "loyalty_ledger_id_seq" to service_role;
grant USAGE on sequence "loyalty_ledger_id_seq" to service_role;
revoke all on table "loyalty_lots" from public,anon,authenticated,service_role;
grant SELECT on table "loyalty_lots" to authenticated;
grant TRUNCATE on table "loyalty_lots" to authenticated;
grant REFERENCES on table "loyalty_lots" to authenticated;
grant TRIGGER on table "loyalty_lots" to authenticated;
grant MAINTAIN on table "loyalty_lots" to authenticated;
grant INSERT on table "loyalty_lots" to service_role;
grant SELECT on table "loyalty_lots" to service_role;
grant UPDATE on table "loyalty_lots" to service_role;
grant DELETE on table "loyalty_lots" to service_role;
grant TRUNCATE on table "loyalty_lots" to service_role;
grant REFERENCES on table "loyalty_lots" to service_role;
grant TRIGGER on table "loyalty_lots" to service_role;
grant MAINTAIN on table "loyalty_lots" to service_role;
alter table "loyalty_lots" enable row level security;
revoke all on sequence "loyalty_lots_id_seq" from public,anon,authenticated,service_role;
grant SELECT on sequence "loyalty_lots_id_seq" to anon;
grant UPDATE on sequence "loyalty_lots_id_seq" to anon;
grant USAGE on sequence "loyalty_lots_id_seq" to anon;
grant SELECT on sequence "loyalty_lots_id_seq" to authenticated;
grant UPDATE on sequence "loyalty_lots_id_seq" to authenticated;
grant USAGE on sequence "loyalty_lots_id_seq" to authenticated;
grant SELECT on sequence "loyalty_lots_id_seq" to service_role;
grant UPDATE on sequence "loyalty_lots_id_seq" to service_role;
grant USAGE on sequence "loyalty_lots_id_seq" to service_role;
revoke all on table "menu_items" from public,anon,authenticated,service_role;
grant INSERT on table "menu_items" to authenticated;
grant SELECT on table "menu_items" to authenticated;
grant UPDATE on table "menu_items" to authenticated;
grant DELETE on table "menu_items" to authenticated;
grant TRUNCATE on table "menu_items" to authenticated;
grant REFERENCES on table "menu_items" to authenticated;
grant TRIGGER on table "menu_items" to authenticated;
grant MAINTAIN on table "menu_items" to authenticated;
grant INSERT on table "menu_items" to service_role;
grant SELECT on table "menu_items" to service_role;
grant UPDATE on table "menu_items" to service_role;
grant DELETE on table "menu_items" to service_role;
grant TRUNCATE on table "menu_items" to service_role;
grant REFERENCES on table "menu_items" to service_role;
grant TRIGGER on table "menu_items" to service_role;
grant MAINTAIN on table "menu_items" to service_role;
alter table "menu_items" enable row level security;
revoke all on table "order_chat" from public,anon,authenticated,service_role;
grant INSERT on table "order_chat" to authenticated;
grant SELECT on table "order_chat" to authenticated;
grant UPDATE on table "order_chat" to authenticated;
grant DELETE on table "order_chat" to authenticated;
grant TRUNCATE on table "order_chat" to authenticated;
grant REFERENCES on table "order_chat" to authenticated;
grant TRIGGER on table "order_chat" to authenticated;
grant MAINTAIN on table "order_chat" to authenticated;
grant INSERT on table "order_chat" to service_role;
grant SELECT on table "order_chat" to service_role;
grant UPDATE on table "order_chat" to service_role;
grant DELETE on table "order_chat" to service_role;
grant TRUNCATE on table "order_chat" to service_role;
grant REFERENCES on table "order_chat" to service_role;
grant TRIGGER on table "order_chat" to service_role;
grant MAINTAIN on table "order_chat" to service_role;
alter table "order_chat" enable row level security;
revoke all on sequence "order_chat_id_seq" from public,anon,authenticated,service_role;
grant SELECT on sequence "order_chat_id_seq" to authenticated;
grant UPDATE on sequence "order_chat_id_seq" to authenticated;
grant USAGE on sequence "order_chat_id_seq" to authenticated;
grant SELECT on sequence "order_chat_id_seq" to service_role;
grant UPDATE on sequence "order_chat_id_seq" to service_role;
grant USAGE on sequence "order_chat_id_seq" to service_role;
revoke all on table "order_customer_phone" from public,anon,authenticated,service_role;
grant INSERT on table "order_customer_phone" to service_role;
grant SELECT on table "order_customer_phone" to service_role;
grant UPDATE on table "order_customer_phone" to service_role;
grant DELETE on table "order_customer_phone" to service_role;
grant TRUNCATE on table "order_customer_phone" to service_role;
grant REFERENCES on table "order_customer_phone" to service_role;
grant TRIGGER on table "order_customer_phone" to service_role;
grant MAINTAIN on table "order_customer_phone" to service_role;
alter table "order_customer_phone" enable row level security;
revoke all on table "order_driver_phone" from public,anon,authenticated,service_role;
grant INSERT on table "order_driver_phone" to service_role;
grant SELECT on table "order_driver_phone" to service_role;
grant UPDATE on table "order_driver_phone" to service_role;
grant DELETE on table "order_driver_phone" to service_role;
grant TRUNCATE on table "order_driver_phone" to service_role;
grant REFERENCES on table "order_driver_phone" to service_role;
grant TRIGGER on table "order_driver_phone" to service_role;
grant MAINTAIN on table "order_driver_phone" to service_role;
alter table "order_driver_phone" enable row level security;
revoke all on table "order_events" from public,anon,authenticated,service_role;
grant INSERT on table "order_events" to authenticated;
grant SELECT on table "order_events" to authenticated;
grant UPDATE on table "order_events" to authenticated;
grant DELETE on table "order_events" to authenticated;
grant TRUNCATE on table "order_events" to authenticated;
grant REFERENCES on table "order_events" to authenticated;
grant TRIGGER on table "order_events" to authenticated;
grant MAINTAIN on table "order_events" to authenticated;
grant INSERT on table "order_events" to service_role;
grant SELECT on table "order_events" to service_role;
grant UPDATE on table "order_events" to service_role;
grant DELETE on table "order_events" to service_role;
grant TRUNCATE on table "order_events" to service_role;
grant REFERENCES on table "order_events" to service_role;
grant TRIGGER on table "order_events" to service_role;
grant MAINTAIN on table "order_events" to service_role;
alter table "order_events" enable row level security;
revoke all on sequence "order_events_id_seq" from public,anon,authenticated,service_role;
grant SELECT on sequence "order_events_id_seq" to authenticated;
grant UPDATE on sequence "order_events_id_seq" to authenticated;
grant USAGE on sequence "order_events_id_seq" to authenticated;
grant SELECT on sequence "order_events_id_seq" to service_role;
grant UPDATE on sequence "order_events_id_seq" to service_role;
grant USAGE on sequence "order_events_id_seq" to service_role;
revoke all on table "order_items" from public,anon,authenticated,service_role;
grant INSERT on table "order_items" to authenticated;
grant SELECT on table "order_items" to authenticated;
grant UPDATE on table "order_items" to authenticated;
grant DELETE on table "order_items" to authenticated;
grant TRUNCATE on table "order_items" to authenticated;
grant REFERENCES on table "order_items" to authenticated;
grant TRIGGER on table "order_items" to authenticated;
grant MAINTAIN on table "order_items" to authenticated;
grant INSERT on table "order_items" to service_role;
grant SELECT on table "order_items" to service_role;
grant UPDATE on table "order_items" to service_role;
grant DELETE on table "order_items" to service_role;
grant TRUNCATE on table "order_items" to service_role;
grant REFERENCES on table "order_items" to service_role;
grant TRIGGER on table "order_items" to service_role;
grant MAINTAIN on table "order_items" to service_role;
alter table "order_items" enable row level security;
revoke all on table "order_offers" from public,anon,authenticated,service_role;
grant INSERT on table "order_offers" to authenticated;
grant SELECT on table "order_offers" to authenticated;
grant UPDATE on table "order_offers" to authenticated;
grant DELETE on table "order_offers" to authenticated;
grant TRUNCATE on table "order_offers" to authenticated;
grant REFERENCES on table "order_offers" to authenticated;
grant TRIGGER on table "order_offers" to authenticated;
grant MAINTAIN on table "order_offers" to authenticated;
grant INSERT on table "order_offers" to service_role;
grant SELECT on table "order_offers" to service_role;
grant UPDATE on table "order_offers" to service_role;
grant DELETE on table "order_offers" to service_role;
grant TRUNCATE on table "order_offers" to service_role;
grant REFERENCES on table "order_offers" to service_role;
grant TRIGGER on table "order_offers" to service_role;
grant MAINTAIN on table "order_offers" to service_role;
alter table "order_offers" enable row level security;
revoke all on sequence "order_offers_id_seq" from public,anon,authenticated,service_role;
grant SELECT on sequence "order_offers_id_seq" to anon;
grant UPDATE on sequence "order_offers_id_seq" to anon;
grant USAGE on sequence "order_offers_id_seq" to anon;
grant SELECT on sequence "order_offers_id_seq" to authenticated;
grant UPDATE on sequence "order_offers_id_seq" to authenticated;
grant USAGE on sequence "order_offers_id_seq" to authenticated;
grant SELECT on sequence "order_offers_id_seq" to service_role;
grant UPDATE on sequence "order_offers_id_seq" to service_role;
grant USAGE on sequence "order_offers_id_seq" to service_role;
revoke all on table "order_recipient" from public,anon,authenticated,service_role;
grant SELECT on table "order_recipient" to authenticated;
grant TRUNCATE on table "order_recipient" to authenticated;
grant REFERENCES on table "order_recipient" to authenticated;
grant TRIGGER on table "order_recipient" to authenticated;
grant MAINTAIN on table "order_recipient" to authenticated;
grant INSERT on table "order_recipient" to service_role;
grant SELECT on table "order_recipient" to service_role;
grant UPDATE on table "order_recipient" to service_role;
grant DELETE on table "order_recipient" to service_role;
grant TRUNCATE on table "order_recipient" to service_role;
grant REFERENCES on table "order_recipient" to service_role;
grant TRIGGER on table "order_recipient" to service_role;
grant MAINTAIN on table "order_recipient" to service_role;
alter table "order_recipient" enable row level security;
revoke all on table "orders" from public,anon,authenticated,service_role;
grant INSERT on table "orders" to authenticated;
grant SELECT on table "orders" to authenticated;
grant UPDATE on table "orders" to authenticated;
grant DELETE on table "orders" to authenticated;
grant TRUNCATE on table "orders" to authenticated;
grant REFERENCES on table "orders" to authenticated;
grant TRIGGER on table "orders" to authenticated;
grant MAINTAIN on table "orders" to authenticated;
grant INSERT on table "orders" to service_role;
grant SELECT on table "orders" to service_role;
grant UPDATE on table "orders" to service_role;
grant DELETE on table "orders" to service_role;
grant TRUNCATE on table "orders" to service_role;
grant REFERENCES on table "orders" to service_role;
grant TRIGGER on table "orders" to service_role;
grant MAINTAIN on table "orders" to service_role;
alter table "orders" enable row level security;
revoke all on sequence "orders_id_seq" from public,anon,authenticated,service_role;
grant SELECT on sequence "orders_id_seq" to authenticated;
grant UPDATE on sequence "orders_id_seq" to authenticated;
grant USAGE on sequence "orders_id_seq" to authenticated;
grant SELECT on sequence "orders_id_seq" to service_role;
grant UPDATE on sequence "orders_id_seq" to service_role;
grant USAGE on sequence "orders_id_seq" to service_role;
revoke all on table "profiles" from public,anon,authenticated,service_role;
grant INSERT on table "profiles" to authenticated;
grant SELECT on table "profiles" to authenticated;
grant UPDATE on table "profiles" to authenticated;
grant DELETE on table "profiles" to authenticated;
grant TRUNCATE on table "profiles" to authenticated;
grant REFERENCES on table "profiles" to authenticated;
grant TRIGGER on table "profiles" to authenticated;
grant MAINTAIN on table "profiles" to authenticated;
grant INSERT on table "profiles" to service_role;
grant SELECT on table "profiles" to service_role;
grant UPDATE on table "profiles" to service_role;
grant DELETE on table "profiles" to service_role;
grant TRUNCATE on table "profiles" to service_role;
grant REFERENCES on table "profiles" to service_role;
grant TRIGGER on table "profiles" to service_role;
grant MAINTAIN on table "profiles" to service_role;
alter table "profiles" enable row level security;
revoke all on table "promo_attempts" from public,anon,authenticated,service_role;
grant INSERT on table "promo_attempts" to authenticated;
grant SELECT on table "promo_attempts" to authenticated;
grant UPDATE on table "promo_attempts" to authenticated;
grant DELETE on table "promo_attempts" to authenticated;
grant TRUNCATE on table "promo_attempts" to authenticated;
grant REFERENCES on table "promo_attempts" to authenticated;
grant TRIGGER on table "promo_attempts" to authenticated;
grant MAINTAIN on table "promo_attempts" to authenticated;
grant INSERT on table "promo_attempts" to service_role;
grant SELECT on table "promo_attempts" to service_role;
grant UPDATE on table "promo_attempts" to service_role;
grant DELETE on table "promo_attempts" to service_role;
grant TRUNCATE on table "promo_attempts" to service_role;
grant REFERENCES on table "promo_attempts" to service_role;
grant TRIGGER on table "promo_attempts" to service_role;
grant MAINTAIN on table "promo_attempts" to service_role;
alter table "promo_attempts" enable row level security;
revoke all on table "promo_codes" from public,anon,authenticated,service_role;
grant INSERT on table "promo_codes" to authenticated;
grant SELECT on table "promo_codes" to authenticated;
grant UPDATE on table "promo_codes" to authenticated;
grant DELETE on table "promo_codes" to authenticated;
grant TRUNCATE on table "promo_codes" to authenticated;
grant REFERENCES on table "promo_codes" to authenticated;
grant TRIGGER on table "promo_codes" to authenticated;
grant MAINTAIN on table "promo_codes" to authenticated;
grant INSERT on table "promo_codes" to service_role;
grant SELECT on table "promo_codes" to service_role;
grant UPDATE on table "promo_codes" to service_role;
grant DELETE on table "promo_codes" to service_role;
grant TRUNCATE on table "promo_codes" to service_role;
grant REFERENCES on table "promo_codes" to service_role;
grant TRIGGER on table "promo_codes" to service_role;
grant MAINTAIN on table "promo_codes" to service_role;
alter table "promo_codes" enable row level security;
revoke all on table "promo_guess" from public,anon,authenticated,service_role;
grant INSERT on table "promo_guess" to service_role;
grant SELECT on table "promo_guess" to service_role;
grant UPDATE on table "promo_guess" to service_role;
grant DELETE on table "promo_guess" to service_role;
grant TRUNCATE on table "promo_guess" to service_role;
grant REFERENCES on table "promo_guess" to service_role;
grant TRIGGER on table "promo_guess" to service_role;
grant MAINTAIN on table "promo_guess" to service_role;
alter table "promo_guess" enable row level security;
revoke all on sequence "promo_guess_id_seq" from public,anon,authenticated,service_role;
grant SELECT on sequence "promo_guess_id_seq" to anon;
grant UPDATE on sequence "promo_guess_id_seq" to anon;
grant USAGE on sequence "promo_guess_id_seq" to anon;
grant SELECT on sequence "promo_guess_id_seq" to authenticated;
grant UPDATE on sequence "promo_guess_id_seq" to authenticated;
grant USAGE on sequence "promo_guess_id_seq" to authenticated;
grant SELECT on sequence "promo_guess_id_seq" to service_role;
grant UPDATE on sequence "promo_guess_id_seq" to service_role;
grant USAGE on sequence "promo_guess_id_seq" to service_role;
revoke all on table "ratings" from public,anon,authenticated,service_role;
grant INSERT on table "ratings" to authenticated;
grant SELECT on table "ratings" to authenticated;
grant UPDATE on table "ratings" to authenticated;
grant DELETE on table "ratings" to authenticated;
grant TRUNCATE on table "ratings" to authenticated;
grant REFERENCES on table "ratings" to authenticated;
grant TRIGGER on table "ratings" to authenticated;
grant MAINTAIN on table "ratings" to authenticated;
grant INSERT on table "ratings" to service_role;
grant SELECT on table "ratings" to service_role;
grant UPDATE on table "ratings" to service_role;
grant DELETE on table "ratings" to service_role;
grant TRUNCATE on table "ratings" to service_role;
grant REFERENCES on table "ratings" to service_role;
grant TRIGGER on table "ratings" to service_role;
grant MAINTAIN on table "ratings" to service_role;
alter table "ratings" enable row level security;
revoke all on table "staff_members" from public,anon,authenticated,service_role;
grant SELECT on table "staff_members" to authenticated;
grant TRUNCATE on table "staff_members" to authenticated;
grant REFERENCES on table "staff_members" to authenticated;
grant TRIGGER on table "staff_members" to authenticated;
grant MAINTAIN on table "staff_members" to authenticated;
grant INSERT on table "staff_members" to service_role;
grant SELECT on table "staff_members" to service_role;
grant UPDATE on table "staff_members" to service_role;
grant DELETE on table "staff_members" to service_role;
grant TRUNCATE on table "staff_members" to service_role;
grant REFERENCES on table "staff_members" to service_role;
grant TRIGGER on table "staff_members" to service_role;
grant MAINTAIN on table "staff_members" to service_role;
alter table "staff_members" enable row level security;
revoke all on table "store_requests" from public,anon,authenticated,service_role;
grant INSERT on table "store_requests" to authenticated;
grant SELECT on table "store_requests" to authenticated;
grant UPDATE on table "store_requests" to authenticated;
grant DELETE on table "store_requests" to authenticated;
grant TRUNCATE on table "store_requests" to authenticated;
grant REFERENCES on table "store_requests" to authenticated;
grant TRIGGER on table "store_requests" to authenticated;
grant MAINTAIN on table "store_requests" to authenticated;
grant INSERT on table "store_requests" to service_role;
grant SELECT on table "store_requests" to service_role;
grant UPDATE on table "store_requests" to service_role;
grant DELETE on table "store_requests" to service_role;
grant TRUNCATE on table "store_requests" to service_role;
grant REFERENCES on table "store_requests" to service_role;
grant TRIGGER on table "store_requests" to service_role;
grant MAINTAIN on table "store_requests" to service_role;
alter table "store_requests" enable row level security;
revoke all on table "stores" from public,anon,authenticated,service_role;
grant INSERT on table "stores" to authenticated;
grant UPDATE on table "stores" to authenticated;
grant DELETE on table "stores" to authenticated;
grant TRUNCATE on table "stores" to authenticated;
grant REFERENCES on table "stores" to authenticated;
grant TRIGGER on table "stores" to authenticated;
grant MAINTAIN on table "stores" to authenticated;
grant INSERT on table "stores" to service_role;
grant SELECT on table "stores" to service_role;
grant UPDATE on table "stores" to service_role;
grant DELETE on table "stores" to service_role;
grant TRUNCATE on table "stores" to service_role;
grant REFERENCES on table "stores" to service_role;
grant TRIGGER on table "stores" to service_role;
grant MAINTAIN on table "stores" to service_role;
alter table "stores" enable row level security;
revoke all on table "support_tickets" from public,anon,authenticated,service_role;
grant INSERT on table "support_tickets" to authenticated;
grant SELECT on table "support_tickets" to authenticated;
grant UPDATE on table "support_tickets" to authenticated;
grant DELETE on table "support_tickets" to authenticated;
grant TRUNCATE on table "support_tickets" to authenticated;
grant REFERENCES on table "support_tickets" to authenticated;
grant TRIGGER on table "support_tickets" to authenticated;
grant MAINTAIN on table "support_tickets" to authenticated;
grant INSERT on table "support_tickets" to service_role;
grant SELECT on table "support_tickets" to service_role;
grant UPDATE on table "support_tickets" to service_role;
grant DELETE on table "support_tickets" to service_role;
grant TRUNCATE on table "support_tickets" to service_role;
grant REFERENCES on table "support_tickets" to service_role;
grant TRIGGER on table "support_tickets" to service_role;
grant MAINTAIN on table "support_tickets" to service_role;
alter table "support_tickets" enable row level security;
revoke all on sequence "support_tickets_id_seq" from public,anon,authenticated,service_role;
grant SELECT on sequence "support_tickets_id_seq" to anon;
grant UPDATE on sequence "support_tickets_id_seq" to anon;
grant USAGE on sequence "support_tickets_id_seq" to anon;
grant SELECT on sequence "support_tickets_id_seq" to authenticated;
grant UPDATE on sequence "support_tickets_id_seq" to authenticated;
grant USAGE on sequence "support_tickets_id_seq" to authenticated;
grant SELECT on sequence "support_tickets_id_seq" to service_role;
grant UPDATE on sequence "support_tickets_id_seq" to service_role;
grant USAGE on sequence "support_tickets_id_seq" to service_role;
revoke all on table "ticket_messages" from public,anon,authenticated,service_role;
grant INSERT on table "ticket_messages" to authenticated;
grant SELECT on table "ticket_messages" to authenticated;
grant UPDATE on table "ticket_messages" to authenticated;
grant DELETE on table "ticket_messages" to authenticated;
grant TRUNCATE on table "ticket_messages" to authenticated;
grant REFERENCES on table "ticket_messages" to authenticated;
grant TRIGGER on table "ticket_messages" to authenticated;
grant MAINTAIN on table "ticket_messages" to authenticated;
grant INSERT on table "ticket_messages" to service_role;
grant SELECT on table "ticket_messages" to service_role;
grant UPDATE on table "ticket_messages" to service_role;
grant DELETE on table "ticket_messages" to service_role;
grant TRUNCATE on table "ticket_messages" to service_role;
grant REFERENCES on table "ticket_messages" to service_role;
grant TRIGGER on table "ticket_messages" to service_role;
grant MAINTAIN on table "ticket_messages" to service_role;
alter table "ticket_messages" enable row level security;
revoke all on sequence "ticket_messages_id_seq" from public,anon,authenticated,service_role;
grant SELECT on sequence "ticket_messages_id_seq" to anon;
grant UPDATE on sequence "ticket_messages_id_seq" to anon;
grant USAGE on sequence "ticket_messages_id_seq" to anon;
grant SELECT on sequence "ticket_messages_id_seq" to authenticated;
grant UPDATE on sequence "ticket_messages_id_seq" to authenticated;
grant USAGE on sequence "ticket_messages_id_seq" to authenticated;
grant SELECT on sequence "ticket_messages_id_seq" to service_role;
grant UPDATE on sequence "ticket_messages_id_seq" to service_role;
grant USAGE on sequence "ticket_messages_id_seq" to service_role;
revoke all on table "wallet_entries" from public,anon,authenticated,service_role;
grant SELECT on table "wallet_entries" to authenticated;
grant TRUNCATE on table "wallet_entries" to authenticated;
grant REFERENCES on table "wallet_entries" to authenticated;
grant TRIGGER on table "wallet_entries" to authenticated;
grant MAINTAIN on table "wallet_entries" to authenticated;
grant INSERT on table "wallet_entries" to service_role;
grant SELECT on table "wallet_entries" to service_role;
grant UPDATE on table "wallet_entries" to service_role;
grant DELETE on table "wallet_entries" to service_role;
grant TRUNCATE on table "wallet_entries" to service_role;
grant REFERENCES on table "wallet_entries" to service_role;
grant TRIGGER on table "wallet_entries" to service_role;
grant MAINTAIN on table "wallet_entries" to service_role;
alter table "wallet_entries" enable row level security;
revoke all on sequence "wallet_entries_id_seq" from public,anon,authenticated,service_role;
grant SELECT on sequence "wallet_entries_id_seq" to anon;
grant UPDATE on sequence "wallet_entries_id_seq" to anon;
grant USAGE on sequence "wallet_entries_id_seq" to anon;
grant SELECT on sequence "wallet_entries_id_seq" to authenticated;
grant UPDATE on sequence "wallet_entries_id_seq" to authenticated;
grant USAGE on sequence "wallet_entries_id_seq" to authenticated;
grant SELECT on sequence "wallet_entries_id_seq" to service_role;
grant UPDATE on sequence "wallet_entries_id_seq" to service_role;
grant USAGE on sequence "wallet_entries_id_seq" to service_role;
grant select("id") on "stores" to authenticated;
grant select("name") on "stores" to authenticated;
grant select("category") on "stores" to authenticated;
grant select("description") on "stores" to authenticated;
grant select("logo_url") on "stores" to authenticated;
grant select("cover_url") on "stores" to authenticated;
grant select("address") on "stores" to authenticated;
grant select("lat") on "stores" to authenticated;
grant select("lng") on "stores" to authenticated;
grant select("fee_type") on "stores" to authenticated;
grant select("fee_base") on "stores" to authenticated;
grant select("fee_per_km") on "stores" to authenticated;
grant select("fee_free_km") on "stores" to authenticated;
grant select("discount_pct") on "stores" to authenticated;
grant select("is_open") on "stores" to authenticated;
grant select("is_active") on "stores" to authenticated;
grant select("is_featured") on "stores" to authenticated;
grant select("created_at") on "stores" to authenticated;
grant select("phone") on "stores" to authenticated;
grant select("free_first_delivery") on "stores" to authenticated;
grant select("google_place_id") on "stores" to authenticated;
grant select("rating") on "stores" to authenticated;
grant select("rating_count") on "stores" to authenticated;
grant select("rating_updated_at") on "stores" to authenticated;
grant select("app_rating") on "stores" to authenticated;
grant select("app_rating_count") on "stores" to authenticated;
grant select("brand_id") on "stores" to authenticated;
grant select("branch_name") on "stores" to authenticated;
grant select("points_min_order") on "stores" to authenticated;
grant select("cashback_pct") on "stores" to authenticated;
grant select("free_delivery_min") on "stores" to authenticated;
grant select("earn_per_tjs") on "stores" to authenticated;
revoke all on function active_contacts() from public,anon,authenticated,service_role;
grant execute on function active_contacts() to authenticated;
grant execute on function active_contacts() to service_role;
revoke all on function addr_after_delete() from public,anon,authenticated,service_role;
grant execute on function addr_after_delete() to PUBLIC;
grant execute on function addr_after_delete() to authenticated;
grant execute on function addr_after_delete() to service_role;
revoke all on function addr_before_insert() from public,anon,authenticated,service_role;
grant execute on function addr_before_insert() to PUBLIC;
grant execute on function addr_before_insert() to authenticated;
grant execute on function addr_before_insert() to service_role;
revoke all on function admin_assign_driver(bigint,uuid) from public,anon,authenticated,service_role;
grant execute on function admin_assign_driver(bigint,uuid) to authenticated;
grant execute on function admin_assign_driver(bigint,uuid) to service_role;
revoke all on function admin_customers(text,integer,integer) from public,anon,authenticated,service_role;
grant execute on function admin_customers(text,integer,integer) to authenticated;
grant execute on function admin_customers(text,integer,integer) to service_role;
revoke all on function admin_set_customer_phone(uuid,text,text) from public,anon,authenticated,service_role;
grant execute on function admin_set_customer_phone(uuid,text,text) to authenticated;
grant execute on function admin_set_customer_phone(uuid,text,text) to service_role;
revoke all on function apply_as_driver() from public,anon,authenticated,service_role;
grant execute on function apply_as_driver() to authenticated;
grant execute on function apply_as_driver() to service_role;
revoke all on function assign_owner(uuid,text) from public,anon,authenticated,service_role;
grant execute on function assign_owner(uuid,text) to authenticated;
grant execute on function assign_owner(uuid,text) to service_role;
revoke all on function audit_changes() from public,anon,authenticated,service_role;
grant execute on function audit_changes() to service_role;
revoke all on function best_dishes(uuid,integer) from public,anon,authenticated,service_role;
grant execute on function best_dishes(uuid,integer) to authenticated;
grant execute on function best_dishes(uuid,integer) to service_role;
revoke all on function branch_create(uuid,text,text,double precision,double precision,text) from public,anon,authenticated,service_role;
grant execute on function branch_create(uuid,text,text,double precision,double precision,text) to authenticated;
grant execute on function branch_create(uuid,text,text,double precision,double precision,text) to service_role;
revoke all on function brand_attach(uuid,uuid,text) from public,anon,authenticated,service_role;
grant execute on function brand_attach(uuid,uuid,text) to authenticated;
grant execute on function brand_attach(uuid,uuid,text) to service_role;
revoke all on function brand_create(text,text) from public,anon,authenticated,service_role;
grant execute on function brand_create(text,text) to authenticated;
grant execute on function brand_create(text,text) to service_role;
revoke all on function brand_detach(uuid) from public,anon,authenticated,service_role;
grant execute on function brand_detach(uuid) to authenticated;
grant execute on function brand_detach(uuid) to service_role;
revoke all on function brand_route(uuid,double precision,double precision,text[]) from public,anon,authenticated,service_role;
grant execute on function brand_route(uuid,double precision,double precision,text[]) to authenticated;
grant execute on function brand_route(uuid,double precision,double precision,text[]) to service_role;
revoke all on function brand_stats(uuid,integer) from public,anon,authenticated,service_role;
grant execute on function brand_stats(uuid,integer) to authenticated;
grant execute on function brand_stats(uuid,integer) to service_role;
revoke all on function brand_sync_menu(uuid,uuid) from public,anon,authenticated,service_role;
grant execute on function brand_sync_menu(uuid,uuid) to authenticated;
grant execute on function brand_sync_menu(uuid,uuid) to service_role;
revoke all on function can_see_order(bigint) from public,anon,authenticated,service_role;
grant execute on function can_see_order(bigint) to authenticated;
grant execute on function can_see_order(bigint) to service_role;
revoke all on function cap_options() from public,anon,authenticated,service_role;
grant execute on function cap_options() to PUBLIC;
grant execute on function cap_options() to authenticated;
grant execute on function cap_options() to service_role;
revoke all on function cash_balances() from public,anon,authenticated,service_role;
grant execute on function cash_balances() to authenticated;
grant execute on function cash_balances() to service_role;
revoke all on function check_image_url(text) from public,anon,authenticated,service_role;
grant execute on function check_image_url(text) to authenticated;
grant execute on function check_image_url(text) to service_role;
revoke all on function check_promo(text,uuid,jsonb) from public,anon,authenticated,service_role;
grant execute on function check_promo(text,uuid,jsonb) to authenticated;
grant execute on function check_promo(text,uuid,jsonb) to service_role;
revoke all on function check_promo_base(text,uuid,jsonb) from public,anon,authenticated,service_role;
grant execute on function check_promo_base(text,uuid,jsonb) to service_role;
revoke all on function contacts_for(bigint[]) from public,anon,authenticated,service_role;
grant execute on function contacts_for(bigint[]) to authenticated;
grant execute on function contacts_for(bigint[]) to service_role;
revoke all on function copy_menu(uuid,uuid,boolean) from public,anon,authenticated,service_role;
grant execute on function copy_menu(uuid,uuid,boolean) to service_role;
revoke all on function courier_steps_version() from public,anon,authenticated,service_role;
grant execute on function courier_steps_version() to PUBLIC;
grant execute on function courier_steps_version() to authenticated;
grant execute on function courier_steps_version() to service_role;
revoke all on function create_ticket(bigint,text,text) from public,anon,authenticated,service_role;
grant execute on function create_ticket(bigint,text,text) to authenticated;
grant execute on function create_ticket(bigint,text,text) to service_role;
revoke all on function decide_store_request(uuid,boolean,text) from public,anon,authenticated,service_role;
grant execute on function decide_store_request(uuid,boolean,text) to authenticated;
grant execute on function decide_store_request(uuid,boolean,text) to service_role;
revoke all on function deliver_order(bigint,numeric,text,text) from public,anon,authenticated,service_role;
grant execute on function deliver_order(bigint,numeric,text,text) to authenticated;
grant execute on function deliver_order(bigint,numeric,text,text) to service_role;
revoke all on function delivery_calc(uuid,double precision,double precision,uuid) from public,anon,authenticated,service_role;
grant execute on function delivery_calc(uuid,double precision,double precision,uuid) to service_role;
revoke all on function delivery_quote(uuid,double precision,double precision) from public,anon,authenticated,service_role;
grant execute on function delivery_quote(uuid,double precision,double precision) to authenticated;
grant execute on function delivery_quote(uuid,double precision,double precision) to service_role;
revoke all on function dispatch_next(bigint) from public,anon,authenticated,service_role;
grant execute on function dispatch_next(bigint) to service_role;
revoke all on function dispatch_tick() from public,anon,authenticated,service_role;
grant execute on function dispatch_tick() to authenticated;
grant execute on function dispatch_tick() to service_role;
revoke all on function dist_km(double precision,double precision,double precision,double precision) from public,anon,authenticated,service_role;
grant execute on function dist_km(double precision,double precision,double precision,double precision) to authenticated;
grant execute on function dist_km(double precision,double precision,double precision,double precision) to service_role;
revoke all on function driver_accept(bigint) from public,anon,authenticated,service_role;
grant execute on function driver_accept(bigint) to authenticated;
grant execute on function driver_accept(bigint) to service_role;
revoke all on function driver_arrived(bigint,text) from public,anon,authenticated,service_role;
grant execute on function driver_arrived(bigint,text) to authenticated;
grant execute on function driver_arrived(bigint,text) to service_role;
revoke all on function driver_decline(bigint) from public,anon,authenticated,service_role;
grant execute on function driver_decline(bigint) to authenticated;
grant execute on function driver_decline(bigint) to service_role;
revoke all on function driver_location(double precision,double precision,double precision) from public,anon,authenticated,service_role;
grant execute on function driver_location(double precision,double precision,double precision) to authenticated;
grant execute on function driver_location(double precision,double precision,double precision) to service_role;
revoke all on function driver_ping(boolean) from public,anon,authenticated,service_role;
grant execute on function driver_ping(boolean) to authenticated;
grant execute on function driver_ping(boolean) to service_role;
revoke all on function eligible_couriers(bigint,boolean) from public,anon,authenticated,service_role;
grant execute on function eligible_couriers(bigint,boolean) to service_role;
revoke all on function group_add(uuid,uuid,integer,jsonb,text) from public,anon,authenticated,service_role;
grant execute on function group_add(uuid,uuid,integer,jsonb,text) to authenticated;
grant execute on function group_add(uuid,uuid,integer,jsonb,text) to service_role;
revoke all on function group_create(uuid) from public,anon,authenticated,service_role;
grant execute on function group_create(uuid) to authenticated;
grant execute on function group_create(uuid) to service_role;
revoke all on function group_get(uuid) from public,anon,authenticated,service_role;
grant execute on function group_get(uuid) to authenticated;
grant execute on function group_get(uuid) to service_role;
revoke all on function group_json(uuid) from public,anon,authenticated,service_role;
grant execute on function group_json(uuid) to service_role;
revoke all on function group_remove(bigint) from public,anon,authenticated,service_role;
grant execute on function group_remove(bigint) to authenticated;
grant execute on function group_remove(bigint) to service_role;
revoke all on function group_set(uuid,text) from public,anon,authenticated,service_role;
grant execute on function group_set(uuid,text) to authenticated;
grant execute on function group_set(uuid,text) to service_role;
revoke all on function guard_item_approval() from public,anon,authenticated,service_role;
grant execute on function guard_item_approval() to authenticated;
grant execute on function guard_item_approval() to service_role;
revoke all on function guard_profile() from public,anon,authenticated,service_role;
grant execute on function guard_profile() to authenticated;
grant execute on function guard_profile() to service_role;
revoke all on function handle_new_user() from public,anon,authenticated,service_role;
grant execute on function handle_new_user() to authenticated;
grant execute on function handle_new_user() to service_role;
revoke all on function happy_hour_pct(uuid,timestamp with time zone) from public,anon,authenticated,service_role;
grant execute on function happy_hour_pct(uuid,timestamp with time zone) to PUBLIC;
grant execute on function happy_hour_pct(uuid,timestamp with time zone) to authenticated;
grant execute on function happy_hour_pct(uuid,timestamp with time zone) to service_role;
revoke all on function has_perm(text) from public,anon,authenticated,service_role;
grant execute on function has_perm(text) to PUBLIC;
grant execute on function has_perm(text) to authenticated;
grant execute on function has_perm(text) to service_role;
grant execute on function has_perm(text) to anon;
revoke all on function is_admin() from public,anon,authenticated,service_role;
grant execute on function is_admin() to authenticated;
grant execute on function is_admin() to service_role;
revoke all on function item_approval() from public,anon,authenticated,service_role;
grant execute on function item_approval() to authenticated;
grant execute on function item_approval() to service_role;
revoke all on function log_order_event() from public,anon,authenticated,service_role;
grant execute on function log_order_event() to authenticated;
grant execute on function log_order_event() to service_role;
revoke all on function loyalty_balance(uuid) from public,anon,authenticated,service_role;
grant execute on function loyalty_balance(uuid) to service_role;
revoke all on function loyalty_setting(text) from public,anon,authenticated,service_role;
grant execute on function loyalty_setting(text) to service_role;
revoke all on function loyalty_spend(uuid,integer,bigint) from public,anon,authenticated,service_role;
grant execute on function loyalty_spend(uuid,integer,bigint) to service_role;
revoke all on function loyalty_summary() from public,anon,authenticated,service_role;
grant execute on function loyalty_summary() to authenticated;
grant execute on function loyalty_summary() to service_role;
revoke all on function my_offers() from public,anon,authenticated,service_role;
grant execute on function my_offers() to authenticated;
grant execute on function my_offers() to service_role;
revoke all on function my_perms() from public,anon,authenticated,service_role;
grant execute on function my_perms() to PUBLIC;
grant execute on function my_perms() to authenticated;
grant execute on function my_perms() to service_role;
grant execute on function my_perms() to anon;
revoke all on function my_rating() from public,anon,authenticated,service_role;
grant execute on function my_rating() to authenticated;
grant execute on function my_rating() to service_role;
revoke all on function norm_phone(text) from public,anon,authenticated,service_role;
grant execute on function norm_phone(text) to authenticated;
grant execute on function norm_phone(text) to service_role;
revoke all on function order_contacts(bigint) from public,anon,authenticated,service_role;
grant execute on function order_contacts(bigint) to authenticated;
grant execute on function order_contacts(bigint) to service_role;
revoke all on function order_courier_position(bigint) from public,anon,authenticated,service_role;
grant execute on function order_courier_position(bigint) to authenticated;
grant execute on function order_courier_position(bigint) to service_role;
revoke all on function owns_store(uuid) from public,anon,authenticated,service_role;
grant execute on function owns_store(uuid) to authenticated;
grant execute on function owns_store(uuid) to service_role;
revoke all on function place_order(uuid,jsonb,numeric,text,text,double precision,double precision,text,text,numeric,numeric,integer,jsonb) from public,anon,authenticated,service_role;
grant execute on function place_order(uuid,jsonb,numeric,text,text,double precision,double precision,text,text,numeric,numeric,integer,jsonb) to authenticated;
grant execute on function place_order(uuid,jsonb,numeric,text,text,double precision,double precision,text,text,numeric,numeric,integer,jsonb) to service_role;
revoke all on function price_line(uuid,jsonb) from public,anon,authenticated,service_role;
grant execute on function price_line(uuid,jsonb) to service_role;
revoke all on function promo_eval(text,numeric,uuid,boolean,numeric) from public,anon,authenticated,service_role;
grant execute on function promo_eval(text,numeric,uuid,boolean,numeric) to service_role;
revoke all on function promo_guard_version() from public,anon,authenticated,service_role;
grant execute on function promo_guard_version() to PUBLIC;
grant execute on function promo_guard_version() to authenticated;
grant execute on function promo_guard_version() to service_role;
revoke all on function rate_order(bigint,integer,integer,text) from public,anon,authenticated,service_role;
grant execute on function rate_order(bigint,integer,integer,text) to authenticated;
grant execute on function rate_order(bigint,integer,integer,text) to service_role;
revoke all on function reject_order(bigint,text,text) from public,anon,authenticated,service_role;
grant execute on function reject_order(bigint,text,text) to authenticated;
grant execute on function reject_order(bigint,text,text) to service_role;
revoke all on function reopen_rating(bigint) from public,anon,authenticated,service_role;
grant execute on function reopen_rating(bigint) to authenticated;
grant execute on function reopen_rating(bigint) to service_role;
revoke all on function report_client_error(text,text,text,text) from public,anon,authenticated,service_role;
grant execute on function report_client_error(text,text,text,text) to authenticated;
grant execute on function report_client_error(text,text,text,text) to service_role;
revoke all on function request_store(text,text,text,text,double precision,double precision,text) from public,anon,authenticated,service_role;
grant execute on function request_store(text,text,text,text,double precision,double precision,text) to authenticated;
grant execute on function request_store(text,text,text,text,double precision,double precision,text) to service_role;
revoke all on function resolve_rating(bigint,text) from public,anon,authenticated,service_role;
grant execute on function resolve_rating(bigint,text) to authenticated;
grant execute on function resolve_rating(bigint,text) to service_role;
revoke all on function set_customer_ban(uuid,boolean,text) from public,anon,authenticated,service_role;
grant execute on function set_customer_ban(uuid,boolean,text) to authenticated;
grant execute on function set_customer_ban(uuid,boolean,text) to service_role;
revoke all on function set_default_address(uuid) from public,anon,authenticated,service_role;
grant execute on function set_default_address(uuid) to authenticated;
grant execute on function set_default_address(uuid) to service_role;
revoke all on function set_my_cashback(uuid,numeric) from public,anon,authenticated,service_role;
grant execute on function set_my_cashback(uuid,numeric) to authenticated;
grant execute on function set_my_cashback(uuid,numeric) to service_role;
revoke all on function set_my_discount(text,numeric) from public,anon,authenticated,service_role;
grant execute on function set_my_discount(text,numeric) to authenticated;
grant execute on function set_my_discount(text,numeric) to service_role;
revoke all on function set_my_free_delivery(uuid,numeric) from public,anon,authenticated,service_role;
grant execute on function set_my_free_delivery(uuid,numeric) to authenticated;
grant execute on function set_my_free_delivery(uuid,numeric) to service_role;
revoke all on function set_my_phone(text) from public,anon,authenticated,service_role;
grant execute on function set_my_phone(text) to authenticated;
grant execute on function set_my_phone(text) to service_role;
revoke all on function set_order_status(bigint,order_status) from public,anon,authenticated,service_role;
grant execute on function set_order_status(bigint,order_status) to authenticated;
grant execute on function set_order_status(bigint,order_status) to service_role;
revoke all on function set_page(text,text,text) from public,anon,authenticated,service_role;
grant execute on function set_page(text,text,text) to authenticated;
grant execute on function set_page(text,text,text) to service_role;
revoke all on function set_prep_time(bigint,integer) from public,anon,authenticated,service_role;
grant execute on function set_prep_time(bigint,integer) to authenticated;
grant execute on function set_prep_time(bigint,integer) to service_role;
revoke all on function set_setting(text,numeric) from public,anon,authenticated,service_role;
grant execute on function set_setting(text,numeric) to authenticated;
grant execute on function set_setting(text,numeric) to service_role;
revoke all on function set_store_earn(uuid,numeric) from public,anon,authenticated,service_role;
grant execute on function set_store_earn(uuid,numeric) to authenticated;
grant execute on function set_store_earn(uuid,numeric) to service_role;
revoke all on function set_store_free_delivery(uuid,numeric) from public,anon,authenticated,service_role;
grant execute on function set_store_free_delivery(uuid,numeric) to authenticated;
grant execute on function set_store_free_delivery(uuid,numeric) to service_role;
revoke all on function set_store_loyalty(uuid,numeric,numeric) from public,anon,authenticated,service_role;
grant execute on function set_store_loyalty(uuid,numeric,numeric) to authenticated;
grant execute on function set_store_loyalty(uuid,numeric,numeric) to service_role;
revoke all on function set_store_open(uuid,boolean) from public,anon,authenticated,service_role;
grant execute on function set_store_open(uuid,boolean) to authenticated;
grant execute on function set_store_open(uuid,boolean) to service_role;
revoke all on function set_text_setting(text,text) from public,anon,authenticated,service_role;
grant execute on function set_text_setting(text,text) to authenticated;
grant execute on function set_text_setting(text,text) to service_role;
revoke all on function settle_driver_cash(uuid) from public,anon,authenticated,service_role;
grant execute on function settle_driver_cash(uuid) to authenticated;
grant execute on function settle_driver_cash(uuid) to service_role;
revoke all on function staff_list() from public,anon,authenticated,service_role;
grant execute on function staff_list() to authenticated;
grant execute on function staff_list() to service_role;
revoke all on function staff_remove(uuid) from public,anon,authenticated,service_role;
grant execute on function staff_remove(uuid) to authenticated;
grant execute on function staff_remove(uuid) to service_role;
revoke all on function staff_set(text,text[],boolean) from public,anon,authenticated,service_role;
grant execute on function staff_set(text,text[],boolean) to authenticated;
grant execute on function staff_set(text,text[],boolean) to service_role;
revoke all on function store_owner_info(uuid) from public,anon,authenticated,service_role;
grant execute on function store_owner_info(uuid) to authenticated;
grant execute on function store_owner_info(uuid) to service_role;
revoke all on function store_private() from public,anon,authenticated,service_role;
grant execute on function store_private() to authenticated;
grant execute on function store_private() to service_role;
revoke all on function store_speed() from public,anon,authenticated,service_role;
grant execute on function store_speed() to authenticated;
grant execute on function store_speed() to service_role;
revoke all on function ticket_reason_ok(text,text,boolean) from public,anon,authenticated,service_role;
grant execute on function ticket_reason_ok(text,text,boolean) to authenticated;
grant execute on function ticket_reason_ok(text,text,boolean) to service_role;
revoke all on function ticket_refund_room(bigint) from public,anon,authenticated,service_role;
grant execute on function ticket_refund_room(bigint) to authenticated;
grant execute on function ticket_refund_room(bigint) to service_role;
revoke all on function ticket_reply(bigint,text) from public,anon,authenticated,service_role;
grant execute on function ticket_reply(bigint,text) to authenticated;
grant execute on function ticket_reply(bigint,text) to service_role;
revoke all on function ticket_seen(bigint) from public,anon,authenticated,service_role;
grant execute on function ticket_seen(bigint) to authenticated;
grant execute on function ticket_seen(bigint) to service_role;
revoke all on function ticket_set_status(bigint,text,text,numeric) from public,anon,authenticated,service_role;
grant execute on function ticket_set_status(bigint,text,text,numeric) to authenticated;
grant execute on function ticket_set_status(bigint,text,text,numeric) to service_role;
revoke all on function ticket_staff_reply(bigint,text) from public,anon,authenticated,service_role;
grant execute on function ticket_staff_reply(bigint,text) to authenticated;
grant execute on function ticket_staff_reply(bigint,text) to service_role;
revoke all on function trg_chat_limit() from public,anon,authenticated,service_role;
grant execute on function trg_chat_limit() to PUBLIC;
grant execute on function trg_chat_limit() to authenticated;
grant execute on function trg_chat_limit() to service_role;
revoke all on function trg_check_images() from public,anon,authenticated,service_role;
grant execute on function trg_check_images() to PUBLIC;
grant execute on function trg_check_images() to authenticated;
grant execute on function trg_check_images() to service_role;
revoke all on function trg_dispatch() from public,anon,authenticated,service_role;
grant execute on function trg_dispatch() to PUBLIC;
grant execute on function trg_dispatch() to authenticated;
grant execute on function trg_dispatch() to service_role;
revoke all on function trg_fav_limit() from public,anon,authenticated,service_role;
grant execute on function trg_fav_limit() to PUBLIC;
grant execute on function trg_fav_limit() to authenticated;
grant execute on function trg_fav_limit() to service_role;
revoke all on function trg_loyalty() from public,anon,authenticated,service_role;
grant execute on function trg_loyalty() to PUBLIC;
grant execute on function trg_loyalty() to authenticated;
grant execute on function trg_loyalty() to service_role;
revoke all on function trg_profile_phone() from public,anon,authenticated,service_role;
grant execute on function trg_profile_phone() to PUBLIC;
grant execute on function trg_profile_phone() to authenticated;
grant execute on function trg_profile_phone() to service_role;
revoke all on function trg_rating_aggregate() from public,anon,authenticated,service_role;
grant execute on function trg_rating_aggregate() to PUBLIC;
grant execute on function trg_rating_aggregate() to authenticated;
grant execute on function trg_rating_aggregate() to service_role;
revoke all on function trg_rating_reward() from public,anon,authenticated,service_role;
grant execute on function trg_rating_reward() to PUBLIC;
grant execute on function trg_rating_reward() to authenticated;
grant execute on function trg_rating_reward() to service_role;
revoke all on function trg_store_phone() from public,anon,authenticated,service_role;
grant execute on function trg_store_phone() to PUBLIC;
grant execute on function trg_store_phone() to authenticated;
grant execute on function trg_store_phone() to service_role;
revoke all on function trg_wallet_immutable() from public,anon,authenticated,service_role;
grant execute on function trg_wallet_immutable() to PUBLIC;
grant execute on function trg_wallet_immutable() to authenticated;
grant execute on function trg_wallet_immutable() to service_role;
revoke all on function trg_wallet_return() from public,anon,authenticated,service_role;
grant execute on function trg_wallet_return() to PUBLIC;
grant execute on function trg_wallet_return() to authenticated;
grant execute on function trg_wallet_return() to service_role;
revoke all on function update_my_store(uuid,text,text,text) from public,anon,authenticated,service_role;
grant execute on function update_my_store(uuid,text,text,text) to authenticated;
grant execute on function update_my_store(uuid,text,text,text) to service_role;
revoke all on function validate_item() from public,anon,authenticated,service_role;
grant execute on function validate_item() to PUBLIC;
grant execute on function validate_item() to authenticated;
grant execute on function validate_item() to service_role;
revoke all on function validate_store() from public,anon,authenticated,service_role;
grant execute on function validate_store() to authenticated;
grant execute on function validate_store() to service_role;
revoke all on function wallet_adjust(uuid,numeric,text) from public,anon,authenticated,service_role;
grant execute on function wallet_adjust(uuid,numeric,text) to authenticated;
grant execute on function wallet_adjust(uuid,numeric,text) to service_role;
revoke all on function wallet_balance(uuid) from public,anon,authenticated,service_role;
grant execute on function wallet_balance(uuid) to authenticated;
grant execute on function wallet_balance(uuid) to service_role;
CREATE TRIGGER trg_item_approval BEFORE INSERT OR UPDATE OF name, price, store_id ON public.menu_items FOR EACH ROW EXECUTE FUNCTION item_approval();
CREATE TRIGGER trg_order_events AFTER INSERT OR UPDATE ON public.orders FOR EACH ROW EXECUTE FUNCTION log_order_event();
CREATE TRIGGER trg_validate_store BEFORE INSERT OR UPDATE ON public.stores FOR EACH ROW EXECUTE FUNCTION validate_store();
CREATE TRIGGER trg_guard_item_approval BEFORE UPDATE ON public.menu_items FOR EACH ROW EXECUTE FUNCTION guard_item_approval();
CREATE TRIGGER trg_validate_item BEFORE INSERT OR UPDATE ON public.menu_items FOR EACH ROW EXECUTE FUNCTION validate_item();
CREATE TRIGGER trg_order_dispatch AFTER UPDATE OF status ON public.orders FOR EACH ROW EXECUTE FUNCTION trg_dispatch();
CREATE TRIGGER trg_cap_groups BEFORE INSERT ON public.item_option_groups FOR EACH ROW EXECUTE FUNCTION cap_options();
CREATE TRIGGER trg_cap_options BEFORE INSERT ON public.item_options FOR EACH ROW EXECUTE FUNCTION cap_options();
CREATE TRIGGER trg_addr_before_insert BEFORE INSERT ON public.addresses FOR EACH ROW EXECUTE FUNCTION addr_before_insert();
CREATE TRIGGER trg_addr_after_delete AFTER DELETE ON public.addresses FOR EACH ROW EXECUTE FUNCTION addr_after_delete();
CREATE TRIGGER trg_images_menu BEFORE INSERT OR UPDATE ON public.menu_items FOR EACH ROW EXECUTE FUNCTION trg_check_images();
CREATE TRIGGER trg_images_stores BEFORE INSERT OR UPDATE ON public.stores FOR EACH ROW EXECUTE FUNCTION trg_check_images();
CREATE TRIGGER trg_images_banners BEFORE INSERT OR UPDATE ON public.banners FOR EACH ROW EXECUTE FUNCTION trg_check_images();
CREATE TRIGGER trg_audit_stores AFTER INSERT OR DELETE OR UPDATE ON public.stores FOR EACH ROW EXECUTE FUNCTION audit_changes('id', 'name', 'owner_id', 'commission_pct', 'max_discount_pct', 'discount_pct', 'is_active', 'is_open', 'fee_type', 'fee_base', 'fee_per_km', 'free_first_delivery');
CREATE TRIGGER trg_audit_promo AFTER INSERT OR DELETE OR UPDATE ON public.promo_codes FOR EACH ROW EXECUTE FUNCTION audit_changes('id', 'code', 'kind', 'value', 'min_order', 'max_uses', 'is_active', 'starts_at', 'ends_at');
CREATE TRIGGER trg_audit_banners AFTER INSERT OR DELETE OR UPDATE ON public.banners FOR EACH ROW EXECUTE FUNCTION audit_changes('id', 'title', 'is_active', 'placement', 'starts_at', 'ends_at', 'link_type', 'link_value');
CREATE TRIGGER trg_audit_items AFTER UPDATE ON public.menu_items FOR EACH ROW EXECUTE FUNCTION audit_changes('id', 'price', 'approved', 'available', 'discount_pct');
CREATE TRIGGER trg_audit_orders AFTER UPDATE ON public.orders FOR EACH ROW EXECUTE FUNCTION audit_changes('id', 'driver_id', 'cash_settled_at');
CREATE TRIGGER trg_audit_ratings AFTER UPDATE ON public.ratings FOR EACH ROW EXECUTE FUNCTION audit_changes('order_id', 'handled_at', 'handled_note');
CREATE TRIGGER trg_chat_limit BEFORE INSERT ON public.order_chat FOR EACH ROW EXECUTE FUNCTION trg_chat_limit();
CREATE TRIGGER trg_fav_limit BEFORE INSERT ON public.favorites FOR EACH ROW EXECUTE FUNCTION trg_fav_limit();
CREATE TRIGGER trg_store_phone BEFORE INSERT OR UPDATE ON public.stores FOR EACH ROW EXECUTE FUNCTION trg_store_phone();
CREATE TRIGGER trg_audit_settings AFTER UPDATE ON public.app_settings FOR EACH ROW EXECUTE FUNCTION audit_changes('key', 'value');
CREATE TRIGGER trg_rating_aggregate AFTER INSERT ON public.ratings FOR EACH ROW EXECUTE FUNCTION trg_rating_aggregate();
CREATE TRIGGER trg_audit_texts AFTER UPDATE ON public.app_texts FOR EACH ROW EXECUTE FUNCTION audit_changes('key', 'value');
CREATE TRIGGER trg_audit_tickets AFTER UPDATE ON public.support_tickets FOR EACH ROW EXECUTE FUNCTION audit_changes('id', 'status', 'refund_amount');
CREATE TRIGGER trg_wallet_no_update BEFORE UPDATE ON public.wallet_entries FOR EACH ROW EXECUTE FUNCTION trg_wallet_immutable();
CREATE TRIGGER trg_orders_wallet_return BEFORE UPDATE OF status ON public.orders FOR EACH ROW EXECUTE FUNCTION trg_wallet_return();
CREATE TRIGGER trg_guard_profile BEFORE UPDATE ON public.profiles FOR EACH ROW EXECUTE FUNCTION guard_profile();
CREATE TRIGGER trg_audit_profiles AFTER UPDATE ON public.profiles FOR EACH ROW EXECUTE FUNCTION audit_changes('id', 'role', 'driver_status', 'cash_limit', 'accept_blocked', 'banned_at', 'banned_reason', 'phone');
CREATE TRIGGER trg_profile_phone BEFORE UPDATE OF phone ON public.profiles FOR EACH ROW EXECUTE FUNCTION trg_profile_phone();
CREATE TRIGGER trg_audit_pages AFTER UPDATE ON public.app_pages FOR EACH ROW EXECUTE FUNCTION audit_changes('slug', 'updated_at');
CREATE TRIGGER trg_ratings_reward AFTER INSERT ON public.ratings FOR EACH ROW EXECUTE FUNCTION trg_rating_reward();
CREATE TRIGGER trg_orders_loyalty BEFORE UPDATE OF status ON public.orders FOR EACH ROW EXECUTE FUNCTION trg_loyalty();