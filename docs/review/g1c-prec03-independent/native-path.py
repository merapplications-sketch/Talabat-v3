"""Local-only precision probe; needs the already-received private AUDIT107 extracts.
Never connects to Supabase. The fixture is deliberately partial, not target equivalence.
Source functions are read unchanged. All created rows and settings are synthetic.
"""
import json, hashlib, subprocess, pathlib, os, datetime, re, uuid

ROOT=pathlib.Path(__file__).resolve().parent
PG=pathlib.Path(os.environ['PRECISION_PG_BIN'])
DATA=ROOT/'runtime'/'data'
defs=json.loads((ROOT/'private-inputs/selected-definitions.json').read_text())
catalog=json.loads((ROOT/'private-inputs/catalog-excerpts.json').read_text())
inputs=json.loads((ROOT/'input-results.json').read_text())
source=(ROOT/'source/isolation.sql').read_text()
assert hashlib.sha1(('blob '+str(len(source.encode()))+'\0').encode()+source.encode()).hexdigest()=='47c7e72784cf36a77c638ac4726560ad1b270ff9'
oids=[18428,18466,18472,18475,18487,18505,18506,18525,18528,18536]
selected=[next(d for d in defs if d['oid']==oid) for oid in oids]
# Exact read-back trigger DDL from catalog snippets; no runtime trigger substitutions.
triggers={}
def objects(s):
 for pos in (m.start() for m in re.finditer(r'\{',s)):
  try:
   value,_=json.JSONDecoder().raw_decode(s[pos:])
   if isinstance(value,dict):yield value
  except json.JSONDecodeError:pass
for f in catalog:
 if f['name']=='target-triggers.json':
  for m in f['matches']:
   for ob in objects(m['content']):
    if ob.get('oid') in [18658,18645,18652,18642,18646,18675] and 'definition' in ob:triggers[ob['oid']]=ob['definition']
assert len(triggers)==6
constraints={}
for f in catalog:
 if f['name']=='target-constraints.json':
  for m in f['matches']:
   for ob in objects(m['content']):
    if 'name' in ob and 'definition' in ob:constraints[ob['name']]=ob['definition']
required=['menu_items_price_check','menu_items_price_finite','stores_earn_per_tjs_check','item_options_price_delta_check']
assert all(x in constraints for x in required),constraints.keys()
assert all(constraints[x].startswith('CHECK (') for x in required)
assert constraints['menu_items_price_check']=='CHECK (price >= 0::numeric)'
schema=r'''
create schema auth;
-- Fixture identity only: real Auth/RLS and all external writers are NOT represented.
create function auth.uid() returns uuid language sql as $$select '90000000-0000-4000-8000-000000000001'::uuid$$;
create function public.is_admin() returns boolean language sql as $$select true$$;
create function public.has_perm(text) returns boolean language sql as $$select true$$;
-- Image helper substitute: only null images used. No price behavior added.
create function public.check_image_url(text) returns boolean language sql as $$select $1 is null$$;
create table stores(id uuid primary key, category text, discount_pct numeric default 0, max_discount_pct numeric default 100, earn_per_tjs numeric, cashback_pct numeric, free_delivery_min numeric default 0);
create table menu_items(id uuid primary key,store_id uuid references stores,name text not null,price numeric not null,discount_pct numeric not null default 0,approved boolean default true,available boolean default true,image_url text,popular boolean default false,section text);
create table item_option_groups(id uuid primary key,item_id uuid,name text,max_sel int,required boolean,sort int,created_at timestamptz);
create table item_options(id uuid primary key,group_id uuid,name text,price_delta numeric not null default 0,available boolean,sort int);
create table orders(id uuid primary key,store_id uuid,customer_id uuid,status text,subtotal numeric not null default 0,discount numeric not null default 0,promo_discount numeric not null default 0,points_value numeric not null default 0,points_earned integer not null default 0,cashback numeric default 0,points_used integer default 0,loyalty_done_at timestamptz,points_returned_at timestamptz);
create table order_items(order_id uuid,item_id uuid,name text,price numeric not null,qty integer,note text,options jsonb);
create table app_settings(key text primary key,value numeric not null,updated_at timestamptz,updated_by uuid);
create table loyalty_lots(user_id uuid,points int,points_left int,expires_at timestamptz,order_id uuid,kind text);
create unique index fixture_earn on loyalty_lots(order_id) where kind='earn';
create unique index fixture_return on loyalty_lots(order_id) where kind='return';
create table loyalty_ledger(user_id uuid,points int,kind text,order_id uuid);
create table wallet_entries(user_id uuid,amount numeric(12,2) not null,kind text,order_id uuid,note text);
create unique index fixture_cashback on wallet_entries(order_id) where kind='cashback';
create table audit_log(user_id uuid,action text,table_name text,row_id text,details jsonb);
create table qa_results(seq serial,id text,status text,observed jsonb);
create function qa_assert(n text,b boolean,o jsonb default '{}'::jsonb) returns void language plpgsql as $$begin if b is distinct from true then raise exception 'QA assertion failed: %: %',n,o;end if;insert into qa_results(id,status,observed)values(n,'PASS',o);end$$;
'''
for n,table in zip(required,['menu_items','menu_items','stores','item_options']):
 schema+=f'\nalter table {table} add constraint {n} {constraints[n]};'
