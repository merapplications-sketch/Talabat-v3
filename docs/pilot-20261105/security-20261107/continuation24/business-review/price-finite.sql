alter table public.menu_items add constraint menu_items_price_finite check (price not in ('NaN'::numeric,'Infinity'::numeric,'-Infinity'::numeric));
alter table public.stores add constraint stores_delivery_fees_finite check (fee_base not in ('NaN'::numeric,'Infinity'::numeric,'-Infinity'::numeric) and fee_per_km not in ('NaN'::numeric,'Infinity'::numeric,'-Infinity'::numeric));
