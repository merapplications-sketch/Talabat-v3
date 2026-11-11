"""Add isolated PRICE01 checks to pinned sources; never edit their history."""
from pathlib import Path
import hashlib
root=Path('tests/price01-impl')
def once(s,a,b):
 assert s.count(a)==1,('source drift',a,s.count(a));return s.replace(a,b,1)
s=Path('tests/tip02-null01/acceptance.sql').read_text()
s=once(s,'declare v_build_prev text;','declare v_price_expected jsonb; v_price_lines jsonb; v_price_ids uuid[]:=array[]::uuid[]; v_price_id uuid; v_build_prev text;')
s=once(s,'  select key_id,secret into v_key_id,v_secret',"  v_price_expected:=security_private.price01_normalize(p_extra->'price01');\n  select key_id,secret into v_key_id,v_secret")
s=once(s,"values (v_id, v_item.id, v_item.name, (pl->>'unit')::numeric, it.qty, it.note, pl->'snap');", "values (v_id, v_item.id, v_item.name, (pl->>'unit')::numeric, it.qty, it.note, pl->'snap') returning id into v_price_id;\n    v_price_ids:=array_append(v_price_ids,v_price_id);")
rd='round(oi.price * oi.qty * greatest(s.discount_pct, coalesce(m.discount_pct, 0)) / 100, 2)'
ad='round(oi.price * oi.qty * greatest(s.discount_pct, coalesce(m.discount_pct, 0), v_hh) / 100, 2)'
s=once(s,'    into v_sub, v_disc, v_all, v_base',", jsonb_agg(security_private.price01_line(oi.item_id,oi.qty,oi.price,oi.options,\n        p_items->(array_position(v_price_ids,oi.id)-1)->'options',"+rd+','+ad+") order by array_position(v_price_ids,oi.id))\n    into v_sub, v_disc, v_all, v_base, v_price_lines")
# Preserve original financial expressions AND write ordering. This is a real
# creation attempt, not a quote endpoint. Any mismatch aborts its subtransaction.
guard="""  perform security_private.price01_assert(v_price_expected,security_private.price01_saved(v_id,v_price_ids,v_price_lines));
"""
s=once(s,'  if v_gid is not null then update group_orders',guard+'  if v_gid is not null then update group_orders')
s=once(s,"  return jsonb_build_object('status','created'", "  -- Re-read after all candidate helpers/triggers/binding insert; no later pricing write is allowed.\n  perform security_private.price01_assert(v_price_expected,security_private.price01_saved(v_id,v_price_ids,v_price_lines));\n  return jsonb_build_object('status','created'")
wrapper=Path('tests/native104/functions.sql').read_text().split('create or replace function public.place_order103',1)[1].split('create or replace function public.place_order(',1)[0]
wrapper='create or replace function public.place_order103'+wrapper
wrapper=once(wrapper,'declare result jsonb;','declare result jsonb;price_detail text;')
wrapper=once(wrapper,' exception\n',' exception\n  when sqlstate \'P0102\' then\n   get stacked diagnostics price_detail=PG_EXCEPTION_DETAIL;\n   return jsonb_build_object(\'status\',\'rejected\',\'reason\',\'price_changed\',\'key\',p_key,\'price_review\',price_detail::jsonb);\n  when sqlstate \'P0101\' or sqlstate \'P0103\' then\n   return jsonb_build_object(\'status\',\'rejected\',\'reason\',SQLERRM,\'key\',p_key);\n')
closure=Path('tests/native105/resources.sql').read_text().split('create or replace function public.place_order104',1)[1].split('create or replace function public.order_request_status104',1)[0]
closure='create or replace function public.place_order104'+closure
closure=once(closure,' return security_private.closure_result104(p_key);'," s:=security_private.closure_result104(p_key);\n if r->>'reason'='price_changed' and r ? 'price_review' then s:=s||jsonb_build_object('price_review',r->'price_review');end if;\n return s;")
out='-- Generated PRICE01 isolated candidate. Apply atomically AFTER accepted NULL01.\n'+(root/'helpers.sql').read_text()+'\n'+s+'\n'+wrapper+'\n'+closure
(root/'candidate.sql').write_text(out)
# Recovery-only rollback also closes the private entry; unlike reverting the source.
rollback=Path('tests/native104/rollback.sql').read_text()
private=rollback.split('create or replace function public.place_order103',1)[1].split('-- Legacy public.place_order',1)[0]
rollback+='\ncreate or replace function security_private.create_order103'+private
(root/'rollback.sql').write_text(rollback)
print('Built PRICE01 candidate and recovery-only rollback; original files untouched.')
