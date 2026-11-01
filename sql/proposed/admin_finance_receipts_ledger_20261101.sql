-- PROPOSAL B, separate from integrity fixes. NOT APPLIED. No backfill, activation or payout calculation.
-- Schema only: no posting endpoint, no automatic settlement trigger, no external notifications.
begin;
create table public.finance_receipts (
 id uuid primary key, command_id uuid unique references finance_private.commands(request),
 direction text not null check(direction in ('driver_to_office','office_to_driver')),
 amount numeric(14,2) not null check(amount>0), subject_user uuid not null references public.profiles(id),
 recorded_by uuid not null references public.profiles(id), occurred_at timestamptz not null,
 created_at timestamptz not null default now(), note text,
 counterpart_ack_at timestamptz -- null is NOT an acknowledgement; record entry is not physical handover proof.
);
create table public.finance_receipt_orders (
 receipt_id uuid references public.finance_receipts(id), order_id bigint references public.orders(id),
 cash_amount numeric(14,2) not null check(cash_amount>=0), primary key(receipt_id,order_id)
);
create table public.finance_disbursements (
 id uuid primary key, receipt_id uuid not null unique references public.finance_receipts(id),
 driver_id uuid not null references public.profiles(id), amount numeric(14,2) not null check(amount>0),
 recorded_by uuid not null references public.profiles(id), paid_at timestamptz not null,
 approval_reference text not null check(length(btrim(approval_reference))>0)
 -- No automatic deduction from cash held, no automatic offset or new commission rules.
);
create table public.finance_notifications (
 id uuid primary key, recipient_id uuid not null references public.profiles(id),
 receipt_id uuid not null references public.finance_receipts(id), event_kind text not null check(event_kind in ('receipt_recorded','disbursement_recorded')),
 created_at timestamptz not null default now(), read_at timestamptz,
 unique(recipient_id,receipt_id,event_kind)
);
alter table public.finance_receipts enable row level security;
alter table public.finance_receipt_orders enable row level security;
alter table public.finance_disbursements enable row level security;
alter table public.finance_notifications enable row level security;
create policy finance_receipt_read on public.finance_receipts for select to authenticated using(subject_user=auth.uid() or recorded_by=auth.uid() or (public.finance_access()->>'execute')='true');
create policy finance_receipt_orders_read on public.finance_receipt_orders for select to authenticated using(exists(select 1 from public.finance_receipts r where r.id=receipt_id));
create policy finance_disbursement_read on public.finance_disbursements for select to authenticated using(driver_id=auth.uid() or recorded_by=auth.uid() or (public.finance_access()->>'execute')='true');
create policy finance_notification_read on public.finance_notifications for select to authenticated using(recipient_id=auth.uid());
-- No client can post/edit/delete a receipt, payout or notification; future writer must validate totals/linkages atomically.
revoke all on public.finance_receipts,public.finance_receipt_orders,public.finance_disbursements,public.finance_notifications from public,anon,authenticated;
grant select on public.finance_receipts,public.finance_receipt_orders,public.finance_disbursements,public.finance_notifications to authenticated;
commit;