schema+='\n'+'\n'.join(d['definition'].rstrip().rstrip(';')+';' for d in selected)
schema+='\n'+'\n'.join(t+';' for t in triggers.values())
# Order pricing/aggregation are literal blocks from source106. Identity/dispatch/promo/wallet/order RPC lifecycle are outside this precision probe.
lineblock=source[source.index('  for it in select (x->>\'item_id\')'):source.index('  -- each line gets')]
sumblock=source[source.index('  select sum(oi.price * oi.qty)'):source.index('  -- free delivery above')]
schema+='''
create function qa_price_path(v_id uuid,p_store uuid,p_items jsonb) returns void language plpgsql as $$
declare it record;v_item menu_items;pl jsonb;s stores;v_sub numeric;v_disc numeric;v_all numeric;v_base numeric;v_hh numeric:=0;v_hdisc numeric;
begin
 select * into strict s from stores where id=p_store;
'''+lineblock+sumblock+'''
 update orders set subtotal=v_sub,discount=v_disc+v_hdisc where id=v_id;
end$$;
'''
insert=inputs['insert']['json']; update=inputs['update']['json']
schema+=r'''
insert into stores(id,category,earn_per_tjs,cashback_pct) values ('10000000-0000-4000-8000-000000000001','restaurant',10,0);
insert into app_settings(key,value) values ('loyalty_earn_per_tjs',10),('loyalty_expiry_days',90),('cashback_pct',0);
'''
schema+=f"""
insert into menu_items(id,store_id,name,price,discount_pct,image_url)
select '20000000-0000-4000-8000-000000000001',(j->>'store_id')::uuid,j->>'name',(j->>'price')::numeric,(j->>'discount_pct')::numeric,j->>'image_url'
from (select $json${insert}$json$::jsonb j) d;
select qa_assert('PG01-JSON-insert-exact-with-item-triggers',price=12.00000001,jsonb_build_object('price',price::text,'scale',scale(price))) from menu_items;
update menu_items set price=12;
update menu_items set price=(($json${update}$json$::jsonb)->>'price')::numeric;
select qa_assert('PG02-JSON-update-exact-with-item-triggers',price=12.00000001,jsonb_build_object('price',price::text,'audit_rows',(select count(*) from audit_log))) from menu_items;
"""
schema+=r'''
do $$declare x numeric; rejected int:=0; begin
 foreach x in array array[-1::numeric,'NaN'::numeric,'Infinity'::numeric,'-Infinity'::numeric] loop
  begin update menu_items set price=x; exception when check_violation then rejected:=rejected+1;end;
 end loop;
 perform qa_assert('PG03-price-checks-reject-negative-nonfinite',rejected=4,jsonb_build_object('rejected',rejected));
end$$;
select set_store_earn('10000000-0000-4000-8000-000000000001',10);
select set_setting('loyalty_earn_per_tjs',10);
do $$declare n int:=0;begin
 begin perform set_store_earn('10000000-0000-4000-8000-000000000001',10.5);exception when others then if sqlerrm='bad_value' then n:=n+1;else raise;end if;end;
 begin perform set_setting('loyalty_earn_per_tjs',10.5);exception when others then if sqlerrm='bad_value' then n:=n+1;else raise;end if;end;
 begin update stores set earn_per_tjs=10.5;exception when check_violation then n:=n+1;end;
 perform qa_assert('PG04-integer-rate-guards-and-store-constraint',n=3,jsonb_build_object('rejected',n,'synthetic_rate',10));
end$$;
insert into orders(id,store_id,customer_id,status) values ('30000000-0000-4000-8000-000000000001','10000000-0000-4000-8000-000000000001','90000000-0000-4000-8000-000000000001','pickedup');
select qa_price_path('30000000-0000-4000-8000-000000000001','10000000-0000-4000-8000-000000000001','[{"item_id":"20000000-0000-4000-8000-000000000001","qty":1,"options":[]}]');
select qa_assert('PG05-price-line-and-order-item-preserve-scale',price=12.00000001,jsonb_build_object('order_item_price',price::text,'scale',scale(price))) from order_items;
select qa_assert('PG06-aggregate-retains-fraction-at-loyalty-input',subtotal=12.00000001 and discount=0 and promo_discount=0 and points_value=0,jsonb_build_object('subtotal',subtotal::text,'discount',discount::text,'promo_discount',promo_discount::text,'points_value',points_value::text)) from orders;
update orders set status='delivered';
-- Approved expected 121 is imported from the accepted G1-C analysis; no oracle runs the tested formula.
select qa_assert('PG07-captured-trigger-reproduces-known-shortfall',points_earned=120 and points_earned<>121 and (select sum(points) from loyalty_lots where kind='earn')=120 and (select sum(points) from loyalty_ledger where kind='earn')=120,
 jsonb_build_object('actual_points',points_earned,'approved_expected_points',121,'loyalty_lot_points',(select sum(points) from loyalty_lots where kind='earn'),'loyalty_ledger_points',(select sum(points) from loyalty_ledger where kind='earn'),'verdict','PRECISION_GAP_REPRODUCED')) from orders;
-- A numeric(12,2) target elsewhere is not an implicit cast of the order subtotal.
select qa_assert('PG08-unrelated-fixed-scale-does-not-normalize-input',subtotal=12.00000001 and subtotal::numeric(12,2)=12.00 and (select count(*) from wallet_entries)=0,jsonb_build_object('subtotal',subtotal::text,'fixed_scale_control',(subtotal::numeric(12,2))::text,'wallet_rows',0)) from orders;
-- Repeat the precision path using the captured global fallback with a synthetic documented integer setting.
select set_store_earn('10000000-0000-4000-8000-000000000001',null);
insert into orders(id,store_id,customer_id,status) values ('30000000-0000-4000-8000-000000000002','10000000-0000-4000-8000-000000000001','90000000-0000-4000-8000-000000000001','pickedup');
select qa_price_path('30000000-0000-4000-8000-000000000002','10000000-0000-4000-8000-000000000001','[{"item_id":"20000000-0000-4000-8000-000000000001","qty":1,"options":[]}]');
update orders set status='delivered' where id='30000000-0000-4000-8000-000000000002';
select qa_assert('PG09-global-fallback-reproduces-known-shortfall',points_earned=120,jsonb_build_object('actual_points',points_earned,'approved_expected_points',121,'synthetic_global_rate',10)) from orders where id='30000000-0000-4000-8000-000000000002';
'''
generated=ROOT/'runtime/probe-private.sql'; generated.write_text(schema)
def run(*a,**kw):return subprocess.run([str(x) for x in a],check=True,text=True,capture_output=True,**kw)
# Start/test/stop in one process: managed tool sessions do not preserve detached daemons.
started=False
try:
 run(PG/'pg_ctl','-D',DATA,'-l',ROOT/'runtime/postgres.log','-o',"-h 127.0.0.1 -p 42755 -k ''",'-w','start');started=True
 dbname='precision_'+uuid.uuid4().hex[:12]
 run(PG/'createdb','-h','127.0.0.1','-p','42755',dbname)
 psql=[PG/'psql','-X','-h','127.0.0.1','-p','42755','-d',dbname,'-v','ON_ERROR_STOP=1','-At']
 run(*psql,'-f',generated)
 got=run(*psql,'-c',"select jsonb_build_object('postgres',version(),'checks',(select jsonb_agg(to_jsonb(q)-'seq' order by seq) from qa_results q))").stdout.strip()
 result=json.loads(got)
 result.update({'kind':'NATIVE POSTGRESQL / partial synthetic schema, captured functions, synthetic data; no hosted HTTP','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'definition_hashes':[{'oid':d['oid'],'source_line':d.get('source_line'),'sha256_utf8':hashlib.sha256(d['definition'].encode()).hexdigest()} for d in selected],
 'exact_trigger_oids':list(triggers),'exact_constraint_names':required,
 'source_blocks':{'source106':'86eb978e1aeb2be4a9d90999dc9b5a1267cb33df','path':'tests/native106/isolation.sql','git_blob':'47c7e72784cf36a77c638ac4726560ad1b270ff9','line_block_sha256':hashlib.sha256(lineblock.encode()).hexdigest(),'sum_block_sha256':hashlib.sha256(sumblock.encode()).hexdigest()},
 'substitutes':['auth.uid synthetic identity','is_admin/has_perm true fixture helpers','check_image_url null-only helper, images null','partial tables plus local indexes for trigger ON CONFLICT','qa_price_path wrapper executes exact line/aggregation blocks; not complete order RPC','cashback=0, rate=10, no discounts/promo/redemption/options; all settings synthetic'],
 'not_proven':['current deployment','hosted API or RLS','complete target catalog/trigger equivalence','actual business setting values','native browser UI submission','all downstream delivery writers']})
 (ROOT/'native-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(result))
except subprocess.CalledProcessError as e:
 print(json.dumps({'failed_command':str(e.cmd),'stdout':e.stdout,'stderr':e.stderr}));raise
finally:
 if started: run(PG/'pg_ctl','-D',DATA,'-m','fast','-w','stop')
