-- Patch 25: About and Privacy pages that the administrator edits (Russian and English), instead of fixed text in the app
-- Run once in Supabase SQL Editor AFTER patch 24. Safe to re-run (it never overwrites text you already edited).
--
-- ROW LEVEL SECURITY / PERMISSIONS
--   app_pages : every signed-in user can READ; nobody writes directly. Only set_page() (admin only) changes the text.

create table if not exists app_pages (
  slug text primary key check (slug in ('about', 'privacy')),
  body_ru text not null default '' check (char_length(body_ru) <= 20000),
  body_en text not null default '' check (char_length(body_en) <= 20000),
  updated_at timestamptz not null default now(),
  updated_by uuid
);
alter table app_pages enable row level security;
drop policy if exists pages_read on app_pages;
create policy pages_read on app_pages for select using (auth.uid() is not null);
revoke insert, update, delete on app_pages from anon, authenticated;

-- starting texts: a draft to be edited from the admin panel (only inserted when the row does not exist yet)
insert into app_pages(slug, body_ru, body_en) values
 ('about', $t$Talabat — сервис доставки еды и продуктов.

Заказывайте из ресторанов, магазинов и аптек вашего города: курьер заберёт заказ у заведения и привезёт к вам. Следите за заказом в приложении, общайтесь с курьером и оплачивайте удобным способом.

Если что-то пошло не так, напишите в поддержку из раздела «Поддержка» в профиле — мы поможем.$t$, $t$Talabat is a food and grocery delivery service.

Order from restaurants, shops and pharmacies in your city: a courier picks the order up and brings it to you. Follow your order in the app, chat with the courier and pay in a convenient way.

If something goes wrong, write to support from the “Support” section of your profile — we will help.$t$),
 ('privacy', $t$Политика конфиденциальности

1. Какие данные мы собираем
Имя, номер телефона, адрес электронной почты, адреса доставки и их координаты, историю заказов и обращений в поддержку. Во время смены курьера — его местоположение.

2. Зачем они нужны
Чтобы принимать и доставлять заказы, связывать вас с курьером, считать стоимость доставки, помогать вам в поддержке и защищать сервис от злоупотреблений.

3. Кому мы их показываем
Ресторан видит состав заказа и время, но не ваш номер телефона. Курьер видит ваше имя, адрес и номер телефона только на время активного заказа. Администрация сервиса видит данные, необходимые для работы и поддержки.

4. Хранение и защита
Данные хранятся на защищённых серверах. Доступ к ним ограничен правилами доступа, а важные действия фиксируются в журнале.

5. Ваши права
Вы можете изменить имя и номер телефона в настройках, а также попросить удалить аккаунт, написав в поддержку.

6. Изменения
Мы можем обновлять эту политику. Актуальная версия всегда находится в приложении.

Вопросы по конфиденциальности — через раздел «Поддержка».$t$, $t$Privacy policy

1. What we collect
Your name, phone number, email address, delivery addresses and their coordinates, your order history and support requests. During a courier's shift — his location.

2. Why we need it
To accept and deliver orders, connect you with the courier, calculate the delivery price, help you in support and protect the service from abuse.

3. Who can see it
The restaurant sees the order contents and times, but not your phone number. The courier sees your name, address and phone number only while an order is active. The service administration sees the data needed for operation and support.

4. Storage and protection
Data is stored on protected servers. Access is limited by access rules and important actions are written to a log.

5. Your rights
You can change your name and phone number in settings, and ask for your account to be deleted by writing to support.

6. Changes
We may update this policy. The current version is always in the app.

Questions about privacy — through the “Support” section.$t$)
on conflict (slug) do nothing;

create or replace function set_page(p_slug text, p_lang text, p_body text) returns void
language plpgsql security definer set search_path = public as $$
declare v_b text := coalesce(p_body, '');
begin
  if not is_admin() then raise exception 'not_allowed'; end if;
  if p_slug not in ('about', 'privacy') or p_lang not in ('ru', 'en') or char_length(v_b) > 20000 then raise exception 'bad_value'; end if;
  if p_lang = 'ru' then
    update app_pages set body_ru = v_b, updated_at = now(), updated_by = auth.uid() where slug = p_slug;
  else
    update app_pages set body_en = v_b, updated_at = now(), updated_by = auth.uid() where slug = p_slug;
  end if;
end $$;
revoke all on function set_page(text, text, text) from public, anon;
grant execute on function set_page(text, text, text) to authenticated;

drop trigger if exists trg_audit_pages on app_pages;
create trigger trg_audit_pages after update on app_pages for each row execute function audit_changes('slug', 'updated_at');
