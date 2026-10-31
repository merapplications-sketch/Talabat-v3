/* talabat-core.js v2 — Supabase backend. Same TLB API as v1, but actions are async (use await). */
(function () {
  'use strict';
  var SB_URL = 'https://dzydscryrnahnneydnry.supabase.co';
  var SB_KEY = 'sb_publishable_zQKbsSffub7O-f87vsXAaQ_GHFnSOQz';   /* publishable key: safe in the browser, RLS protects data */
  var LK = 'tlb_lang';
  var subs = [];
  function fire() { subs.forEach(function (f) { try { f(); } catch (e) { console.error(e); } }); }
  function $(id) { return document.getElementById(id); }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }

  /* ---------- i18n RU / EN ---------- */
  var I = {
    ru: { pending: 'Ожидание подтверждения', preparing: 'Готовится', ready: 'Готов к выдаче курьеру', pickedup: 'Курьер в пути', delivered: 'Доставлено', rejected: 'Отклонён рестораном', cancelled: 'Отменён',
      err_photo_upload: 'Не удалось загрузить фото. Проверьте интернет и попробуйте ещё раз.', err_photo_required: 'Сфотографируйте заказ у двери — без фото доставку не закрыть', err_note_required: 'Добавьте пояснение', cr_out_of_stock: 'Нет блюда в наличии', cr_too_busy: 'Ресторан перегружен', cr_closing: 'Ресторан закрывается', cr_other: 'Другая причина',
      err_closed: 'Ресторан сейчас закрыт', err_unavailable: 'Товар недоступен', err_points_changed: 'Баланс баллов изменился. Проверьте сумму и оформите снова.', err_points_min: 'Недостаточно баллов для списания', err_points_min_order: 'Баллы можно списать, когда сумма блюд не меньше минимальной', err_bad_gift: 'Укажите имя и телефон получателя (+992 и 9 цифр)', err_bad_time: 'Выберите время от 45 минут до 3 дней вперёд', err_bad_group: 'Групповой заказ недоступен (закрыт или оформлен)', err_group_closed: 'Групповой заказ уже закрыт для добавления', err_too_early: 'Запланированный заказ можно начать готовить за час до времени', err_empty: 'Корзина пуста', err_bad_transition: 'Действие недоступно', err_taken: 'Заказ уже взят другим курьером',
      confirm_cancel: 'Отменить заказ?', clear_cart: 'В корзине товары другого магазина. Очистить корзину?', accept: 'Принять', reject: 'Отклонить', add: 'Добавить', cart: 'Корзина', pay: 'Оплатить заказ', online: 'На линии', offline: 'Не в сети' },
    en: { pending: 'Waiting for confirmation', preparing: 'Preparing', ready: 'Ready for courier pickup', pickedup: 'Courier on the way', delivered: 'Delivered', rejected: 'Rejected by restaurant', cancelled: 'Cancelled',
      err_photo_upload: 'Could not upload the photo. Check the internet and try again.', err_photo_required: 'Take a photo of the order at the door — the delivery cannot be closed without it', err_note_required: 'Add an explanation', cr_out_of_stock: 'A dish is out of stock', cr_too_busy: 'The restaurant is too busy', cr_closing: 'The restaurant is closing', cr_other: 'Other reason',
      err_closed: 'The restaurant is closed right now', err_unavailable: 'Item unavailable', err_points_changed: 'Your points balance changed. Check the amount and place the order again.', err_points_min: 'Not enough points to use', err_points_min_order: 'Points can be used when the dishes reach the minimum order', err_bad_gift: 'Enter the recipient\'s name and phone (+992 and 9 digits)', err_bad_time: 'Choose a time from 45 minutes to 3 days ahead', err_bad_group: 'The group order is not available (closed or placed)', err_group_closed: 'The group order is closed for new dishes', err_too_early: 'A scheduled order can be started one hour before its time', err_empty: 'Cart is empty', err_bad_transition: 'Action not allowed', err_taken: 'Order already taken by another courier',
      confirm_cancel: 'Cancel this order?', clear_cart: 'Your cart has items from another store. Clear it?', accept: 'Accept', reject: 'Reject', add: 'Add', cart: 'Cart', pay: 'Pay for order', online: 'Online', offline: 'Offline' }
  };
  var lang = 'ru';
  try { lang = localStorage.getItem(LK) || ((navigator.language || '').indexOf('en') === 0 ? 'en' : 'ru'); } catch (e) {}
  function t(k) { return (I[lang] && I[lang][k]) || I.ru[k] || k; }
  function applyI18n() {
    document.documentElement.lang = lang;
    [].forEach.call(document.querySelectorAll('[data-i18n]'), function (el) { el.textContent = t(el.getAttribute('data-i18n')); });
    [].forEach.call(document.querySelectorAll('[data-i18n-ph]'), function (el) { el.placeholder = t(el.getAttribute('data-i18n-ph')); });
  }
  var CHIP = 'background:#1f2937;color:#fff;font:700 11px sans-serif;padding:5px 11px;border-radius:12px;cursor:pointer;margin:4px 0';
  function chromeBar() {
    var w = document.getElementById('tlb-bar');
    if (!w) { w = document.createElement('div'); w.id = 'tlb-bar'; w.style.cssText = 'display:flex;justify-content:space-between;align-items:center;gap:8px;padding:0 10px;position:relative;z-index:50'; document.body.insertBefore(w, document.body.firstChild); }
    return w;
  }
  function setLang(l) { lang = l; try { localStorage.setItem(LK, l); } catch (e) {} applyI18n(); var b = document.getElementById('tlb-lang'); if (b) b.textContent = l === 'ru' ? 'RU | en' : 'ru | EN'; fire(); }
  document.addEventListener('DOMContentLoaded', function () {
    var b = document.createElement('div'); b.id = 'tlb-lang';
    b.style.cssText = CHIP;
    b.textContent = lang === 'ru' ? 'RU | en' : 'ru | EN';
    b.onclick = function () { setLang(lang === 'ru' ? 'en' : 'ru'); };
    chromeBar().appendChild(b); applyChrome(); applyI18n();   // an app that hid the chrome before this ran keeps it hidden
  });


  Object.assign(I.ru, { tagline: 'Доставка еды и продуктов', loadFail:'Не удалось загрузить данные',dbOldW:'База данных не обновлена: выполните последний SQL-патч в Supabase. Часть функций не работает.', offline:'Нет интернета — данные не обновляются', loading:'Загрузка…',bootT:'Не удалось загрузить приложение',bootS:'Проверьте интернет и нажмите «Обновить». Если не помогает — выйдите и войдите снова.',bootReload:'Обновить',bootSignout:'Выйти и войти заново',applyT:'Стать курьером',applyS:'Укажите ваш номер телефона. Администратор рассмотрит заявку и откроет вам доступ.',applyB:'Подать заявку',notLinked:'Ваш аккаунт ещё не привязан к ресторану. Сообщите администратору ваш email — он привяжет аккаунт к вашему ресторану.',authPwHint2:'Минимум 8 символов. Придумайте новый пароль для Talabat — не используйте пароль от почты.',authPhoneL:'Телефон (+992…)', authNameL:'Ваше имя',authBadEmail:'Введите корректный email, например name@mail.com',authNameShort:'Введите имя (минимум 2 буквы)',authPwShort:'Пароль слишком короткий: минимум 8 символов',authPwHint:'Минимум 8 символов',authWrong:'Неверный email или пароль',authExists:'Этот email уже зарегистрирован. Перейдите на вкладку «Вход».',authRate:'Слишком много попыток или писем. Подождите несколько минут и попробуйте снова.',authUnconf:'Email не подтверждён. Откройте письмо от нас и нажмите на ссылку.',authNoSignup:'Регистрация сейчас отключена.',authSentT:'Проверьте почту',authSentS:'Мы отправили ссылку для подтверждения на адрес:',authResend:'Отправить письмо ещё раз',authResent:'Письмо отправлено. Проверьте и папку «Спам».',authBack:'Войти',authWait:'Подождите минуту перед повторной отправкой.',authWaitB:'Подождите…', login: 'Войти', signup: 'Регистрация', password: 'Пароль', logout: 'Выйти', wrongRole: 'Этот аккаунт не подходит для этого приложения. Выйдите и войдите другим аккаунтом.',
    verL: 'Версия',
    wrongApp: 'Это приложение для другого аккаунта', roleIs: 'Ваш аккаунт зарегистрирован как: {role}. Он работает в своём приложении.', openApp: 'Открыть приложение: {role}', role_admin: 'администратор', role_merchant: 'ресторан', role_driver: 'курьер', role_customer: 'клиент',
    authLock: 'Слишком много попыток. Подождите {s} сек.',
    pendingApp: 'Ваш аккаунт ожидает одобрения администратора.', signupOk: 'Аккаунт создан. Если нужно, подтвердите почту и войдите.', err_generic: 'Ошибка. Попробуйте ещё раз.', err_bad_value: 'Проверьте значения: проценты 0–100, цены не меньше 0, телефон и координаты корректные.', err_discount_over_max: 'Скидка выше допустимого максимума.', err_bad_banner: 'Проверьте баннер: дата окончания должна быть позже даты начала.', err_promo_invalid: 'Промокод не найден или не действует.', err_refund_too_high: 'Сумма возврата больше суммы заказа (с учётом уже возвращённого по нему).', err_refund_needs_order: 'Возврат возможен только по обращению, связанному с заказом.', err_wallet_changed: 'Баланс кошелька изменился. Проверьте сумму и подтвердите заказ ещё раз.', err_insufficient_funds: 'Недостаточно средств в кошельке.', err_already_refunded: 'Возврат по этому обращению уже зачислен.', err_phone_locked: 'Номер нельзя менять, пока есть активный заказ.', err_phone_cooldown: 'Номер можно менять не чаще одного раза в 30 дней. Обратитесь в поддержку.', err_account_blocked: 'Аккаунт приостановлен. Свяжитесь с поддержкой.', err_ticket_expired: 'Срок обращения по этому заказу (48 часов) истёк.', err_ticket_exists: 'По этому заказу уже есть открытое обращение.', err_ticket_closed: 'Обращение закрыто. Создайте новое, если проблема осталась.', err_not_found: 'Не найдено.',  err_fee_changed: 'Стоимость доставки изменилась. Проверьте сумму и подтвердите заказ ещё раз.', err_too_far: 'Адрес слишком далеко от ресторана. Выберите другой адрес или ресторан поближе.', err_phone_required: 'Укажите номер телефона (+992…) в профиле.', err_bad_phone: 'Введите номер Таджикистана: +992 и 9 цифр.', err_address_required: 'Добавьте адрес доставки на карте.', err_bad_options: 'Выбор опций изменился или недоступен. Откройте блюдо и выберите заново.', err_no_offer: 'Это предложение уже недоступно.', err_busy: 'У вас уже есть активный заказ.', err_already_rated: 'Вы уже оценили этот заказ.', err_closed_now: 'Ресторан сейчас закрыт.', err_too_many_orders: 'У вас уже 5 незавершённых заказов. Дождитесь доставки.', err_rating_fail: 'Не удалось получить рейтинг из Google. Проверьте Place ID и настройку функции.', err_promo_offer: 'Промокод нельзя применить, пока у магазина действует своя скидка.', err_promo_min: 'Сумма заказа меньше минимальной для этого промокода.', err_promo_used: 'Вы уже использовали этот промокод.', err_promo_limit: 'Промокод больше недоступен.', err_too_many: 'Слишком много попыток. Попробуйте через 10 минут.', err_bad_promo: 'Проверьте промокод: код 3–20 символов (латиница, цифры), значение больше 0, процент не больше 100.',
    err_not_approved: 'Аккаунт курьера не одобрен', err_name_taken: 'Такое название уже занято', err_no_template: 'Сначала привяжите хотя бы один ресторан к бренду', err_not_allowed: 'Недостаточно прав', err_store_unavailable: 'Магазин недоступен', err_auth: 'Войдите в аккаунт', err_user_not_found: 'Пользователь не найден' });
  Object.assign(I.en, { tagline: 'Food and grocery delivery', loadFail:'Could not load the data',dbOldW:'The database is not up to date: run the latest SQL patch in Supabase. Some features do not work.', offline:'No internet — data is not updating', loading:'Loading…',bootT:'Could not load the app',bootS:'Check your internet and tap “Reload”. If it does not help, sign out and sign in again.',bootReload:'Reload',bootSignout:'Sign out and sign in again',applyT:'Become a courier',applyS:'Enter your phone number. The admin will review your request and open access for you.',applyB:'Apply',notLinked:'Your account is not linked to a restaurant yet. Send your email to the administrator — they will link the account to your restaurant.',authPwHint2:'At least 8 characters. Create a NEW password for Talabat — do not use your email password.',authPhoneL:'Phone (+992…)', authNameL:'Your name',authBadEmail:'Enter a valid email, e.g. name@mail.com',authNameShort:'Enter your name (at least 2 letters)',authPwShort:'Password is too short: at least 8 characters',authPwHint:'At least 8 characters',authWrong:'Wrong email or password',authExists:'This email is already registered. Switch to the “Sign in” tab.',authRate:'Too many attempts or emails. Wait a few minutes and try again.',authUnconf:'Email not confirmed. Open our email and tap the link.',authNoSignup:'Sign-up is currently disabled.',authSentT:'Check your email',authSentS:'We sent a confirmation link to:',authResend:'Send the email again',authResent:'Email sent. Please check your Spam folder too.',authBack:'Sign in',authWait:'Wait a minute before sending again.',authWaitB:'Please wait…', login: 'Sign in', signup: 'Sign up', password: 'Password', logout: 'Sign out', wrongRole: 'This account does not fit this app. Sign out and use another account.',
    verL: 'Version',
    wrongApp: 'This account belongs to a different app', roleIs: 'Your account is registered as: {role}. It works in its own app.', openApp: 'Open the {role} app', role_admin: 'admin', role_merchant: 'restaurant', role_driver: 'courier', role_customer: 'customer',
    authLock: 'Too many attempts. Wait {s} s.',
    pendingApp: 'Your account is waiting for admin approval.', signupOk: 'Account created. If needed, confirm your email and sign in.', err_generic: 'Something went wrong. Try again.', err_bad_value: 'Check the values: percentages 0–100, prices not negative, valid phone and coordinates.', err_discount_over_max: 'The discount is above the allowed maximum.', err_bad_banner: 'Check the banner: the end date must be after the start date.', err_promo_invalid: 'Promo code not found or not active.', err_refund_too_high: 'The refund is more than the order was worth (counting what was already refunded on it).', err_refund_needs_order: 'A refund is possible only on a request linked to an order.', err_wallet_changed: 'The wallet balance has changed. Check the amount and confirm the order again.', err_insufficient_funds: 'Not enough funds in the wallet.', err_already_refunded: 'The refund for this request has already been credited.', err_phone_locked: 'You cannot change the number while you have an active order.', err_phone_cooldown: 'The number can be changed only once every 30 days. Contact support.', err_account_blocked: 'Your account is suspended. Please contact support.', err_ticket_expired: 'The 48-hour window for this order has passed.', err_ticket_exists: 'There is already an open request for this order.', err_ticket_closed: 'This request is closed. Create a new one if the problem remains.', err_not_found: 'Not found.',  err_fee_changed: 'The delivery fee has changed. Check the total and confirm the order again.', err_too_far: 'The address is too far from the restaurant. Choose another address or a closer restaurant.', err_phone_required: 'Add your phone number (+992…) in your profile.', err_bad_phone: 'Enter a Tajikistan number: +992 and 9 digits.', err_address_required: 'Add a delivery address on the map.', err_bad_options: 'The selected options changed or are unavailable. Open the dish and choose again.', err_no_offer: 'This offer is no longer available.', err_busy: 'You already have an active order.', err_already_rated: 'You have already rated this order.', err_closed_now: 'The restaurant is closed right now.', err_too_many_orders: 'You already have 5 unfinished orders. Please wait for delivery.', err_rating_fail: 'Could not get the rating from Google. Check the Place ID and the function setup.', err_promo_offer: 'Promo codes cannot be used while the store has its own discount.', err_promo_min: 'The order is below the minimum for this promo code.', err_promo_used: 'You have already used this promo code.', err_promo_limit: 'This promo code is no longer available.', err_too_many: 'Too many attempts. Try again in 10 minutes.', err_bad_promo: 'Check the promo: code 3–20 characters (letters, digits), value above 0, percent up to 100.',
    err_not_approved: 'Courier account is not approved', err_name_taken: 'This name is already taken', err_no_template: 'Attach at least one restaurant to the brand first', err_not_allowed: 'Not allowed', err_store_unavailable: 'Store unavailable', err_auth: 'Please sign in', err_user_not_found: 'User not found' });

  /* ---------- Extra dictionary ---------- */
  Object.assign(I.ru, { rs_not_delivered: 'Заказ не доставлен', rs_wrong_order: 'Привезли не тот заказ', rs_missing_items: 'Не хватает блюд', rs_quality: 'Качество еды', rs_late: 'Заказ сильно опоздал', rs_courier: 'Проблема с курьером', rs_restaurant: 'Проблема с рестораном', rs_payment: 'Оплата или возврат', rs_other: 'Другое' });
  Object.assign(I.en, { rs_not_delivered: 'Order not delivered', rs_wrong_order: 'Wrong order delivered', rs_missing_items: 'Missing items', rs_quality: 'Food quality', rs_late: 'Order very late', rs_courier: 'Problem with the courier', rs_restaurant: 'Problem with the restaurant', rs_payment: 'Payment or refund', rs_other: 'Other' });
  Object.assign(I.ru, { saved: 'Сохранено ✓', apple: 'Apple Pay', card: 'Карта Alif', cash: 'Наличными', openMap: 'Открыть на карте', locTitle: 'Отправить местоположение',
    locHint:'Двигайте карту: метка в центре показывает точку доставки.',locDenied:'Доступ к геопозиции запрещён. Включите его для Safari в настройках iPhone.',locFail:'Не удалось определить местоположение. Выйдите на открытое место.',locNA:'Это устройство не поддерживает геолокацию.', locSend: 'Отправить это место', mapFail: 'Не удалось загрузить карту', chatClosed: 'Чат закрыт',
    err_blocked: 'Приём заказов остановлен администратором', err_cash_required: 'Укажите полученную сумму', err_note_required: 'Укажите причину, если сумма отличается' });
  Object.assign(I.en, { saved: 'Saved ✓', apple: 'Apple Pay', card: 'Alif card', cash: 'Cash', openMap: 'Open on map', locTitle: 'Send location',
    locHint:'Move the map: the pin in the centre marks the delivery point.',locDenied:'Location access is denied. Turn it on for Safari in iPhone Settings.',locFail:'Cannot get your location. Move to an open area.',locNA:'This device does not support location.', locSend: 'Send this location', mapFail: 'Could not load the map', chatClosed: 'Chat closed',
    err_blocked: 'New orders are paused by the admin', err_cash_required: 'Enter the amount received', err_note_required: 'Add a reason if the amount differs' });

  /* ---------- UI helpers: toast, sound, chrome, location ---------- */
  function toast(msg, bad) {
    var d = document.createElement('div'); d.textContent = msg;
    d.style.cssText = 'position:fixed;left:50%;bottom:96px;transform:translateX(-50%);z-index:10001;background:' + (bad ? '#e74c3c' : '#27ae60') + ';color:#fff;font:700 13px -apple-system,BlinkMacSystemFont,sans-serif;padding:10px 18px;border-radius:22px;box-shadow:0 4px 14px #0004;max-width:86%;text-align:center';
    document.body.appendChild(d); setTimeout(function () { d.remove(); }, 2300);
  }
  var AC = null;
  function unlock() { try { if (!AC) AC = new (window.AudioContext || window.webkitAudioContext)(); if (AC.state === 'suspended') { var pending = AC.resume(); if (pending && typeof pending.catch === 'function') pending.catch(function () { }); } } catch (e) { } }
  ['touchstart', 'click'].forEach(function (ev) { document.addEventListener(ev, unlock, { passive: true }); });
  function beep() {
    try { unlock(); [0, 0.35].forEach(function (d) { var o = AC.createOscillator(), g = AC.createGain(); o.frequency.value = 880; g.gain.setValueAtTime(0.2, AC.currentTime + d); g.gain.exponentialRampToValueAtTime(0.001, AC.currentTime + d + 0.28); o.connect(g); g.connect(AC.destination); o.start(AC.currentTime + d); o.stop(AC.currentTime + d + 0.3); }); } catch (e) { }
  }
  var ringT = null;
  function audioOk() { return !!AC && AC.state === 'running'; }
  function ringBeep() {
    try { unlock(); [0, 0.22, 0.44].forEach(function (d, i) { var o = AC.createOscillator(), g = AC.createGain(); o.frequency.value = i === 1 ? 1175 : 988; g.gain.setValueAtTime(0.28, AC.currentTime + d); g.gain.exponentialRampToValueAtTime(0.001, AC.currentTime + d + 0.18); o.connect(g); g.connect(AC.destination); o.start(AC.currentTime + d); o.stop(AC.currentTime + d + 0.2); }); } catch (e) { }
  }
  function ring(on) {
    if (on) { if (ringT) return; ringBeep(); ringT = setInterval(ringBeep, 2600); }
    else if (ringT) { clearInterval(ringT); ringT = null; }
  }
  function unlockNow() {
    unlock();
    try { var b = AC.createBuffer(1, 1, 22050), src = AC.createBufferSource(); src.buffer = b; src.connect(AC.destination); src.start(0); } catch (e) { }
    return audioOk();
  }
  var chromeOn = true;
  function applyChrome() { ['tlb-lang', 'tlb-out'].forEach(function (id) { var e = $(id); if (e) e.style.display = chromeOn ? '' : 'none'; }); }
  function fmtMsg(txt) {
    var m = /^LOC:(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)$/.exec(String(txt));
    // 31 Oct: a shared point opens a choice of maps for exactly these coordinates (no provider forced)
    if (m) return '<a href="#" role="button" onclick="return TLB.openPoint(' + (+m[1]) + ',' + (+m[2]) + ')" style="color:inherit;font-weight:700;text-decoration:underline">📍 ' + esc(t('openMap')) + '</a>';
    return esc(txt);
  }
  function loadLeaflet(cb, fail) {
    if (window.L) return cb();
    var l = document.createElement('link'); l.rel = 'stylesheet'; l.href = 'https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css'; document.head.appendChild(l);
    var s = document.createElement('script'); s.src = 'https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js';
    s.onload = cb; s.onerror = function () { if (fail) fail(); else toast(t('mapFail'), true); }; document.head.appendChild(s);
  }
  /* One-time (not live) location: map opens on the device position, the user can drag the pin or tap the map. */
  function pickLocation(cb, start, hooks) {
    hooks = hooks || {}; var alive = true, loadTimer;
    function state(phase, key) { if (hooks.onState) hooks.onState(phase, key); }
    function loadFail() { if (!alive) return; alive = false; clearTimeout(loadTimer); state('error', 'locMapFail'); if (!hooks.onState) toast(t('locMapFail'), true); }
    state('loading'); loadTimer = setTimeout(loadFail, 15000);
    loadLeaflet(function () {
      if (!alive) return; if (!window.L || typeof L.map !== 'function') { loadFail(); return; } clearTimeout(loadTimer);
      if (hooks.canOpen && !hooks.canOpen()) { alive = false; state('cancelled'); return; }
      state('selecting');
      var ov = document.createElement('div');
      ov.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;z-index:10000;background:#fff;display:flex;flex-direction:column;font-family:-apple-system,BlinkMacSystemFont,sans-serif';
      var PIN = '<svg viewBox="0 0 34 44" width="34" height="44"><path d="M17 0C7.6 0 0 7.4 0 16.6 0 29 17 44 17 44s17-15 17-27.4C34 7.4 26.4 0 17 0z" fill="#f1511b"/><circle cx="17" cy="16.5" r="6.5" fill="#fff"/></svg>';
      var ME_ICON = '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="#f1511b" stroke-width="2.2" stroke-linecap="round"><circle cx="12" cy="12" r="3.5"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/><circle cx="12" cy="12" r="8"/></svg>';
      ov.innerHTML = '<div style="padding:calc(12px + env(safe-area-inset-top,0px)) 14px 12px;display:flex;justify-content:space-between;align-items:center;font-weight:700;font-size:17px"><span data-i18n="locTitle"></span><button id="tlb-lx" aria-label="close" style="width:38px;height:38px;border:0;border-radius:50%;background:#f1f1f4;font-size:18px;cursor:pointer;color:#1c1c21">\u2715</button></div>' +
        '<div style="position:relative;flex:1;min-height:200px"><div id="tlb-map" style="position:absolute;top:0;left:0;right:0;bottom:0"></div>' +
        '<div style="position:absolute;left:50%;top:50%;width:0;height:0;z-index:1000;pointer-events:none"><div id="tlb-pin" style="position:absolute;left:-17px;top:-44px;width:34px;height:44px;transition:transform .15s ease;filter:drop-shadow(0 3px 3px rgba(0,0,0,.25))">' + PIN + '</div><div style="position:absolute;left:-6px;top:-3px;width:12px;height:5px;border-radius:50%;background:rgba(0,0,0,.25)"></div></div>' +
        '<button id="tlb-me" aria-label="my location" style="position:absolute;right:14px;bottom:14px;z-index:1000;width:48px;height:48px;border:0;border-radius:50%;background:#fff;box-shadow:0 2px 10px rgba(0,0,0,.25);cursor:pointer;display:flex;align-items:center;justify-content:center">' + ME_ICON + '</button></div>' +
        '<div style="padding:12px 14px calc(16px + env(safe-area-inset-bottom,0px))"><div data-i18n="locHint" style="font-size:13px;color:#4b5563;margin-bottom:4px"></div><div id="tlb-co" style="font-size:12px;color:#8b8f98;min-height:16px"></div><div id="tlb-lm" role="alert" style="font-size:12px;font-weight:600;color:#d92d20;min-height:16px;margin-bottom:6px"></div><button id="tlb-ls" data-i18n="locSend" ' + BT + '></button></div>';
      document.body.appendChild(ov); applyI18n();
      var st = (start && isFinite(+start[0]) && isFinite(+start[1]) && start[0] !== null && start[1] !== null) ? [+start[0], +start[1]] : null;
      var map = L.map('tlb-map', { zoomControl: false }).setView(st || [38.5598, 68.787], st ? 17 : 14);
      L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '\u00a9 OpenStreetMap', referrerPolicy: 'strict-origin-when-cross-origin' }).addTo(map);
      var show = function () { if (!alive || !ov.isConnected) return; var c = map.getCenter(); $('tlb-co').textContent = c.lat.toFixed(6) + ', ' + c.lng.toFixed(6); };
      map.on('movestart', function () { var p = $('tlb-pin'); if (p) p.style.transform = 'translateY(-10px)'; });
      map.on('move', show);
      map.on('moveend', function () { var p = $('tlb-pin'); if (p) p.style.transform = ''; show(); });
      setTimeout(function () { if (alive) { map.invalidateSize(); show(); } }, 150);
      var locating = false, geoTimer = 0, geoSeq = 0;
      function locate() {
        if (locating || !alive) return;
        var note = ov.querySelector('#tlb-lm'), button = ov.querySelector('#tlb-me');
        if (!navigator.geolocation) { note.textContent = t('locNA'); return; }
        if (window.isSecureContext === false) { note.textContent = t('locSecure'); return; }
        locating = true; button.disabled = true; button.setAttribute('aria-busy', 'true'); note.textContent = t('locWaiting');
        var seq = ++geoSeq;
        function finish(key, p) {
          if (!alive || seq !== geoSeq) return;
          ++geoSeq; clearTimeout(geoTimer); locating = false; button.disabled = false; button.removeAttribute('aria-busy');
          note.textContent = t(key);
          if (p) { map.setView([p.coords.latitude, p.coords.longitude], 17); show(); }
        }
        geoTimer = setTimeout(function () { finish('locTimeout'); }, 13000);
        try { navigator.geolocation.getCurrentPosition(function (p) {
          var c = p && p.coords;
          if (!c || !Number.isFinite(c.latitude) || !Number.isFinite(c.longitude) || Math.abs(c.latitude) > 90 || Math.abs(c.longitude) > 180) return finish('locFail');
          finish('locFound', p);
        }, function (e) { finish(e && e.code === 1 ? 'locDenied' : e && e.code === 3 ? 'locTimeout' : 'locFail'); }, { enableHighAccuracy: true, timeout: 12000, maximumAge: 5000 }); }
        catch (e) { finish('locFail'); }
      }
      if (!st) locate();
      $('tlb-me').onclick = locate;
      function close() { alive = false; ++geoSeq; clearTimeout(geoTimer); map.remove(); ov.remove(); }
      $('tlb-lx').onclick = function () { close(); state('cancelled'); };
      $('tlb-ls').onclick = function () { var c = map.getCenter(); close(); cb(c.lat, c.lng); };
    }, loadFail);
  }

  Object.assign(I.ru, {locMapFail:'Карта выбора места не загрузилась. Проверьте соединение и попробуйте снова.',locWaiting:'Определяем местоположение…',locFound:'Местоположение определено. Проверьте точку перед отправкой.',locTimeout:'Время ожидания геопозиции истекло. Повторите или выберите точку на карте.',locSecure:'Для геопозиции откройте страницу через HTTPS.'});
  /* Chooser for a point from the chat. The driver app has its own (route-layer, same server links); elsewhere a small sheet
     with the same server links (Edge Function «route», op links). If the links cannot be loaded, the coordinates can be
     copied — no provider is forced. */
  function openPoint(lat, lng) {
    lat = +lat; lng = +lng;
    if (!isFinite(lat) || !isFinite(lng) || Math.abs(lat) > 90 || Math.abs(lng) > 180) return false;
    if (typeof window.aNavigationOpenPoint === 'function' && window.aNavigationOpenPoint(lat, lng)) return false;
    var old = document.getElementById('tlb-pt'); if (old) old.remove();
    var ov = document.createElement('div'); ov.id = 'tlb-pt';
    ov.style.cssText = 'position:fixed;inset:0;z-index:10000;background:rgba(23,36,60,.45);display:flex;align-items:flex-end;justify-content:center';
    var ll = lat.toFixed(6) + ', ' + lng.toFixed(6);
    var box = '<div role="dialog" aria-modal="true" aria-label="' + esc(t('ptTitle')) + '" style="background:#fff;width:min(430px,100%);border-radius:20px 20px 0 0;padding:16px 16px calc(16px + env(safe-area-inset-bottom,0px));font-family:-apple-system,BlinkMacSystemFont,sans-serif;max-height:85dvh;overflow:auto">' +
      '<div style="display:flex;justify-content:space-between;align-items:center;gap:8px"><b style="font-size:18px">' + esc(t('ptTitle')) + '</b><button id="tlb-pt-x" aria-label="' + esc(t('closeB') || 'Закрыть') + '" style="width:44px;height:44px;border:0;border-radius:12px;background:#f1f1f4;font-size:20px">×</button></div>' +
      '<p style="margin:6px 0 12px;color:#536176;font-size:13px">' + esc(ll) + '</p><div id="tlb-pt-l" role="status">' + esc(t('ptLoading')) + '</div>' +
      '<button id="tlb-pt-c" style="margin-top:12px;width:100%;min-height:44px;border:1px solid #E0E5EC;border-radius:12px;background:#fff">' + esc(t('ptCopy')) + '</button></div>';
    ov.innerHTML = box; document.body.appendChild(ov);
    var close = function () { ov.remove(); };
    ov.addEventListener('click', function (e) { if (e.target === ov) close(); });
    ov.querySelector('#tlb-pt-x').onclick = close;
    ov.querySelector('#tlb-pt-c').onclick = function () { var b = this; try { navigator.clipboard.writeText(ll).then(function () { b.textContent = t('ptCopied'); }, function () { b.textContent = ll; }); } catch (e) { b.textContent = ll; } };
    var ok = function (u) { return typeof u === 'string' && /^(https:\/\/(www\.google\.com\/maps\/dir\/|yandex\.ru\/maps\/|2gis\.ru\/directions\/)|yandexmaps:\/\/maps\.yandex\.(com|ru)\/)/.test(u); };
    window.TLB.navigation({ op: 'links', to: [lat, lng] }).then(function (r) {
      var el = ov.querySelector('#tlb-pt-l'); if (!el) return;
      var list = (r && Array.isArray(r.links) ? r.links : []).filter(function (v) { return ok(v.app) && ok(v.web); });
      if (!list.length) { el.textContent = t('ptNoLinks'); el.setAttribute('role', 'alert'); return; }
      el.innerHTML = list.map(function (v) { return '<div style="display:flex;align-items:center;justify-content:space-between;gap:8px;padding:8px 0;border-top:1px solid #f0f2f5"><b>' + esc(v.name) + '</b><span style="display:flex;gap:6px"><a href="' + esc(v.app) + '" target="_blank" rel="noopener noreferrer" style="min-height:44px;display:inline-flex;align-items:center;padding:0 14px;border-radius:12px;background:#f1511b;color:#fff;text-decoration:none">' + esc(t('ptOpen')) + '</a><a href="' + esc(v.web) + '" target="_blank" rel="noopener noreferrer" style="min-height:44px;display:inline-flex;align-items:center;padding:0 8px;color:#536176">' + esc(t('ptWeb')) + '</a></span></div>'; }).join('');
    }, function () { var el = ov.querySelector('#tlb-pt-l'); if (el) el.textContent = t('ptNoLinks'); });
    return false;
  }
  var qrLoad = null;
  function loadQr() {
    if (window.qrcode) return Promise.resolve(window.qrcode);
    if (qrLoad) return qrLoad;
    qrLoad = new Promise(function (ok, bad) {
      var s = document.createElement('script'); s.src = 'https://cdn.jsdelivr.net/npm/qrcode-generator@1.4.4/qrcode.js';
      s.integrity = 'sha384-8FWZA6BGMXhsfO+BLtrJK0We6gg5o1JyO8xQm6peWDEUs17ACA5ziE/NIAkl9z2k'; s.crossOrigin = 'anonymous';
      s.onload = function () { window.qrcode ? ok(window.qrcode) : bad(new Error('qr_unavailable')); };
      s.onerror = function () { qrLoad = null; bad(new Error('qr_unavailable')); }; document.head.appendChild(s);
    });
    return qrLoad;
  }
  Object.assign(I.ru, {err_store_location_missing:'Доставка из этого заведения временно недоступна: не указана его точка на карте.'});
  Object.assign(I.en, {err_store_location_missing:'Delivery from this place is unavailable for now: its map point is not set.'});
  Object.assign(I.ru, {ptTitle:'Открыть точку на карте',ptLoading:'Загружаем карты…',ptNoLinks:'Ссылки на карты недоступны. Скопируйте координаты.',ptCopy:'Скопировать координаты',ptCopied:'Скопировано',ptOpen:'Открыть',ptWeb:'Сайт'});
  Object.assign(I.en, {ptTitle:'Open the point on a map',ptLoading:'Loading maps…',ptNoLinks:'Map links unavailable. Copy the coordinates.',ptCopy:'Copy coordinates',ptCopied:'Copied',ptOpen:'Open',ptWeb:'Website'});
  Object.assign(I.ru, {payWalletPart:'Из кошелька',payRestCash:'Наличными курьеру',payRestOther:'Остаток',payMixed:'Оплата частями'});
  Object.assign(I.en, {payWalletPart:'From the wallet',payRestCash:'Cash to the courier',payRestOther:'Remainder',payMixed:'Split payment'});
  Object.assign(I.ru, {jrPending:'Ждёт подтверждения',jrPreparing:'Готовится',jrReady:'Готов',jrHanded:'Передан курьеру',jrEnded:'Заказ завершён',jcSearching:'Ищем курьера',jcAssigned:'Назначен',jcOnWay:'Везёт заказ',jcDelivered:'Доставил',jcAssignedEarlier:'Назначен ранее',jcNoUpdate:'Нет обновления',ordersStale:'Не удалось обновить заказ — показаны последние данные',statusAtL:'Статус заказа',courierAtL:'Геопозиция курьера',timeUnknown:'время неизвестно'});
  Object.assign(I.en, {jrPending:'Awaiting confirmation',jrPreparing:'Preparing',jrReady:'Ready',jrHanded:'Handed to the courier',jrEnded:'Order closed',jcSearching:'Looking for a courier',jcAssigned:'Assigned',jcOnWay:'On the way',jcDelivered:'Delivered',jcAssignedEarlier:'Assigned earlier',jcNoUpdate:'No update',ordersStale:'Could not update the order — showing the last data',statusAtL:'Order status',courierAtL:'Courier location',timeUnknown:'time unknown'});
  Object.assign(I.en, {locMapFail:'The location picker could not load. Check your connection and try again.',locWaiting:'Finding your location…',locFound:'Location found. Check the pin before sending.',locTimeout:'Location request timed out. Retry or choose a point on the map.',locSecure:'Open the page over HTTPS to use location.'});
  /* ---------- Supabase runtime ---------- */
  var sb = null, ME = null, need = '', onReady = null, sig = '', ORD = [], firstLoad = true;
  var pagesSt = 'loading', pagesErr = '';
  var DB = { stores: [], items: [], orders: [], oitems: [], xorders: [], xitems: [], chat: [], drivers: [], banners: [], favs: [], events: [], cash: {}, promos: [], myOffers: [], offersAll: [], ratings: [], groups: [], options: [], addresses: [], contacts: {}, settings: {}, myRating: null, tickets: [], tmsgs: {}, texts: {}, sreqs: [], people: {}, wallet: { balance: 0, entries: [] }, pages: {}, hh: [], loyalty: null, pts: [], recipients: {}, best: [], speed: {} };
  var seenChat = {}, lastStatus = {}, unread = {};
  var secOk = {}, secFailAt = {}, evSt = {};   // C-1 orders health · C-2 status-event loads (27 Oct)
  var walletStale = true, wantTix = false, tixHold = false, sigs = {}, secRun = {}, secT0 = {}, secFail = {}, extraLoaded = {}, ptsSeq = 0, extraOrders = {}, kicks = {}, offlineNow = false, lastProbe = 0, lastTick = 0, fireT = null, errSent = 0;
  /* happy-hour windows running at a moment (Dushanbe = UTC+5, no daylight saving) — same rule as happy_hour_pct() in SQL */
  function hhOnNow(at) {
    var d = new Date((at || Date.now()) + 5 * 3600000), dow = d.getUTCDay() || 7, prev = dow === 1 ? 7 : dow - 1, mins = d.getUTCHours() * 60 + d.getUTCMinutes() + d.getUTCSeconds() / 60;
    var tm = function (s) { var p = String(s || '0:0').split(':'); return (+p[0] || 0) * 60 + (+p[1] || 0) + (+p[2] || 0) / 60; };
    return (DB.hh || []).filter(function (h) {
      if (!h.active) return false;
      var a = tm(h.start_time), b = tm(h.end_time), days = (h.days || []).map(Number);
      return a < b ? (days.indexOf(dow) >= 0 && mins >= a && mins < b) : ((days.indexOf(dow) >= 0 && mins >= a) || (days.indexOf(prev) >= 0 && mins < b));
    });
  }
  function grp(r) { if (r.error) return { error: errKey(r.error) }; if (!r.data) return { error: 'bad_group' }; return { group: r.data }; }
  function storeName(id) { var s = DB.stores.find(function (x) { return x.id === id; }); return s ? s.name : '?'; }
  function storePhone(id) { var s = DB.stores.find(function (x) { return x.id === id; }); return s ? (s.phone || '') : ''; }
  var ALL_PERMS = ['orders', 'support', 'finance', 'stores', 'content'], MYPERMS = [];
  var VERSION = 'v56';
  function groupsOf(id) { return DB.groups.filter(function (g) { return g.item_id === id; }); }
  function availOpts(g) { return DB.options.filter(function (o) { return o.group_id === g.id && o.available; }); }
  function shapeItem(i) { return { id: i.id, name: i.name, price: +i.price, image: i.image_url || '', available: i.available, popular: i.popular, approved: i.approved, section: i.section || '', discount: +i.discount_pct || 0, hasOpts: groupsOf(i.id).some(function (g) { return availOpts(g).length > 0; }), optsBlocked: groupsOf(i.id).some(function (g) { return g.required && availOpts(g).length === 0; }), store: storeName(i.store_id) }; }
  function shape() {
    // orders found by the admin search outside the newest loaded ones are shaped too (flag _x) but not listed by TLB.orders()
    var have = {}; DB.orders.forEach(function (o) { have[o.id] = 1; });
    var extra = DB.xorders.filter(function (o) { return !have[o.id]; }), xi = {}; extra.forEach(function (o) { xi[o.id] = 1; });
    var allItems = DB.oitems.concat(DB.xitems.filter(function (i) { return xi[i.order_id]; }));
    return DB.orders.concat(extra).map(function (o) {
      return { id: o.id, store: storeName(o.store_id), storeId: o.store_id, storePhone: storePhone(o.store_id), status: o.status,
        _x: !!xi[o.id], items: allItems.filter(function (i) { return i.order_id === o.id; }).map(function (i) { return { id: i.item_id, name: i.name, price: +i.price, qty: i.qty, note: i.note || '', opts: Array.isArray(i.options) ? i.options.map(function (x) { return { id: x.id, g: String(x.g || ''), n: String(x.n || ''), p: +x.p || 0 }; }) : [] }; }),
        subtotal: +o.subtotal, discount: +o.discount, promoDiscount: +o.promo_discount || 0, promoCode: o.promo_code || '', delivery: +o.delivery_fee, tip: +o.tip, total: +o.total, commission: +o.commission || 0, commissionSet: o.commission != null && o.commission !== '', commissionPct: +o.commission_pct,
        payment: o.payment || '', address: o.address, deliveryBase: o.delivery_base == null ? null : +o.delivery_base, deliveryExtra: +o.delivery_extra || 0, deliveryKm: o.delivery_km == null ? null : +o.delivery_km, walletUsed: +o.wallet_used || 0, walletReturnedAt: o.wallet_returned_at ? Date.parse(o.wallet_returned_at) : null, pointsReturnedAt: o.points_returned_at ? Date.parse(o.points_returned_at) : null, arrivedStoreAt: o.arrived_store_at ? Date.parse(o.arrived_store_at) : null, arrivedCustAt: o.arrived_cust_at ? Date.parse(o.arrived_cust_at) : null, deliveryPhoto: o.delivery_photo || null, cancelReason: o.cancel_reason || null, cancelNote: o.cancel_note || '', cancelledBy: o.cancelled_by || null, hhDiscount: +o.hh_discount || 0, leaveAtDoor: !!o.leave_at_door, scheduledFor: o.scheduled_for ? Date.parse(o.scheduled_for) : null, feeWaived: +o.fee_waived || 0, groupId: o.group_id || null, substitution: o.substitution || 'call', isGift: !!o.is_gift, recipient: DB.recipients[o.id] || null, hhPct: +o.hh_pct || 0, pointsUsed: +o.points_used || 0, pointsValue: +o.points_value || 0, pointsEarned: +o.points_earned || 0, cashback: +o.cashback || 0, lat: o.lat == null ? null : +o.lat, lng: o.lng == null ? null : +o.lng, prepTime: o.prep_time, driver: o.driver_id, driverName: o.driver_name || '', payout: +o.driver_payout,
        cashCollected: o.cash_collected == null ? null : +o.cash_collected, cashNote: o.cash_note || '', cashSettled: !!o.cash_settled_at,
        client: { name: o.customer_name || '', phone: ((DB.contacts[o.id] || {}).customer_phone) || '' }, driverPhone: ((DB.contacts[o.id] || {}).driver_phone) || '', customerId: o.customer_id,
        chat: DB.chat.filter(function (c) { return c.order_id === o.id; }).map(function (c) { return { s: c.sender_id === o.customer_id ? 'client' : 'driver', t: c.body, at: Date.parse(c.created_at) }; }),
        createdAt: Date.parse(o.created_at), doneAt: o.done_at ? Date.parse(o.done_at) : null };
    });
  }
  /* sound + toast for new chat messages and (customers) status changes */
  function notify() {
    var fresh = false;
    DB.chat.forEach(function (c) { if (!seenChat[c.id]) { seenChat[c.id] = 1; if (!firstLoad && c.sender_id !== ME.id) { unread[c.order_id] = (unread[c.order_id] || 0) + 1; fresh = true; } } });
    ORD.forEach(function (o) { var p = lastStatus[o.id]; if (!firstLoad && p && p !== o.status && ME.role === 'customer') { toast(t(o.status)); fresh = true; } lastStatus[o.id] = o.status; });
    if (fresh) beep();
    firstLoad = false;
  }
  function reportError(msg, ctx) {
    try {
      if (!sb || !ME || errSent >= 5) return; errSent++;
      sb.rpc('report_client_error', { p_app: need, p_message: String(msg || '').slice(0, 300), p_context: String(ctx || '').slice(0, 300), p_ua: String((navigator && navigator.userAgent) || '').slice(0, 160) }).then(function () { }, function () { });
    } catch (e) { }
  }
  window.addEventListener('error', function (e) { reportError(e.message, String(e.filename || '').split('/').pop() + ':' + e.lineno); });
  window.addEventListener('unhandledrejection', function (e) { reportError('Promise: ' + String((e.reason && e.reason.message) || e.reason), ''); });
  /* ===================== data layer =====================
     Four small sections instead of one giant reload every 4 seconds:
       stat   = stores, menu, options, banners      (slow: every 60 s)
       orders = my orders + their items/chat         (realtime + 10-25 s)
       misc   = favorites, ratings, addresses, ...   (every 10-60 s)
       offers = courier offers (couriers only)       (realtime + 4 s)
     Nothing runs while the tab is hidden; failures back off (x2, up to x8); realtime events only reload the section they touch. */
  var STORE_COLS = 'id,name,category,description,logo_url,cover_url,address,lat,lng,fee_type,fee_base,fee_per_km,fee_free_km,discount_pct,is_open,is_active,is_featured,created_at,phone,free_first_delivery,google_place_id,rating,rating_count,rating_updated_at,app_rating,app_rating_count,brand_id,branch_name';
  var STORE_COLS_V35 = STORE_COLS.replace(',brand_id,branch_name', '');
  var STORE_COLS_BASE = 'id,name,category,description,logo_url,cover_url,address,lat,lng,fee_type,fee_base,fee_per_km,fee_free_km,discount_pct,is_open,is_active,is_featured,created_at,phone,free_first_delivery,google_place_id,rating,rating_count,rating_updated_at';
  var dbOld = false;
  function storesQuery(cols) { return sb.from('stores').select(cols).order('created_at').limit(1000); }
  function banner(id, text, bg, bottom) {
    var b = $(id);
    if (!b) {
      b = document.createElement('div'); b.id = id;
      b.style.cssText = 'position:fixed;left:10px;right:10px;z-index:10001;border-radius:14px;padding:11px 14px;font:600 13px/1.4 -apple-system,BlinkMacSystemFont,sans-serif;text-align:center;box-shadow:0 8px 22px rgba(0,0,0,.25);cursor:pointer;color:#fff';
      b.onclick = function () { location.reload(); };
      document.body.appendChild(b);
    }
    b.style.background = bg; b.style.bottom = 'calc(' + (bottom || 86) + 'px + env(safe-area-inset-bottom,0px))'; b.textContent = text;
  }
  function unbanner(id) { var b = $(id); if (b) b.remove(); }
  var LIMITS = { customer: 60, driver: 60, merchant: 200, admin: 300 };
  var EVERY = {
    customer: { orders: 25000, stat: 60000, misc: 40000 },
    merchant: { orders: 10000, stat: 60000, misc: 60000 },
    driver: { orders: 10000, offers: 4000, stat: 90000, misc: 60000 },
    admin: { orders: 10000, misc: 10000, stat: 60000 }
  };
  var ACTIVE = ['pending', 'preparing', 'ready', 'pickedup'];
  function changed(name, data) { var k = JSON.stringify(data); if (sigs[name] === k) return false; sigs[name] = k; return true; }
  function fireSoon() {
    if (typeof requestAnimationFrame === 'undefined') return fire();
    if (fireT) return; fireT = setTimeout(function () { fireT = null; fire(); }, 120);
  }
  function loadStat() {
    return Promise.all([
      storesQuery(STORE_COLS).then(function (res) {
        if (res.error && (res.error.code === '42703' || res.error.code === '42501' || /does not exist|permission denied/i.test(String(res.error.message || '')))) {
          return storesQuery(STORE_COLS_V35).then(function (r2) {
            if (r2.error && (r2.error.code === '42703' || r2.error.code === '42501' || /does not exist|permission denied/i.test(String(r2.error.message || '')))) { dbOld = true; return storesQuery(STORE_COLS_BASE); }
            return r2;
          });
        }
        return res;
      }),
      sb.from('menu_items').select('*').order('created_at').limit(5000),
      sb.from('banners').select('*').order('sort').order('created_at').limit(100),
      sb.from('item_option_groups').select('*').order('sort').order('created_at').limit(5000),
      sb.from('item_options').select('*').order('sort').order('name').limit(20000),
      (ME.role === 'admin' || ME.role === 'merchant') ? sb.rpc('store_private') : Promise.resolve({ data: [] }),
      sb.from('brands').select('id,name,owner_id').order('name').limit(500).then(function (x) { return x; }, function () { return { data: [] }; }),
      // restaurant rules added by later patches (32: points minimum + cashback, 33: free delivery from); an older database just lacks them
      sb.from('stores').select('id,points_min_order,cashback_pct,free_delivery_min,earn_per_tjs').limit(1000).then(function (x) {
        if (!x.error) return x;
        return sb.from('stores').select('id,points_min_order,cashback_pct').limit(1000).then(function (y) { return y.error ? { data: [] } : y; }, function () { return { data: [] }; });
      }, function () { return { data: [] }; })
    ]).then(function (r) {
      if (r[0].error || r[1].error) throw (r[0].error || r[1].error);
      if (dbOld && (ME.role === 'admin' || ME.role === 'merchant')) banner('tlb-old', t('dbOldW'), '#c2410c', 150);
      var priv = {}; (r[5].error ? [] : (r[5].data || [])).forEach(function (p) { priv[p.id] = p; });
      var rules = {}; ((r[7] && r[7].data) || []).forEach(function (x) { rules[x.id] = x; });
      var stores = (r[0].data || []).map(function (x) { var p = priv[x.id], q = rules[x.id]; if (q) x = Object.assign({}, x, { points_min_order: q.points_min_order, cashback_pct: q.cashback_pct, free_delivery_min: q.free_delivery_min == null ? 0 : q.free_delivery_min, earn_per_tjs: q.earn_per_tjs == null ? null : q.earn_per_tjs }); return p ? Object.assign({}, x, { owner_id: p.owner_id, commission_pct: p.commission_pct, max_discount_pct: p.max_discount_pct }) : x; });
      var pack = [stores, r[1].data, r[2].error ? [] : r[2].data, r[3].error ? [] : r[3].data, r[4].error ? [] : r[4].data, r[6] && !r[6].error ? (r[6].data || []) : []];
      if (!changed('stat', pack)) return false;
      DB.stores = pack[0] || []; DB.items = pack[1] || []; DB.banners = pack[2] || []; DB.groups = pack[3] || []; DB.options = pack[4] || []; DB.brands = pack[5] || [];
      return true;
    });
  }
  function ordersQuery() {
    var q = sb.from('orders').select('*').order('created_at', { ascending: false }).limit(LIMITS[ME.role] || 60);
    if (ME.role === 'customer') q = q.eq('customer_id', ME.id);
    else if (ME.role === 'driver') q = q.eq('driver_id', ME.id);
    else if (ME.role === 'merchant') {
      var ids = DB.stores.filter(function (x) { return x.owner_id === ME.id; }).map(function (x) { return x.id; });
      if (!ids.length) return null;
      q = q.in('store_id', ids);
    }
    return q;
  }
  function loadOrders() {
    var q = ordersQuery();
    var offerIds = ME.role === 'driver' ? DB.myOffers.map(function (f) { return f.order_id; }) : [];
    var qs = [q ? q : Promise.resolve({ data: [] }), offerIds.length ? sb.from('orders').select('*').in('id', offerIds) : Promise.resolve({ data: [] })];
    return Promise.all(qs).then(function (r) {
      if (r[0].error) throw r[0].error;
      var seen = {}, rows = [];
      (r[0].data || []).concat(r[1].error ? [] : (r[1].data || [])).forEach(function (o) { if (!seen[o.id]) { seen[o.id] = 1; rows.push(o); } });
      rows.sort(function (x, y) { return Date.parse(y.created_at) - Date.parse(x.created_at); });
      var ids = rows.map(function (o) { return o.id; });
      var live = rows.filter(function (o) { return ACTIVE.indexOf(o.status) >= 0 || extraOrders[o.id]; }).map(function (o) { return o.id; });
      return Promise.all([
        ids.length ? sb.from('order_items').select('*').in('order_id', ids) : Promise.resolve({ data: [] }),
        live.length ? sb.from('order_chat').select('*').in('order_id', live).order('created_at') : Promise.resolve({ data: [] }),
        (ME.role === 'driver' || ME.role === 'admin') ? sb.rpc('cash_balances') : Promise.resolve({ data: [] }),
        ME.role === 'admin' ? Promise.resolve({ data: null }) : sb.rpc('active_contacts'),
        // gift recipients (patch 32): readable only by the customer, the courier of the order and staff
        (ME.role !== 'merchant' && live.length) ? sb.from('order_recipient').select('*').in('order_id', live) : Promise.resolve({ data: [] })
      ]).then(function (x) {
        if (x[0].error) throw x[0].error;
        var cash = {}; if (!x[2].error) (x[2].data || []).forEach(function (c) { cash[c.driver_id] = +c.balance; });
        // chat of orders opened on demand (admin detail) that are no longer "live" stays in memory
        var keepChat = DB.chat.filter(function (c) { return live.indexOf(c.order_id) < 0 && extraOrders[c.order_id]; });
        var chat = (x[1].error ? [] : (x[1].data || [])).concat(keepChat);
        var contacts = {}; if (x[3] && !x[3].error) (x[3].data || []).forEach(function (c) { contacts[c.order_id] = { customer_phone: c.customer_phone || '', driver_phone: c.driver_phone || '' }; });
        if (ME.role === 'admin') contacts = DB.contacts;                       // the admin loads phones on demand (opened order, low ratings)
        var rcp = {}; if (x[4] && !x[4].error) (x[4].data || []).forEach(function (g) { rcp[g.order_id] = { name: g.name, phone: g.phone }; });
        if (!changed('orders', [rows, x[0].data, chat, cash, contacts, rcp])) return false;
        DB.recipients = rcp;
        DB.orders = rows; DB.oitems = x[0].data || []; DB.chat = chat; DB.cash = cash; DB.contacts = contacts;
        return true;
      });
    });
  }
  function loadMisc() {
    var admin = ME.role === 'admin', cust = ME.role === 'customer';
    return Promise.all([
      sb.from('profiles').select('*').eq('id', ME.id).single(),
      sb.from('favorites').select('store_id').limit(300),
      (admin || cust) ? sb.from('ratings').select('*').order('created_at', { ascending: false }).limit(300) : Promise.resolve({ data: [] }),
      cust ? sb.from('addresses').select('*').order('created_at').limit(20) : Promise.resolve({ data: [] }),
      admin ? sb.from('promo_codes').select('*').order('created_at', { ascending: false }).limit(200) : Promise.resolve({ data: [] }),
      admin ? sb.from('profiles').select('*').eq('role', 'driver').limit(1000) : Promise.resolve({ data: [] }),
      admin ? sb.from('order_offers').select('*').order('offered_at', { ascending: false }).limit(300) : Promise.resolve({ data: [] }),
      (admin || cust) ? sb.from('app_settings').select('*') : Promise.resolve({ data: [] }),
      ME.role === 'driver' ? sb.rpc('my_rating') : Promise.resolve({ data: null }),
      // a customer's tickets and the support phone are fetched only when he has a ticket or opened the support screen (keeps an idle customer cheap)
      (admin || (cust && (DB.tickets.length || wantTix))) ? sb.from('support_tickets').select('*').order('updated_at', { ascending: false }).limit(admin ? 200 : 30) : Promise.resolve({ data: cust ? DB.tickets : [] }),
      (admin || (cust && (DB.tickets.length || wantTix))) ? sb.from('app_texts').select('*') : Promise.resolve({ data: Object.keys(DB.texts).map(function (k) { return { key: k, value: DB.texts[k] }; }) }),
      (admin || ME.role === 'merchant' || MYPERMS.indexOf('stores') >= 0) ? sb.from('store_requests').select('*').order('created_at', { ascending: false }).limit(ME.role === 'merchant' ? 20 : 100) : Promise.resolve({ data: [] }),
      // the balance is fetched once, then only after a wallet event (realtime), coming back to the app, or an order that used it: an idle customer costs nothing
      cust ? (walletStale ? sb.rpc('wallet_balance') : Promise.resolve({ data: DB.wallet.balance })) : Promise.resolve({ data: null }),
      // happy hours change prices, every app shows them; the customer also gets his points (patch 29; empty before it is run)
      sb.from('happy_hours').select('*').order('start_time').limit(100),
      cust ? sb.rpc('loyalty_summary') : Promise.resolve({ data: null }),
      cust ? sb.rpc('best_dishes', { p_store: null, p_limit: 30 }) : Promise.resolve({ data: [] }),
      cust ? sb.rpc('store_speed') : Promise.resolve({ data: [] })
    ]).then(function (r) {
      if (r[0].error && r[1].error) throw r[0].error;
      var pack = [r[0].data, r[1].error ? [] : r[1].data, r[2].error ? [] : r[2].data, r[3].error ? [] : r[3].data, r[4].error ? [] : r[4].data, r[5].error ? [] : r[5].data, r[6].error ? [] : r[6].data, r[7].error ? [] : r[7].data, r[8].error ? null : r[8].data, r[9].error ? [] : r[9].data, r[10].error ? [] : r[10].data, r[11].error ? [] : r[11].data, r[12].error ? null : r[12].data, r[13].error ? [] : r[13].data, r[14].error ? null : r[14].data, r[15].error ? [] : r[15].data, r[16].error ? [] : r[16].data];
      if (!changed('misc', pack)) return false;
      if (pack[0]) ME = Object.assign(ME, pack[0]);
      DB.favs = (pack[1] || []).map(function (x) { return x.store_id; });
      DB.ratings = pack[2] || []; DB.addresses = pack[3] || []; DB.promos = pack[4] || []; DB.drivers = pack[5] || []; DB.offersAll = pack[6] || [];
      var st = {}; (pack[7] || []).forEach(function (x) { st[x.key] = +x.value; }); DB.settings = st;
      DB.myRating = pack[8] && pack[8].count != null ? { avg: pack[8].avg == null ? null : +pack[8].avg, count: +pack[8].count || 0 } : null;
      DB.tickets = pack[9] || []; DB.sreqs = pack[11] || []; DB.hh = pack[13] || []; DB.loyalty = pack[14] || null; DB.best = pack[15] || []; var sp = {}; (pack[16] || []).forEach(function (x) { sp[x.store_id] = { min: +x.avg_min, n: +x.n }; }); DB.speed = sp;
      if (ME.role === 'customer') { DB.wallet.balance = pack[12] == null ? 0 : Math.round(+pack[12] * 100) / 100; if (!r[12].error) walletStale = false; }
      if (ME.role === 'customer' && !DB.tickets.length && !tixHold) wantTix = false;   // nothing to follow: stop fetching until he opens support
      var tx = {}; (pack[10] || []).forEach(function (x) { tx[x.key] = x.value || ''; }); DB.texts = tx;
      return true;
    }).then(function (ch) {
      if (ME.role !== 'admin') return ch;
      var need = {}; DB.tickets.forEach(function (t) { if (t.customer_id && !DB.people[t.customer_id]) need[t.customer_id] = 1; }); DB.sreqs.forEach(function (q) { if (q.user_id && !DB.people[q.user_id]) need[q.user_id] = 1; });
      var pids = Object.keys(need).slice(0, 100);
      if (pids.length) return sb.from('profiles').select('id,name,phone').in('id', pids).then(function (pr) { if (pr.error) return ch; (pr.data || []).forEach(function (p) { DB.people[p.id] = { name: p.name || '', phone: p.phone || '' }; });
        // a profile that is not readable (deleted, hidden) is remembered as unknown: otherwise it was asked again and the screen redrawn every 10 s
        pids.forEach(function (id) { if (!DB.people[id]) DB.people[id] = { name: '', phone: '' }; }); return !!(pr.data || []).length; }, function () { return ch; }).then(function (more) { return afterAdminMisc(ch || more); });
      return afterAdminMisc(ch);
    });
  }
  function afterAdminMisc(ch0) {
    return Promise.resolve(ch0).then(function (ch) {
      var ids = DB.ratings.filter(function (r) { return !r.handled_at && ((r.store_stars != null && r.store_stars <= 2) || (r.driver_stars != null && r.driver_stars <= 2)); }).map(function (r) { return r.order_id; });
      return fetchAdminContacts(ids).then(function (more) { return ch || more; });
    });
  }
  /* The admin may see every phone; they are loaded only for the orders that need them (opened order, low ratings). */
  function fetchAdminContacts(ids) {
    ids = ids.filter(function (id) { return !DB.contacts[id]; }).slice(0, 100);
    if (!ids.length) return Promise.resolve(false);
    return sb.rpc('contacts_for', { p_ids: ids }).then(function (r) {
      if (r.error) return false;
      (r.data || []).forEach(function (c) { DB.contacts[c.order_id] = { customer_phone: c.customer_phone || '', driver_phone: c.driver_phone || '' }; });
      return true;
    }, function () { return false; });
  }
  function loadOffers() {
    return sb.rpc('my_offers').then(function (r) {
      if (r.error) throw r.error;
      var gotAt = Date.now(), list = (r.data || []).map(function (x) { return { order_id: x.order_id, mode: x.mode, rank: x.rank, dist: x.dist_km == null ? null : +x.dist_km, secs: +x.secs_left || 0, got: gotAt }; });
      var key = list.map(function (o) { return o.order_id + ':' + o.mode + ':' + o.rank; }).join(',');
      var same = sigs.offers === key; sigs.offers = key;
      DB.myOffers = list;                      // seconds-left always refreshed (the countdown reads them)
      if (list.some(function (o) { return !DB.orders.some(function (x) { return x.id === o.order_id; }); })) kick('orders');
      return !same || list.length > 0;
    });
  }
  var LOADERS = { stat: loadStat, orders: loadOrders, misc: loadMisc, offers: loadOffers };
  function runSection(name) {
    if (secRun[name]) return secRun[name];
    secT0[name] = Date.now();
    var go = function () { return LOADERS[name](); };
    // a restaurant needs to know its own stores before it can ask for its orders
    var p = (name === 'orders' && ME.role === 'merchant' && !DB.stores.length) ? loadStat().then(go) : go();
    secRun[name] = p.then(function (ch) { var was = secFail[name] > 0; secFail[name] = 0; secOk[name] = Date.now(); if (!secFail.stat && !secFail.orders) unbanner('tlb-err'); if (was && name === 'orders') fireSoon(); return !!ch; }, function (e) {
      secFail[name] = (secFail[name] || 0) + 1; secFailAt[name] = Date.now(); if (name === 'orders' && secFail[name] === 1) fireSoon(); console.error(name, e); lastErr = String((e && e.message) || e);
      if (/failed to fetch|networkerror|load failed|network request failed/i.test(lastErr)) checkNet();
      if ((name === 'stat' && !DB.stores.length) || ((name === 'stat' || name === 'orders') && secFail[name] >= 2)) banner('tlb-err', t('loadFail') + ' \u00b7 ' + lastErr.slice(0, 90), '#1c1c21', 86);
      return false;
    }).then(function (v) { secRun[name] = null; return v; });
    return secRun[name];
  }
  function refresh(which) {
    if (!ME || !sb) return Promise.resolve();
    var names = which ? [].concat(which) : ['stat', 'orders', 'misc'].concat(ME.role === 'driver' ? ['offers'] : []);
    return Promise.all(names.map(runSection)).then(function (res) {
      if (res.some(Boolean)) { ORD = shape(); notify(); fireSoon(); maybeTick(); }
    }).catch(function (e) { console.error(e); lastErr = String((e && e.message) || e); });
  }
  function kick(sec) {
    if (kicks[sec]) return;
    kicks[sec] = setTimeout(function () { kicks[sec] = null; refresh(sec); }, 250 + Math.floor(Math.random() * 400));
  }
  function subscribeRealtime() {
    var ch = sb.channel('tlb-' + ME.id);
    var on = function (table, sec) { ch.on('postgres_changes', { event: '*', schema: 'public', table: table }, function () { kick(sec); }); };
    on('orders', 'orders'); on('order_chat', 'orders'); on('happy_hours', 'misc');
    if (ME.role === 'customer') on('orders', 'misc');                     // a delivered / cancelled order changes the points
    if (ME.role === 'driver') on('order_offers', 'offers');
    if (ME.role === 'admin') { on('ratings', 'misc'); on('order_offers', 'misc'); on('support_tickets', 'misc'); on('ticket_messages', 'misc'); on('store_requests', 'misc'); }
    if (ME.role === 'customer') { on('support_tickets', 'misc'); ch.on('postgres_changes', { event: '*', schema: 'public', table: 'wallet_entries' }, function () { walletStale = true; kick('misc'); }); }
    if (ME.role === 'merchant' || (ME.role !== 'admin' && MYPERMS.indexOf('stores') >= 0)) { on('store_requests', 'misc'); }   /* staff with 'stores': restaurant / website requests */
    ch.subscribe();
  }
  /* The browser's "offline" event is unreliable (iOS fires it by mistake and sometimes never sends "online").
     So an event only triggers a REAL check against the server; while we believe we are offline we keep checking every 10 s. */
  function probeNet() {
    if (typeof fetch !== 'function') return Promise.resolve(true);
    var ctl = (typeof AbortController === 'function') ? new AbortController() : null, to = ctl ? setTimeout(function () { ctl.abort(); }, 6000) : null;
    return fetch(SB_URL + '/rest/v1/', { method: 'HEAD', headers: { apikey: SB_KEY }, cache: 'no-store', signal: ctl ? ctl.signal : undefined })
      .then(function () { if (to) clearTimeout(to); return true; }, function () { if (to) clearTimeout(to); return false; });
  }
  (function () { var st = document.createElement('style'); st.textContent = '.tlb-offon .top{top:var(--offh,40px)!important}'; (document.head || document.documentElement).appendChild(st); })();
  function setOffline(on) {
    var b = $('tlb-off');
    if (on) {
      offlineNow = true;
      if (!b) {
        b = document.createElement('div'); b.id = 'tlb-off'; b.setAttribute('data-i18n', 'offline'); b.setAttribute('role', 'alert');
        /* in normal flow (not fixed): it takes its own strip above the page and pushes the header down, never covers it */
        b.style.cssText = 'position:sticky;top:0;z-index:10002;background:#b42318;color:#fff;font:600 13px/1.35 -apple-system,sans-serif;text-align:center;padding:calc(8px + env(safe-area-inset-top,0px)) 12px 8px;word-break:break-word;box-sizing:border-box;width:100%';
        try { var bc = getComputedStyle(document.body); b.style.margin = '-' + (bc.paddingTop || '0px') + ' -' + (bc.paddingRight || '0px') + ' 0 -' + (bc.paddingLeft || '0px'); } catch (e) { }
        document.body.insertBefore(b, document.body.firstChild); document.documentElement.classList.add('tlb-offon'); document.documentElement.style.setProperty('--offh', b.offsetHeight + 'px'); applyI18n();
      }
    } else if (offlineNow || b) { offlineNow = false; if (b) b.remove(); document.documentElement.classList.remove('tlb-offon'); refresh(); }
  }
  function checkNet() { return probeNet().then(function (ok) { setOffline(!ok); return ok; }); }
  function startScheduler() {
    var every = EVERY[ME.role] || EVERY.customer, now0 = Date.now();
    Object.keys(every).forEach(function (k) { secT0[k] = now0 - Math.floor(Math.random() * every[k] * 0.5); });   // spread the users in time
    setInterval(function () {
      if (typeof document !== 'undefined' && document.hidden) return;
      if (offlineNow) { if (Date.now() - lastProbe >= 10000) { lastProbe = Date.now(); checkNet(); } return; }
      var now = Date.now();
      Object.keys(every).forEach(function (sec) {
        if (sec === 'offers' && !ME.online) return;
        var empty = sec === 'stat' && !DB.stores.length;                       // nothing loaded yet: retry soon, never back off
        var mult = empty ? 1 : Math.min(8, Math.pow(2, secFail[sec] || 0));
        if (now - (secT0[sec] || 0) >= (empty ? 10000 : every[sec]) * mult) refresh(sec);
      });
    }, 1000);
    document.addEventListener('visibilitychange', function () { if (!document.hidden) { walletStale = true; setTimeout(function () { refresh(); }, Math.floor(Math.random() * 1200)); } });
    window.addEventListener('online', function () { checkNet(); });
    window.addEventListener('offline', function () { setTimeout(checkNet, 1500); });
  }
  /* Dispatch heartbeat: expires old offers and moves waiting orders to the next courier. Only when it can matter. */
  function maybeTick() {
    if (!ME || !sb || Date.now() - lastTick < 4000) return;
    var need_ = ME.role === 'driver' ? !!ME.online : (ME.role === 'admin' || ME.role === 'merchant') ? DB.orders.some(function (o) { return !o.driver_id && (o.status === 'preparing' || o.status === 'ready'); }) : false;
    if (need_) { lastTick = Date.now(); sb.rpc('dispatch_tick').then(function () { }, function () { }); }
  }
  var UUID = /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/;
  /* cart -> server lines. Accepts a list of {item_id, qty, options, note} or a legacy {itemId: qty} map. Returns null if anything looks wrong. */
  function linesOf(src, notes) {
    var arr = Array.isArray(src) ? src : Object.keys(src || {}).map(function (id) { return { item_id: id, qty: src[id], note: (notes || {})[id] }; });
    if (!arr.length || arr.length > 60) return null;
    var out = [];
    for (var i = 0; i < arr.length; i++) {
      var l = arr[i], q = Math.floor(+l.qty), ops = Array.isArray(l.options) ? l.options : [];
      if (!UUID.test(String(l.item_id)) || !(q >= 1 && q <= 50) || ops.length > 40) return null;
      for (var k = 0; k < ops.length; k++) if (!UUID.test(String(ops[k]))) return null;
      out.push({ item_id: l.item_id, qty: q, options: ops, note: String(l.note || '').slice(0, 120) });
    }
    return out;
  }
  function errKey(e) {
    var m = String((e && e.message) || '').toLowerCase();
    var ks = ['store_location_missing', 'link_disabled', 'already_linked', 'refund_too_high', 'refund_needs_order', 'wallet_changed', 'points_changed', 'points_min_order', 'points_min', 'bad_gift', 'photo_required', 'bad_time', 'bad_group', 'group_closed', 'too_early', 'insufficient_funds', 'already_refunded', 'note_required', 'phone_locked', 'phone_cooldown', 'account_blocked', 'ticket_expired', 'ticket_exists', 'ticket_closed', 'not_found', 'fee_changed', 'too_far', 'phone_required', 'address_required', 'bad_options', 'no_offer', 'busy', 'already_rated', 'too_many_orders', 'promo_offer', 'promo_invalid', 'promo_min', 'promo_used', 'promo_limit', 'too_many', 'discount_over_max', 'bad_value', 'bad_phone', 'store_unavailable', 'unavailable', 'closed', 'empty', 'bad_transition', 'not_approved', 'not_allowed', 'user_not_found', 'blocked', 'name_taken', 'no_template', 'cash_required', 'note_required', 'auth'];
    for (var i = 0; i < ks.length; i++) if (m.indexOf(ks[i]) >= 0) return ks[i];
    return 'generic';
  }
  function rpc(name, args, okToast) {
    return sb.rpc(name, args).then(function (r) {
      if (r.error) { console.error(r.error); return { error: errKey(r.error), detail: String((r.error && r.error.message) || '').slice(0, 140) }; }
      if (okToast) toast(t('saved'));
      return refresh().then(function () { return { data: r.data }; });
    });
  }
  function done(r, quiet) {
    if (r.error) { console.error(r.error); toast(t('err_generic'), true); return { error: 'generic', toasted: true }; }
    if (!quiet) toast(t('saved'));
    return refresh().then(function () { return { ok: true }; });
  }
  function doneQ(r) { return done(r, true); }
  function storeByName(n) { return DB.stores.find(function (s) { return s.name === n; }); }
  function cleanStore(f) { var c = Object.assign({}, f); if (typeof c.phone === 'string') c.phone = c.phone.trim() === '' ? null : (normPhone(c.phone) || c.phone.trim()); return c; }
  function validStore(f) {
    var n = function (k, lo, hi) { if (f[k] == null || f[k] === '') return true; var v = +f[k]; return isFinite(v) && v >= lo && v <= hi; };
    if (!(n('commission_pct', 0, 100) && n('discount_pct', 0, 100) && n('max_discount_pct', 0, 100) && n('fee_base', 0, 100000) && n('fee_per_km', 0, 100000) && n('lat', -90, 90) && n('lng', -180, 180) && n('rating', 0, 5) && n('rating_count', 0, 100000000))) return false;
    if (f.google_place_id != null && f.google_place_id !== '' && !/^[A-Za-z0-9_-]{10,200}$/.test(String(f.google_place_id))) return false;
    if ((f.lat == null) !== (f.lng == null) && ('lat' in f || 'lng' in f)) return false;
    if (f.name != null && (String(f.name).trim().length < 1 || String(f.name).length > 80)) return false;
    if (f.description != null && String(f.description).length > 500) return false;
    if (f.address != null && String(f.address).length > 200) return false;
    if (f.phone != null && f.phone !== '' && !normPhone(f.phone)) return false;
    return true;
  }
  function validBanner(f) {
    if (f.placement != null && f.placement !== 'top' && f.placement !== 'bottom') return false;
    var d = function (v) { return v == null || (typeof v === 'string' && isFinite(Date.parse(v))); };
    if (!d(f.starts_at) || !d(f.ends_at)) return false;
    if (f.starts_at && f.ends_at && Date.parse(f.ends_at) <= Date.parse(f.starts_at)) return false;
    if (f.title != null && (String(f.title).trim().length < 1 || String(f.title).length > 80)) return false;
    return true;
  }
  function validPromo(f) {
    if (f.code != null && !/^[A-Za-z0-9_-]{3,20}$/.test(String(f.code))) return false;
    if (f.kind != null && f.kind !== 'percent' && f.kind !== 'fixed') return false;
    if (f.value != null) { var v = +f.value; if (!isFinite(v) || v <= 0 || (f.kind === 'percent' && v > 100) || v > 100000) return false; }
    if (f.min_order != null && (!isFinite(+f.min_order) || +f.min_order < 0)) return false;
    if (f.max_uses != null && (!isFinite(+f.max_uses) || +f.max_uses < 1 || +f.max_uses > 1000000)) return false;
    var d = function (x) { return x == null || (typeof x === 'string' && isFinite(Date.parse(x))); };
    if (!d(f.starts_at) || !d(f.ends_at)) return false;
    if (f.starts_at && f.ends_at && Date.parse(f.ends_at) <= Date.parse(f.starts_at)) return false;
    return true;
  }
  function badPromo() { toast(t('err_bad_promo'), true); return Promise.resolve({ error: 'bad_promo', toasted: true }); }
  function badBanner() { toast(t('err_bad_banner'), true); return Promise.resolve({ error: 'bad_banner', toasted: true }); }
  function validItem(f) {
    if (f.name != null && (String(f.name).trim().length < 1 || String(f.name).length > 80)) return false;
    if (f.price != null && (!isFinite(+f.price) || +f.price < 0 || +f.price > 100000)) return false;
    if (f.image != null && typeof f.image === 'string' && f.image.length > 700000) return false;
    return true;
  }
  function cleanPct(v) { var n = +v; return isFinite(n) && n > 0 && n <= 100 ? Math.round(n * 100) / 100 : 0; }
  /* Tajikistan numbers only: +992 and 9 digits. Accepts 9 digits, 992..., 0..., +992... Returns '+992XXXXXXXXX' or null. */
  function normPhone(v) {
    var d = String(v == null ? '' : v).replace(/\D/g, '');
    if (/^992[0-9]{9}$/.test(d)) return '+' + d;
    if (/^[0-9]{9}$/.test(d)) return '+992' + d;
    if (/^0[0-9]{9}$/.test(d)) return '+992' + d.slice(1);
    return null;
  }
  function num(v) { if (v === null || v === undefined || v === '' || typeof v === 'boolean') return NaN; var n = +v; return isFinite(n) ? n : NaN; }
  function cleanAddr(f) {
    var one = function (v) { return String(v == null ? '' : v).replace(/\s+/g, ' ').trim(); };
    var street = one(f.street), house = one(f.house), ent = one(f.entrance), flr = one(f.floor), apt = one(f.apartment), note = one(f.note);
    var lat = num(f.lat), lng = num(f.lng), lab = f.label;
    if (['home', 'work', 'other'].indexOf(lab) < 0 || street.length < 3 || street.length > 120) return null;
    if (house.length < 1 || house.length > 20 || ent.length > 10 || flr.length > 10 || apt.length > 10 || note.length > 120) return null;
    if (isNaN(lat) || isNaN(lng) || lat < -90 || lat > 90 || lng < -180 || lng > 180) return null;
    return { label: lab, street: street, house: house, entrance: ent || null, floor: flr || null, apartment: apt || null, note: note || null, lat: lat, lng: lng };
  }
  function cleanSection(v) { v = String(v == null ? '' : v).replace(/\s+/g, ' ').trim().slice(0, 40); return v || null; }
  function badStore() { toast(t('err_bad_value'), true); return Promise.resolve({ error: 'bad_value', toasted: true }); }
  function me() { return ME ? { id: ME.id, name: ME.name || ME.email, email: ME.email, phone: ME.phone || '', cashLimit: +ME.cash_limit || 1000, blocked: !!ME.accept_blocked, banned: !!ME.banned_at, bannedReason: ME.banned_reason || '' } : null; }

  /* ---------- login screens ---------- */
  var IN = 'style="width:100%;height:48px;padding:0 14px;margin-bottom:10px;border:1.5px solid #eeeef1;border-radius:14px;font-size:15px;background:#f7f7f9;outline:0"';
  var BT = 'style="width:100%;height:50px;border:0;border-radius:999px;background:#f1511b;color:#fff;font-weight:700;font-size:16px;margin-top:6px;cursor:pointer"';
  var LOGO = '<svg width="64" height="64" viewBox="0 0 64 64" aria-hidden="true"><circle cx="32" cy="32" r="32" fill="#fff"/><path d="M20 26h24l-2 18a3 3 0 0 1-3 2.6H25a3 3 0 0 1-3-2.6z" fill="none" stroke="#f1511b" stroke-width="3.4" stroke-linejoin="round"/><path d="M26 26v-2a6 6 0 0 1 12 0v2" fill="none" stroke="#f1511b" stroke-width="3.4" stroke-linecap="round"/></svg>';
  function overlay(html, brand) {
    var d = $('tlb-ov');
    if (!d) { d = document.createElement('div'); d.id = 'tlb-ov'; d.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;z-index:9998;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:20px;font:15px -apple-system,BlinkMacSystemFont,sans-serif;overflow:auto'; document.body.appendChild(d); }
    d.style.background = brand ? 'linear-gradient(180deg,#f1511b,#e24410)' : '#f6f6f8';
    d.innerHTML = (brand ? '<div style="text-align:center;color:#fff;margin-bottom:22px">' + LOGO + '<div style="font-size:30px;font-weight:800;margin-top:10px;letter-spacing:.3px">Talabat</div><div data-i18n="tagline" style="opacity:.92;margin-top:4px;font-size:14px"></div></div>' : '') +
      '<div style="background:#fff;border-radius:22px;padding:22px;width:100%;max-width:360px;box-shadow:0 12px 40px #0003">' + html + '</div>';
    applyI18n();
  }
  var bootTimer = null, lastErr = '';
  function bootShow() {
    if ($('tlb-boot')) return;
    var d = document.createElement('div'); d.id = 'tlb-boot';
    d.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;z-index:9990;background:#f6f6f8;display:flex;flex-direction:column;align-items:center;justify-content:center;font:15px -apple-system,BlinkMacSystemFont,sans-serif;color:#6b7280';
    d.innerHTML = '<div style="width:44px;height:44px;border-radius:50%;border:4px solid #ffd9cc;border-top-color:#f1511b;animation:tlbspin 0.9s linear infinite"></div><div style="margin-top:14px" data-i18n="loading"></div><style>@keyframes tlbspin{to{transform:rotate(360deg)}}</style>';
    document.body.appendChild(d); applyI18n();
    clearTimeout(bootTimer); bootTimer = setTimeout(function () { if ($('tlb-boot')) bootFail(lastErr || 'timeout'); }, 12000);
  }
  function bootHide() { clearTimeout(bootTimer); var d = $('tlb-boot'); if (d) d.remove(); }
  function bootFail(err) {
    lastErr = String((err && err.message) || err || '').slice(0, 160);
    bootHide();
    overlay('<div style="text-align:center"><div style="width:58px;height:58px;border-radius:50%;background:#fff0e5;color:#c2410c;display:flex;align-items:center;justify-content:center;margin:0 auto 12px;font-size:26px">!</div><b style="font-size:18px" data-i18n="bootT"></b><p style="color:#6b7280;font-size:14px;margin:8px 0 14px" data-i18n="bootS"></p>' + (lastErr ? '<p style="color:#9ca3af;font-size:11px;word-break:break-all;margin-bottom:12px">' + esc(lastErr) + '</p>' : '') + '</div><button id="tlb-rl" data-i18n="bootReload" ' + BT + '></button><button id="tlb-rs2" data-i18n="bootSignout" ' + BT.replace('#f1511b', '#f1f1f4').replace('color:#fff', 'color:#1c1c21') + '></button>', true);
    $('tlb-rl').onclick = function () { location.reload(); };
    $('tlb-rs2').onclick = function () { try { localStorage.removeItem('tlb-auth-' + need); } catch (e) { } location.reload(); };
  }
  function logout() { window.TLB_SIGNING_OUT = true; try { sessionStorage.removeItem('tlb-ui-' + need); } catch (e) { } sb.auth.signOut().then(function () { location.reload(); }); }
  var authMode = 'in', resendAt = 0;
  function authErr(e) {
    var m = String((e && e.message) || '').toLowerCase(), c = String((e && (e.code || e.error_code)) || '');
    if (m.indexOf('invalid login') >= 0 || c === 'invalid_credentials') return t('authWrong');
    if (m.indexOf('already registered') >= 0 || c === 'user_already_exists' || c === 'email_exists') return t('authExists');
    if (c === 'weak_password' || (m.indexOf('password') >= 0 && (m.indexOf('least') >= 0 || m.indexOf('weak') >= 0 || m.indexOf('short') >= 0))) return t('authPwShort');
    if (m.indexOf('rate limit') >= 0 || c === 'over_email_send_rate_limit' || c === 'over_request_rate_limit' || (e && e.status === 429)) return t('authRate');
    if (m.indexOf('not confirmed') >= 0 || c === 'email_not_confirmed') return t('authUnconf');
    if (m.indexOf('signups not allowed') >= 0 || m.indexOf('signup is disabled') >= 0 || c === 'signup_disabled') return t('authNoSignup');
    if (m.indexOf('invalid') >= 0 && m.indexOf('email') >= 0) return t('authBadEmail');
    return t('err_generic') + ' (' + String((e && e.message) || '').slice(0, 80) + ')';
  }
  function authTabs() {
    if (need === 'admin') return '';
    var on = 'background:#fff;color:#1c1c21;box-shadow:0 1px 4px #0002', off = 'background:none;color:#8b8f98';
    var b = 'flex:1;border:0;border-radius:10px;padding:10px 0;font-weight:700;font-size:14px;cursor:pointer;';
    return '<div style="display:flex;background:#f1f1f4;border-radius:13px;padding:3px;margin-bottom:16px"><button id="tlb-t-in" data-i18n="login" style="' + b + (authMode === 'in' ? on : off) + '"></button><button id="tlb-t-up" data-i18n="signup" style="' + b + (authMode === 'up' ? on : off) + '"></button></div>';
  }
  function showSignupDone(email) {
    overlay('<div style="text-align:center"><div style="width:58px;height:58px;border-radius:50%;background:#e6f6ed;color:#1fa05a;display:flex;align-items:center;justify-content:center;margin:0 auto 12px;font-size:28px">✉</div><b style="font-size:18px" data-i18n="authSentT"></b><p style="color:#6b7280;font-size:14px;margin:8px 0 4px" data-i18n="authSentS"></p><p style="font-weight:700;margin-bottom:14px;word-break:break-all">' + esc(email) + '</p></div>' +
      '<div id="tlb-er" style="color:#1fa05a;font-size:13px;min-height:16px;text-align:center;margin-bottom:8px"></div>' +
      '<button id="tlb-rs" data-i18n="authResend" ' + BT.replace('#f1511b', '#f1f1f4').replace('color:#fff', 'color:#1c1c21') + '></button><button id="tlb-bk" data-i18n="authBack" ' + BT + '></button>', true);
    $('tlb-bk').onclick = function () { authMode = 'in'; showLogin(''); };
    $('tlb-rs').onclick = function () {
      var now = Date.now(); if (now < resendAt) { $('tlb-er').style.color = '#d92d20'; $('tlb-er').textContent = t('authWait'); return; }
      resendAt = now + 60000;
      sb.auth.resend({ type: 'signup', email: email }).then(function (r) { $('tlb-er').style.color = r.error ? '#d92d20' : '#1fa05a'; $('tlb-er').textContent = r.error ? authErr(r.error) : t('authResent'); });
    };
  }
  function showLogin(msg, mode) {
    if (mode) authMode = mode;
    var su = authMode === 'up' && need !== 'admin';
    overlay(authTabs() +
      (su ? '<input id="tlb-nm" type="text" maxlength="40" autocomplete="name" data-i18n-ph="authNameL" ' + IN + '><input id="tlb-ph" type="tel" inputmode="tel" autocomplete="tel" maxlength="17" data-i18n-ph="authPhoneL" ' + IN + '>' : '') +
      '<input id="tlb-em" type="email" autocomplete="username" autocapitalize="off" placeholder="Email" ' + IN + '>' +
      '<div style="position:relative"><input id="tlb-pw" type="password" autocomplete="' + (su ? 'new-password' : 'current-password') + '" data-i18n-ph="password" ' + IN.replace('padding:0 14px', 'padding:0 48px 0 14px') + '><button id="tlb-eye" type="button" aria-label="show" style="position:absolute;right:6px;top:4px;width:40px;height:40px;border:0;background:none;font-size:18px;cursor:pointer;color:#8b8f98">👁</button></div>' +
      (su ? '<div data-i18n="authPwHint2" style="font-size:12px;color:#8b8f98;margin:-4px 0 8px;line-height:1.4"></div>' : '') +
      '<div id="tlb-er" role="alert" style="color:#d92d20;background:' + (msg ? '#fdeceb' : 'transparent') + ';border-radius:12px;padding:' + (msg ? '10px 12px' : '0') + ';font-size:13px;font-weight:600;margin-bottom:10px;min-height:0">' + esc(msg || '') + '</div>' +
      '<button id="tlb-go" ' + BT + '></button>', true);
    $('tlb-go').textContent = su ? t('signup') : t('login');
    var show = function (txt) { var e = $('tlb-er'); e.textContent = txt; e.style.background = txt ? '#fdeceb' : 'transparent'; e.style.padding = txt ? '10px 12px' : '0'; };
    if ($('tlb-t-in')) { $('tlb-t-in').onclick = function () { showLogin('', 'in'); }; $('tlb-t-up').onclick = function () { showLogin('', 'up'); }; }
    $('tlb-eye').onclick = function () { var p = $('tlb-pw'); p.type = p.type === 'password' ? 'text' : 'password'; };
    var busy = false;
    var go = function () {
      if (busy) return;
      var wait = authWait(); if (wait > 0) return show(t('authLock').replace('{s}', wait));
      var email = $('tlb-em').value.trim().toLowerCase(), pw = $('tlb-pw').value, name = su ? $('tlb-nm').value.trim() : '', phone = su ? normPhone($('tlb-ph').value) : null;
      show('');
      if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return show(t('authBadEmail'));
      if (su && name.length < 2) return show(t('authNameShort'));
      if (su && !phone) return show(t('err_bad_phone'));
      if (su && pw.length < 8) return show(t('authPwShort'));
      if (!pw) return show(t('authPwShort'));
      busy = true; $('tlb-go').disabled = true; $('tlb-go').textContent = t('authWaitB');
      var req = su ? sb.auth.signUp({ email: email, password: pw, options: { data: { name: name.slice(0, 40), phone: phone } } }) : sb.auth.signInWithPassword({ email: email, password: pw });
      req.then(function (r) {
        busy = false;
        if (r.error) { authFail(); $('tlb-go').disabled = false; $('tlb-go').textContent = su ? t('signup') : t('login'); return show(authErr(r.error)); }
        if (!r.data || !r.data.session) { return showSignupDone(email); }
        enter(r.data.user);
      }, function () { busy = false; $('tlb-go').disabled = false; $('tlb-go').textContent = su ? t('signup') : t('login'); show(t('err_generic')); });
    };
    $('tlb-go').onclick = go;
    ['tlb-em', 'tlb-pw', 'tlb-nm', 'tlb-ph'].forEach(function (id) { var e = $(id); if (e) e.onkeydown = function (ev) { if (ev.key === 'Enter') go(); }; });
  }
  var AF = { n: 0, until: 0, t0: 0 };
  function authFail() { var now = Date.now(); if (now - AF.t0 > 600000) { AF.n = 0; AF.t0 = now; } AF.n++; if (AF.n >= 5) { AF.until = now + Math.min(300000, 30000 * Math.pow(2, AF.n - 5)); } }
  function authWait() { return Math.max(0, Math.ceil((AF.until - Date.now()) / 1000)); }
  function showApply() {
    overlay('<div style="text-align:center"><div style="width:58px;height:58px;border-radius:50%;background:#fff0ea;color:#f1511b;display:flex;align-items:center;justify-content:center;margin:0 auto 12px;font-size:26px">🛵</div><b style="font-size:18px" data-i18n="applyT"></b><p style="color:#6b7280;font-size:14px;margin:8px 0 14px" data-i18n="applyS"></p></div>' +
      '<input id="tlb-ap" type="tel" autocomplete="tel" inputmode="tel" maxlength="16" placeholder="+992…" ' + IN + '><div id="tlb-er" role="alert" style="color:#d92d20;font-size:13px;font-weight:600;min-height:18px;margin-bottom:8px"></div>' +
      '<button id="tlb-go" data-i18n="applyB" ' + BT + '></button><button id="tlb-lo" data-i18n="logout" ' + BT.replace('#f1511b', '#f1f1f4').replace('color:#fff', 'color:#1c1c21') + '></button>', true);
    $('tlb-lo').onclick = logout;
    $('tlb-go').onclick = function () {
      var p = $('tlb-ap').value.replace(/[\s()-]/g, '');
      p = normPhone(p); if (!p) { $('tlb-er').textContent = t('err_bad_phone'); return; }
      $('tlb-go').disabled = true;
      sb.rpc('set_my_phone', { p_phone: p }).then(function (r) {
        if (r.error) { $('tlb-go').disabled = false; $('tlb-er').textContent = t('err_generic'); return; }
        return sb.rpc('apply_as_driver').then(function (r2) {
          if (r2.error) { $('tlb-go').disabled = false; $('tlb-er').textContent = t('err_generic'); return; }
          return enter({ id: ME.id, email: ME.email });
        });
      });
    };
  }
  var APP_OF = { admin: 'admin.html', merchant: 'merchant.html', driver: 'driver.html', customer: 'customer.html' };
  function blocked(key) {
    var hint = '', other = ME && key === 'wrongRole' && APP_OF[ME.role] && ME.role !== need ? ME.role : '';
    if (other) {
      /* the account is fine, it is just in the wrong app: say which one it belongs to and give a button */
      hint = '<p style="color:#4a5568;margin:0 0 12px;font-size:14px;line-height:1.45">' + esc(t('roleIs').replace('{role}', t('role_' + other))) + '</p>' +
        '<a id="tlb-go-app" href="' + APP_OF[other] + '" style="display:flex;align-items:center;justify-content:center;width:100%;height:50px;border-radius:999px;background:#f1511b;color:#fff;font-weight:700;font-size:16px;text-decoration:none;margin-top:6px;box-sizing:border-box">' + esc(t('openApp').replace('{role}', t('role_' + other))) + '</a>';
    }
    overlay('<h3 style="margin-bottom:10px;color:#1a202c" data-i18n="' + (other ? 'wrongApp' : key) + '"></h3><p style="color:#718096;margin-bottom:14px;font-size:13px">' + esc(ME.email) + ' — ' + esc(ME.role) + '</p>' + hint + '<button id="tlb-lo" data-i18n="logout" ' + BT.replace('#f1511b', other ? '#f1f1f4' : '#f1511b').replace('color:#fff', other ? 'color:#1c1c21' : 'color:#fff') + '></button>');
    $('tlb-lo').onclick = logout;
  }
  function logoutBtn() {
    if (!$('tlb-out')) {
      var b = document.createElement('div'); b.id = 'tlb-out'; b.setAttribute('data-i18n', 'logout'); b.textContent = t('logout');
      b.style.cssText = CHIP + ';margin-left:auto';
      b.onclick = logout; chromeBar().appendChild(b);
    }
    applyChrome();
  }
  function enter(user) {
    return sb.from('profiles').select('*').eq('id', user.id).single().then(function (x) {
      if (x.error || !x.data) { bootHide(); showLogin(x.error ? x.error.message : 'profile'); return; }
      ME = Object.assign({ email: user.email }, x.data);
      logoutBtn();
      if (need === 'driver' && ME.role === 'customer') { bootHide(); return showApply(); }
      if (need === 'merchant' && ME.role === 'customer') { bootHide(); return blocked('notLinked'); }
      MYPERMS = need === 'admin' && ME.role === 'admin' ? ALL_PERMS.slice() : [];
      var gate = Promise.resolve(ME.role === need);
      /* staff: a normal account that a super admin added in staff_members; the server decides what it may do (my_perms) */
      if (need === 'admin' && ME.role !== 'admin') {
        gate = sb.rpc('my_perms').then(function (r) {
          var p = r && !r.error && Array.isArray(r.data) ? r.data.filter(function (x) { return ALL_PERMS.indexOf(x) >= 0; }) : [];
          MYPERMS = p; return p.length > 0;
        }, function () { return false; });
      }
      return gate.then(function (ok) {
        if (!ok) { bootHide(); return blocked('wrongRole'); }
        if (need === 'driver' && ME.driver_status !== 'approved') { bootHide(); return blocked('pendingApp'); }
        var o = $('tlb-ov'); if (o) o.remove();
        return refresh().then(function () {
          try { subscribeRealtime(); } catch (e) { console.error(e); }
          startScheduler();
          bootHide();
          onReady(me());
        });
      });
    }).catch(function (e) { console.error(e); bootFail(e); });
  }

  /* ---------- API ---------- */
  /* ===================== staff UI (admin panel + restaurant app only; the customer and courier apps never call these) =====================
     One icon family: 24×24 outline, stroke 2, round caps — the same drawing style the restaurant app already used. */
  var ICONS = {
    plus: '<path d="M12 5v14M5 12h14"/>', x: '<path d="M6 6l12 12M18 6L6 18"/>', check: '<path d="M5 12l5 5L20 7"/>',
    search: '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/>', chev: '<path d="M9 6l6 6-6 6"/>', back: '<path d="M15 6l-6 6 6 6"/>',
    doc: '<path d="M14 3v4a1 1 0 0 0 1 1h4M5 3h9l5 5v11a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2zM9 13h6M9 17h6"/>',
    store: '<path d="M3 9l1-5h16l1 5M3 9a3 3 0 0 0 6 0 3 3 0 0 0 6 0 3 3 0 0 0 6 0M5 12v8h14v-8"/>',
    bike: '<circle cx="6" cy="17" r="3"/><circle cx="18" cy="17" r="3"/><path d="M6 17l4-8h5l3 8M10 9H8"/>',
    users: '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0M16 4.6a3.5 3.5 0 0 1 0 6.8M18.5 13.6A6.5 6.5 0 0 1 21.5 20"/>',
    user: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    help: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="3.5"/><path d="M5.6 5.6l4 4M14.4 14.4l4 4M18.4 5.6l-4 4M9.6 14.4l-4 4"/>',
    text: '<path d="M5 5h14M12 5v14M9 19h6"/>', star: '<path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z"/>',
    image: '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="M21 16l-5-5-9 9"/>',
    tag: '<path d="M3 12V4h8l9 9-8 8zM7.5 8.5h.01"/>', award: '<circle cx="12" cy="9" r="6"/><path d="M8.5 14L7 22l5-3 5 3-1.5-8"/>',
    log: '<path d="M3 12a9 9 0 1 0 3-6.7M3 4v4h4M12 7v5l3 2"/>', shield: '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/>',
    box: '<path d="M21 8l-9-5-9 5 9 5zM3 8v8l9 5 9-5V8M12 13v8"/>', cash: '<rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="12" cy="12" r="2.5"/><path d="M6 12h.01M18 12h.01"/>',
    percent: '<path d="M19 5L5 19"/><circle cx="7" cy="7" r="2.5"/><circle cx="17" cy="17" r="2.5"/>', clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    pin: '<path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/>', home: '<path d="M3 11l9-7 9 7M5 10v10h14V10"/>',
    door: '<path d="M5 21V4a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v17M3 21h18M15 12h.01"/>',
    gift: '<rect x="3" y="8" width="18" height="4" rx="1"/><path d="M5 12v9h14v-9M12 8v13M12 8S10.5 3 8 3a2.5 2.5 0 0 0 0 5M12 8s1.5-5 4-5a2.5 2.5 0 0 1 0 5"/>',
    receipt: '<path d="M5 3h14v18l-3-2-2 2-2-2-2 2-2-2-3 2zM9 8h6M9 12h6M9 16h3"/>', chat: '<path d="M4 5h16v11H9l-5 4z"/>',
    edit: '<path d="M4 20h4L19 9l-4-4L4 16zM13.5 6.5l4 4"/>', save: '<path d="M5 3h11l3 3v15H5zM8 3v5h7M8 21v-7h8v7"/>',
    link: '<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>',
    refresh: '<path d="M20 12a8 8 0 1 1-2.3-5.7M20 4v5h-5"/>', folder: '<path d="M3 6a1 1 0 0 1 1-1h5l2 2h9a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1z"/>',
    alert: '<path d="M12 4L2 20h20zM12 10v4M12 17h.01"/>', ban: '<circle cx="12" cy="12" r="9"/><path d="M5.6 5.6l12.8 12.8"/>',
    clip: '<path d="M9 3h6v3H9zM7 4.5H5V21h14V4.5h-2M9 11h6M9 15h4"/>', cal: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    card: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 10h18M7 15h3"/>', building: '<path d="M4 21V5a1 1 0 0 1 1-1h9a1 1 0 0 1 1 1v16M15 9h4a1 1 0 0 1 1 1v11M3 21h18M8 8h3M8 12h3M8 16h3"/>',
    cam: '<path d="M4 8h3l2-3h6l2 3h3v11H4z"/><circle cx="12" cy="13" r="3.5"/>', phone: '<path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2"/>',
    chart: '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>', out: '<path d="M15 4h4v16h-4M10 8l-4 4 4 4M6 12h10"/>', globe: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>',
    trash: '<path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/>', map: '<path d="M9 4L3 6v14l6-2 6 2 6-2V4l-6 2zM9 4v14M15 6v14"/>', bag: '<path d="M5 8h14l-1 13H6zM9 8V6a3 3 0 0 1 6 0v2"/>',
    dot: '<circle cx="12" cy="12" r="3"/>'
  };
  function icon(n, s, label) {
    var z = s || 16;
    return '<svg class="tic" viewBox="0 0 24 24" width="' + z + '" height="' + z + '" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" ' +
      (label ? 'role="img" aria-label="' + String(label).replace(/"/g, '&quot;') + '"' : 'aria-hidden="true"') + '>' + (ICONS[n] || ICONS.dot) + '</svg>';
  }
  /* shared look of the staff apps: light page, white cards with a thin border, orange only for the active item and the main action,
     dark side menu on wide screens (the same menu entries; phones keep their compact menu) */
  var STAFF_CSS = [
    /* phones and tablets keep the existing layout, sizes and spacing; only the icon family is shared */
    '.tic{display:inline-block;vertical-align:-3px;flex-shrink:0}',
    '.card>b .tic,.card>.row>b .tic{color:var(--o)}',
    '.tabs button .tic{display:none}.sbrand{display:none}',
    '.amt{white-space:nowrap}',
    /* wide screens (>=1024px): dark side menu built from the same menu entries */
    '@media(min-width:1024px){',
    ' body.st-admin{padding-left:272px!important}body.st-merchant{padding-left:256px!important;padding-bottom:30px!important}',
    ' .side{position:fixed;top:0;bottom:0;left:0;width:248px;background:#16171b;color:#c9ccd3;padding:20px 12px;overflow-y:auto;z-index:700}',
    ' .sbrand{display:flex;align-items:center;gap:10px;padding:2px 8px 18px;color:#fff;font-weight:800;font-size:19px;letter-spacing:.3px}.sbrand i{width:36px;height:36px;border-radius:11px;background:var(--o);display:flex;align-items:center;justify-content:center;font-style:normal}.sbrand small{display:block;font-size:11.5px;font-weight:600;color:#8d929c;letter-spacing:0}',
    ' .side .tabs{flex-direction:column;gap:4px;overflow:visible;margin:0}',
    ' .side .tabs button{flex:none;width:100%;display:flex;align-items:center;gap:10px;justify-content:flex-start;background:transparent;border:0;color:#c9ccd3;padding:11px 12px;font-size:14px;font-weight:500;border-radius:12px}',
    ' .side .tabs button .tic{display:inline-block}.side .tabs button:hover{background:#ffffff0f}.side .tabs .on{background:var(--o);color:#fff;font-weight:600}.side .tabs button em{margin-left:auto}',
    ' .nav{top:0;bottom:0!important;right:auto!important;width:232px;flex-direction:column;justify-content:flex-start;gap:4px;background:#16171b!important;border-radius:0!important;box-shadow:none!important;padding:84px 12px 20px!important;z-index:700}',
    ' .nav::before{content:"TALABOT";position:absolute;left:22px;top:26px;color:#fff;font-weight:800;font-size:19px;letter-spacing:.3px}',
    ' .nav div{flex:none!important;display:flex!important;align-items:center;gap:12px;text-align:left!important;padding:11px 12px!important;border-radius:12px;color:#c9ccd3!important;font-size:14px!important;font-weight:500!important}',
    ' .nav div span{display:inline-flex!important}.nav .on{background:var(--o);color:#fff!important}.nav div em{position:static!important;margin-left:auto}',
    '}'
  ].join('\n');
  function staffUI(role) {
    try { document.body.classList.add('st-' + role); } catch (e) { }
    if (document.getElementById('tlb-staff')) return;
    var st = document.createElement('style'); st.id = 'tlb-staff'; st.textContent = STAFF_CSS; document.head.appendChild(st);
  }
  /* Redraw of the same screen: patch the live page to match new HTML instead of rebuilding it (nodes that did not change are left alone:
     focus, an open picker, typed values, horizontal strips and the page height stay). Fields bound to app state (oninput/onchange)
     take the new value unless the user is in them. */
  function isChk(e) { return e.type === 'checkbox' || e.type === 'radio'; }
  function bound(e) { return e.hasAttribute('oninput') || e.hasAttribute('onchange'); }
  function morphKids(a, b) {
    var an = [].slice.call(a.childNodes), bn = [].slice.call(b.childNodes), i, x, y;
    for (i = 0; i < bn.length; i++) {
      x = an[i]; y = bn[i];
      if (!x) { a.appendChild(y); continue; }
      if (x.nodeType !== y.nodeType || x.nodeName !== y.nodeName || (x.nodeType === 1 && ((x.id || '') !== (y.id || '') || (x.getAttribute('type') || '') !== (y.getAttribute('type') || '')))) { a.replaceChild(y, x); continue; }
      if (x.nodeType !== 1) { if (x.nodeValue !== y.nodeValue) x.nodeValue = y.nodeValue; continue; }
      morphEl(x, y);
    }
    for (i = an.length - 1; i >= bn.length; i--) if (an[i].parentNode === a) a.removeChild(an[i]);
  }
  function morphEl(x, y) {
    var k, at = [].slice.call(x.attributes);
    for (k = 0; k < at.length; k++) if (!y.hasAttribute(at[k].name)) x.removeAttribute(at[k].name);
    for (k = 0; k < y.attributes.length; k++) if (x.getAttribute(y.attributes[k].name) !== y.attributes[k].value) x.setAttribute(y.attributes[k].name, y.attributes[k].value);
    var tg = x.nodeName, live = x === document.activeElement;
    if (tg === 'INPUT') { if (bound(x) && !live) { if (isChk(x)) { if (x.checked !== y.checked) x.checked = y.checked; } else if (x.type !== 'file' && x.value !== y.value) x.value = y.value; } return; }
    morphKids(x, y);
    if ((tg === 'TEXTAREA' || tg === 'SELECT') && bound(x) && !live && x.value !== y.value) x.value = y.value;
  }
  function morph(el, html) { var tp = document.createElement('template'); tp.innerHTML = html; morphKids(el, tp.content); }

  var TLBref = null;
  window.TLB = {
    icon: icon, staffUI: staffUI, morph: morph,
    version: VERSION,
    loadFailed: function () { return !!secFail.stat; },
    normPhone: normPhone,
    t: t, esc: esc, applyI18n: applyI18n, setLang: setLang, lang: function () { return lang; },
    addDict: function (ru, en) { Object.assign(I.ru, ru); Object.assign(I.en, en); },
    on: function (f) { subs.push(f); },
    /* role: 'customer' | 'merchant' | 'driver' | 'admin'. Each role keeps its own session, so all 4 apps can be open in one browser. */
    start: function (role, cb) {
      need = role; onReady = cb;
      sb = window.supabase.createClient(SB_URL, SB_KEY, { auth: { storageKey: 'tlb-auth-' + role } });
      bootShow();
      sb.auth.getSession().then(function (x) { if (x.data.session) return enter(x.data.session.user); bootHide(); showLogin(); })
        .catch(function (e) { console.error(e); bootFail(e); });
    },
    reload: function () { return refresh(); },
    me: me, logout: logout, toast: toast, beep: beep, ring: ring, audioReady: audioOk, unlockAudio: unlockNow, testSound: function () { unlockNow(); ringBeep(); }, fmtMsg: fmtMsg, openPoint: openPoint, pickLocation: pickLocation,
    chrome: function (on) { chromeOn = !!on; applyChrome(); },
    isCash: function (o) { return /^(cash|Cash|Наличн)/.test((o && o.payment) || ''); },
    unread: function (id) { return unread[id] || 0; },
    totalUnread: function () { var n = 0; for (var k in unread) n += unread[k]; return n; },
    markRead: function (id) { if (unread[id]) { unread[id] = 0; fire(); } },

    stores: function (all) { return DB.stores.filter(function (s) { return all || s.is_active; }); },
    myStores: function () { return DB.stores.filter(function (s) { return ME && s.owner_id === ME.id; }); },
    drivers: function () { return DB.drivers; },
    pendingItems: function () { return DB.items.filter(function (i) { return !i.approved; }).map(shapeItem); },
    allMenus: function (onlyAvail) {
      var o = {}; DB.stores.forEach(function (s) { o[s.name] = []; });
      DB.items.forEach(function (i) { if (onlyAvail && !(i.available && i.approved)) return; var n = storeName(i.store_id); if (o[n]) o[n].push(shapeItem(i)); });
      return o;
    },
    optionsOf: function (itemId, all) {
      return DB.groups.filter(function (g) { return g.item_id === itemId; }).map(function (g) {
        return { id: g.id, name: g.name, required: !!g.required, max: +g.max_sel || 1, sort: +g.sort || 0,
          options: DB.options.filter(function (o) { return o.group_id === g.id && (all || o.available); }).map(function (o) { return { id: o.id, name: o.name, price: +o.price_delta || 0, available: !!o.available }; }) };
      });
    },
    addGroup: function (itemId, f) { var n = String(f.name || '').trim(); if (!n || n.length > 60) return badStore(); return sb.from('item_option_groups').insert({ item_id: itemId, name: n, required: !!f.required, max_sel: Math.min(20, Math.max(1, Math.floor(+f.max || 1))) }).then(done); },
    updateGroup: function (id, f) { var u = {}; if ('name' in f) { var n = String(f.name || '').trim(); if (!n || n.length > 60) return badStore(); u.name = n; } if ('required' in f) u.required = !!f.required; if ('max' in f) u.max_sel = Math.min(20, Math.max(1, Math.floor(+f.max || 1))); return sb.from('item_option_groups').update(u).eq('id', id).then(function (r) { return done(r, true); }); },
    deleteGroup: function (id) { return sb.from('item_option_groups').delete().eq('id', id).then(done); },
    addOption: function (groupId, f) { var n = String(f.name || '').trim(), p = +f.price || 0; if (!n || n.length > 60 || !isFinite(p) || p < 0 || p > 100000) return badStore(); return sb.from('item_options').insert({ group_id: groupId, name: n, price_delta: Math.round(p * 100) / 100 }).then(done); },
    updateOption: function (id, f) { var u = {}; if ('name' in f) { var n = String(f.name || '').trim(); if (!n || n.length > 60) return badStore(); u.name = n; } if ('price' in f) { var p = +f.price; if (!isFinite(p) || p < 0 || p > 100000) return badStore(); u.price_delta = Math.round(p * 100) / 100; } if ('available' in f) u.available = !!f.available; return sb.from('item_options').update(u).eq('id', id).then(function (r) { return done(r, true); }); },
    deleteOption: function (id) { return sb.from('item_options').delete().eq('id', id).then(done); },
    addresses: function () { return DB.addresses; },
    addAddress: function (f) { var c = cleanAddr(f); if (!c) return badStore(); return sb.from('addresses').insert(Object.assign({ user_id: ME.id }, c)).select('id').single().then(function (r) { if (r.error) { console.error(r.error); toast(t('err_generic'), true); return { error: 'generic', toasted: true }; } return refresh().then(function () { return { ok: true, id: r.data ? r.data.id : null }; }); }); },
    updateAddress: function (id, f) { var c = cleanAddr(f); if (!c) return badStore(); return sb.from('addresses').update(c).eq('id', id).then(done); },
    deleteAddress: function (id) { return sb.from('addresses').delete().eq('id', id).then(done); },
    setDefaultAddress: function (id) { return sb.rpc('set_default_address', { p_id: id }).then(function (r) { return refresh().then(function () { return r.error ? { error: errKey(r.error) } : { ok: true }; }); }); },
    quote: function (storeN, lat, lng) {
      var st = storeByName(storeN); if (!st || isNaN(num(lat)) || isNaN(num(lng))) return Promise.resolve({ error: 'bad_value' });
      return sb.rpc('delivery_quote', { p_store: st.id, p_lat: num(lat), p_lng: num(lng) }).then(function (r) { if (r.error || !r.data || !isFinite(+r.data.fee)) return { error: r.error ? errKey(r.error) : 'generic' };
        var d = r.data, n = function (v) { return v == null ? null : +v; };
        return { fee: +d.fee, feeFull: n(d.fee_full), base: n(d.base), extra: n(d.extra) || 0, steps: n(d.steps) || 0, km: n(d.km), kmStraight: n(d.km_straight), freeKm: n(d.free_km), stepKm: n(d.step_km), stepPrice: n(d.step_price), maxKm: n(d.max_km), firstFree: !!d.first_free, feeType: d.fee_type };
      }, function () { return { error: 'generic' }; });
    },
    getMenu: function (n) { return this.allMenus(false)[n] || []; },
    ping: function (online) { return sb.rpc('driver_ping', { p_online: !!online }).then(function (r) { return { ok: !r.error }; }, function () { return { ok: false }; }); },
    isOpen: function (n) { var s = storeByName(n); return !!s && s.is_open && s.is_active; },
    setOpen: function (n, v) { var s = storeByName(n); return s ? rpc('set_store_open', { p_store: s.id, p_open: !!v }, true) : Promise.resolve({ error: 'generic' }); },

    order: function (id) { return ORD.find(function (o) { return o.id == id; }) || null; },
    /* C-1 (27 Oct): health of the orders refresh, separate from the data. On a failed refresh the last loaded orders (amount,
       status, driver) stay exactly as they were; this only says whether they are current.
       -> { failing: bool, failures: n, lastOkAt: ms|null, lastFailAt: ms|null } (times = this phone's clock of the attempt;
       never an order / status event time). */
    ordersHealth: function () {
      return { failing: (secFail.orders || 0) > 0, failures: secFail.orders || 0, lastOkAt: secOk.orders || null, lastFailAt: secFailAt.orders || null };
    },
    /* C-2 (27 Oct): time of the CURRENT status of an order, from order_events (kind = status name, at = server time).
       Loads the order's events on first call and again when the status changes (errors retried after 30 s).
       -> { status, at: ms|null, source: 'event' | 'placed' | null, state: 'ok' | 'loading' | 'unreadable' | 'none' }
       'placed' = pending only: the order's own creation time (the pending event). Never the refresh time, the courier
       position time or the phone clock. 'unreadable' = the events could not be read (e.g. no permission) -> show «unknown». */
    statusAt: function (id) {
      var o = ORD.find(function (x) { return x.id == id; }); if (!o) return { status: null, at: null, source: null, state: 'none' };
      var st = evSt[o.id], now = Date.now();
      if (sb && ME && (!st || (!st.busy && (st.status !== o.status || (st.err && now - st.t > 30000))))) {
        var mark = evSt[o.id] = { status: o.status, t: now, busy: true, err: st ? st.err : false, loaded: st ? st.loaded : false };
        sb.from('order_events').select('order_id,kind,at').eq('order_id', o.id).order('at').then(function (r) {
          mark.busy = false; mark.t = Date.now();
          if (r.error) { mark.err = true; }
          else { mark.err = false; mark.loaded = true; DB.events = DB.events.filter(function (e) { return e.order_id !== o.id; }).concat(r.data || []); }
          fireSoon();
        }, function () { mark.busy = false; mark.err = true; mark.t = Date.now(); fireSoon(); });
        st = mark;
      }
      var hit = null; DB.events.forEach(function (e) { if (e.order_id == o.id && e.kind === o.status) { var t = Date.parse(e.at); if (isFinite(t) && (hit === null || t > hit)) hit = t; } });
      if (hit !== null) return { status: o.status, at: hit, source: 'event', state: 'ok' };
      if (o.status === 'pending' && isFinite(o.createdAt)) return { status: o.status, at: o.createdAt, source: 'placed', state: 'ok' };
      return { status: o.status, at: null, source: null, state: st && st.err ? 'unreadable' : st && (st.busy && !st.loaded) ? 'loading' : 'none' };
    },
    /* C-3 (27 Oct): short tracking states for the Restaurant / Courier cards (designer R1.1 wording). Order status and the
       driver field only; a driver being assigned never means «ready». stale = the orders refresh is failing (C-1): the last
       known states are kept and marked.
       -> { restaurant: {key,label}, courier: {key,label}|null, ended: key|null, stale: bool } */
    trackStatus: function (o) {
      if (!o) return null;
      var stale = (secFail.orders || 0) > 0, L = function (k) { return { key: k, label: t(k) }; };
      if (['delivered', 'cancelled', 'rejected'].indexOf(o.status) >= 0) return { restaurant: L(o.status === 'delivered' ? 'jrHanded' : 'jrEnded'), courier: o.status === 'delivered' && o.driver ? L('jcDelivered') : null, ended: o.status, stale: stale };
      var rest = { pending: 'jrPending', preparing: 'jrPreparing', ready: 'jrReady', pickedup: 'jrHanded' }[o.status] || 'jrPending';
      var cour = o.status === 'pending' ? null : o.driver ? (stale ? 'jcAssignedEarlier' : o.status === 'pickedup' ? 'jcOnWay' : 'jcAssigned') : (stale ? 'jcNoUpdate' : 'jcSearching');
      return { restaurant: L(rest), courier: cour ? L(cour) : null, ended: null, stale: stale };
    },
    /* C-6 (31 Oct): how an order is paid, from the stored order values only (no new calculation of prices, fees or
       settlement). total = order total (server); wallet = amount the server took from the customer's wallet; rest = what is
       left for the order's payment method (cash to the courier when the method is cash — same rule as the driver's due()).
       -> { total, wallet, rest, method: 'cash'|'card'|'apple'|'wallet'|…, restCash: bool, mixed: bool, points } */
    paymentParts: function (o) {
      if (!o) return null;
      var r2 = function (v) { return Math.round((+v || 0) * 100) / 100; }, total = r2(o.total), wallet = Math.min(total, Math.max(0, r2(o.walletUsed)));
      var rest = r2(Math.max(0, total - wallet)), method = o.payment || (rest === 0 && wallet > 0 ? 'wallet' : '');
      return { total: total, wallet: wallet, rest: rest, method: method, restCash: rest > 0 && /^(cash|Cash|Наличн)/.test(method), mixed: wallet > 0 && rest > 0, points: r2(o.pointsValue) };
    },
    /* C-5 (27 Oct): public link of a store = the customer app next to the current page + ?store=<uuid>. Only the store id
       is carried: no query, hash, session, token or account data of the current page. base (optional) = the customer app
       URL to use instead (e.g. the published one). -> string, or null for an invalid id / base. */
    storeLink: function (storeId, base) {
      var id = String(storeId || '').toLowerCase();
      if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(id)) return null;
      var u; try { u = new URL(base || 'customer.html', location.href); } catch (e) { return null; }
      if (!/^https?:$|^file:$/.test(u.protocol) || u.username || u.password) return null;
      u.search = ''; u.hash = ''; u.searchParams.set('store', id); return u.href;
    },
    /* QR of any text (the store link) as an SVG string. Generator loaded on first use from the pinned npm package
       qrcode-generator@1.4.4 (MIT) on jsDelivr with Subresource Integrity; runs in the browser, no paid service.
       -> Promise<string svg> (rejects if the library cannot load). */
    qrSvg: function (text, cell) { return loadQr().then(function (qrcode) { var q = qrcode(0, 'M'); q.addData(String(text)); q.make(); return q.createSvgTag({ cellSize: cell || 6, margin: 4 }); }); },
    orders: function (fn) { return ORD.filter(function (o) { return !o._x && (!fn || fn(o)); }); },
    /* admin search over ALL orders (patch 35, server side, same permission as the orders list). Falls back to the loaded orders. */
    searchOrders: function (q, status) {
      q = String(q || '').trim().slice(0, 60); if (!q || !sb) return Promise.resolve({ ids: [] });
      return sb.rpc('admin_search_orders', { p_q: q, p_status: status || null, p_limit: 100 }).then(function (r) {
        if (r.error) return { error: errKey(r.error), missing: /admin_search_orders|function|schema cache/i.test(String(r.error.message || '')) };
        var ids = (r.data || []).map(function (x) { return x.id; }); if (!ids.length) return { ids: [] };
        var need = ids.filter(function (id) { return !DB.orders.some(function (o) { return o.id === id; }); });
        return Promise.all([need.length ? sb.from('orders').select('*').in('id', need) : Promise.resolve({ data: [] }), need.length ? sb.from('order_items').select('*').in('order_id', need) : Promise.resolve({ data: [] })]).then(function (x) {
          if (!x[0].error) DB.xorders = (x[0].data || []).concat(DB.xorders.filter(function (o) { return need.indexOf(o.id) < 0; })).slice(0, 300);
          if (!x[1].error) DB.xitems = (x[1].data || []).concat(DB.xitems.filter(function (i) { return need.indexOf(i.order_id) < 0; }));
          return fetchAdminContacts(ids).then(function () { ORD = shape(); return { ids: ids }; });
        });
      }, function () { return { error: 'generic' }; });
    },
    /* staff: bring orders that are not among the loaded newest ones (opened from a customer card, a rating, a ticket, a search) */
    fetchOrders: function (ids) {
      ids = (ids || []).filter(function (id) { return id != null && !ORD.some(function (o) { return o.id == id; }); });
      if (!ids.length || !sb) return Promise.resolve(true);
      return Promise.all([sb.from('orders').select('*').in('id', ids), sb.from('order_items').select('*').in('order_id', ids)]).then(function (x) {
        if (x[0].error) return false;
        var got = (x[0].data || []).filter(function (o) { return ids.some(function (id) { return o.id == id; }); });
        if (!got.length) return false;
        var gid = got.map(function (o) { return o.id; });
        DB.xorders = got.concat(DB.xorders.filter(function (o) { return gid.indexOf(o.id) < 0; })).slice(0, 300);
        if (!x[1].error) DB.xitems = (x[1].data || []).filter(function (i) { return gid.indexOf(i.order_id) >= 0; }).concat(DB.xitems.filter(function (i) { return gid.indexOf(i.order_id) < 0; }));
        return (ME && ME.role === 'admin' ? fetchAdminContacts(gid) : Promise.resolve()).then(function () { ORD = shape(); fireSoon(); return true; });
      }, function () { return false; });
    },
    offers: function () {
      return DB.myOffers.map(function (f) {
        var o = ORD.filter(function (x) { return x.id === f.order_id; })[0]; if (!o) return null;
        return Object.assign({}, o, { offer: { mode: f.mode, rank: f.rank, dist: f.dist, left: Math.max(0, f.secs - (Date.now() - f.got) / 1000) } });
      }).filter(Boolean);
    },
    decline: function (id) { return sb.rpc('driver_decline', { p_id: id }).then(function (r) { return refresh().then(function () { return r.error ? { error: errKey(r.error) } : { ok: true }; }); }); },
    /* Server-owned navigation policy and normalized routes; no provider key or policy stored in this client. */
    navigation: function (body, signal) {
      if (!sb.functions || !sb.functions.invoke) return Promise.resolve({ mode: 'tracking', reason: 'service_unavailable' });
      var ctl = new AbortController(), timer, onAbort = function () { ctl.abort(); };
      if (signal) { if (signal.aborted) ctl.abort(); else signal.addEventListener('abort', onAbort, { once: true }); }
      return Promise.race([
        sb.functions.invoke('route', { body: body, signal: ctl.signal }).then(function (r) {
          return r && !r.error && r.data ? r.data : { mode: 'tracking', reason: 'service_unavailable' };
        }, function () { return { mode: 'tracking', reason: 'service_unavailable' }; }),
        new Promise(function (res) { timer = setTimeout(function () { ctl.abort(); res({ mode: 'tracking', reason: 'timeout' }); }, 8000); })
      ]).then(function (r) { clearTimeout(timer); if (signal) signal.removeEventListener('abort', onAbort); return r; });
    },
    route: function (from, to) {
      return TLB.navigation({ from: from, to: to }).then(function (d) {
        if (d.mode !== 'internal' || !Array.isArray(d.coords) || d.coords.length < 2 || !Number.isFinite(d.distance_m) || !Number.isFinite(d.duration_s)) return null;
        return { coords: d.coords, steps: d.steps || [], distanceM: d.distance_m, durationS: d.duration_s,
          source: d.source || '', attribution: d.attribution || '', at: d.calculated_at };
      });
    },
    /* C (prepared for review, needs the proposed SQL function order_courier_position): the last courier position of MY
       order, only while it is out for delivery. Result {lat, lng, acc, at(ms)} or null (not allowed / not on the way / none). */
    courierPosition: function (orderId, signal) {
      var request = sb.rpc('order_courier_position', { p_order: orderId });
      if (signal && typeof request.abortSignal === 'function') request = request.abortSignal(signal);
      return request.then(function (r) {
        var d = r && !r.error && (Array.isArray(r.data) ? r.data[0] : r.data);
        if (!d || d.lat == null || d.lng == null) return null;
        return { lat: +d.lat, lng: +d.lng, acc: d.acc == null ? null : +d.acc, at: d.updated_at ? new Date(d.updated_at).getTime() : null };
      }, function () { return null; });
    },
    sendLocation: function (lat, lng, acc) { if (isNaN(num(lat)) || isNaN(num(lng))) return Promise.resolve({ ok: false }); return sb.rpc('driver_location', { p_lat: num(lat), p_lng: num(lng), p_acc: isNaN(num(acc)) ? null : num(acc) }).then(function (r) { return { ok: !r.error }; }, function () { return { ok: false }; }); },
    assignDriver: function (orderId, driverId) { return rpc('admin_assign_driver', { p_order: orderId, p_driver: driverId }, true); },
    allOffers: function () { return DB.offersAll; },
    ratings: function () { return DB.ratings; },
    resolveRating: function (orderId, note) { return rpc('resolve_rating', { p_order: orderId, p_note: String(note || '').slice(0, 300) }, true); },
    reopenRating: function (orderId) { return rpc('reopen_rating', { p_order: orderId }, true); },
    lowRatings: function (maxStars, includeHandled) {
      var m = maxStars || 2;
      return DB.ratings.filter(function (r) { return ((r.store_stars != null && r.store_stars <= m) || (r.driver_stars != null && r.driver_stars <= m)) && (includeHandled || !r.handled_at); });
    },
    ratingOf: function (orderId) { return DB.ratings.filter(function (x) { return x.order_id === orderId; })[0] || null; },
    rateOrder: function (orderId, store, driver, comment) {
      var ok = function (v) { return v == null || (v >= 1 && v <= 5 && Math.floor(v) === v); };
      if (!ok(store) || !ok(driver) || (store == null && driver == null)) return Promise.resolve({ error: 'bad_value' });
      return rpc('rate_order', { p_order: orderId, p_store: store == null ? null : store, p_driver: driver == null ? null : driver, p_comment: String(comment || '').slice(0, 300) }, true);
    },
    uploadImage: function (file, o) {
      o = o || {};
      return new Promise(function (resolve) {
        if (!file || !/^image\//.test(file.type || '') || file.size > 12 * 1024 * 1024) { toast(t('err_bad_value'), true); return resolve(null); }
        var fr = new FileReader();
        fr.onerror = function () { toast(t('err_generic'), true); resolve(null); };
        fr.onload = function () {
          var im = new Image();
          im.onerror = function () { toast(t('err_bad_value'), true); resolve(null); };
          im.onload = function () {
            var max = o.maxW || 800, k = Math.min(1, max / Math.max(im.width, im.height)), c = document.createElement('canvas');
            c.width = Math.max(1, Math.round(im.width * k)); c.height = Math.max(1, Math.round(im.height * k));
            c.getContext('2d').drawImage(im, 0, 0, c.width, c.height);
            var q = o.q || 0.78, inline = function () { resolve(c.toDataURL('image/jpeg', q)); };
            if (!c.toBlob || !sb || !sb.storage || !ME) return inline();
            c.toBlob(function (blob) {
              if (!blob) return inline();
              var id = (window.crypto && crypto.randomUUID) ? crypto.randomUUID() : (Date.now().toString(36) + Math.random().toString(36).slice(2, 10));
              var path = ME.id + '/' + id + '.jpg';
              sb.storage.from('media').upload(path, blob, { contentType: 'image/jpeg', cacheControl: '31536000', upsert: false }).then(function (r) {
                if (r.error) { console.error(r.error); return inline(); }                    // storage not set up yet: keep working with an inline image
                resolve(sb.storage.from('media').getPublicUrl(path).data.publicUrl);
              }, function () { inline(); });
            }, 'image/jpeg', q);
          };
          im.src = fr.result;
        };
        fr.readAsDataURL(file);
      });
    },
    reportError: reportError,
    loadOrderExtra: function (id) {
      if (!ME || !sb || (extraLoaded[id] && Date.now() - extraLoaded[id] < 15000)) return Promise.resolve();
      extraLoaded[id] = Date.now(); extraOrders[id] = 1;
      if (ME.role === 'admin') fetchAdminContacts([id]).then(function (c) { if (c) { ORD = shape(); fireSoon(); } });
      return Promise.all([sb.from('order_chat').select('*').eq('order_id', id).order('created_at'), sb.from('order_events').select('*').eq('order_id', id).order('at')]).then(function (r) {
        var seen = {}; DB.chat.forEach(function (c) { seen[c.id] = 1; });
        (r[0].error ? [] : (r[0].data || [])).forEach(function (c) { if (!seen[c.id]) { DB.chat.push(c); seen[c.id] = 1; } });
        DB.events = DB.events.filter(function (e) { return e.order_id !== id; }).concat(r[1].error ? [] : (r[1].data || []));
        ORD = shape(); fireSoon();
      }).catch(function (e) { console.error(e); });
    },
    /* ---------- About / Privacy pages (edited by the admin) ---------- */
    pages: function () { return DB.pages; },
    /* 'loading' until the first answer; 'ok'; 'empty' = the table has no rows (set_page can only update existing rows); 'error' */
    pagesState: function () { return pagesSt; },
    loadPages: function (force) {
      var now = Date.now();
      if (!force && extraLoaded.pages && now - extraLoaded.pages < 30000) return Promise.resolve(false);
      extraLoaded.pages = now;
      var st0 = pagesSt;
      return sb.from('app_pages').select('slug,body_ru,body_en').then(function (r) {
        if (r.error) { pagesSt = 'error'; pagesErr = String(r.error.message || r.error.code || ''); if (st0 !== 'error') fireSoon(); return false; }
        var o = {}; (r.data || []).forEach(function (p) { o[p.slug] = { ru: p.body_ru || '', en: p.body_en || '' }; });
        pagesSt = Object.keys(o).length ? 'ok' : 'empty';
        if (JSON.stringify(o) === JSON.stringify(DB.pages) && st0 === pagesSt) return false;
        DB.pages = o; fireSoon(); return true;
      }, function (e) { pagesSt = 'error'; pagesErr = String((e && e.message) || e || ''); fireSoon(); return false; });
    },
    pagesError: function () { return pagesErr; },
    setPage: function (slug, lang, body) {
      var b = String(body == null ? '' : body);
      if (['about', 'privacy'].indexOf(slug) < 0 || ['ru', 'en'].indexOf(lang) < 0 || b.length > 20000) return Promise.resolve({ error: 'bad_value' });
      return rpc('set_page', { p_slug: slug, p_lang: lang, p_body: b }, true).then(function (r) { return r && r.error ? r : TLBref.loadPages(true).then(function () { return { ok: true }; }); });
    },
    refundRoom: function (ticketId) {
      return sb.rpc('ticket_refund_room', { p_ticket: ticketId }).then(function (r) {
        if (r.error || !r.data || !r.data.length) return null;
        var x = r.data[0]; return { total: +x.order_total, refunded: +x.refunded, room: +x.room };
      }, function () { return null; });
    },
    setCustomerPhone: function (userId, phone, reason) {
      var ph = normPhone(phone), why = String(reason || '').trim();
      if (!ph) return Promise.resolve({ error: 'bad_phone' });
      if (why.length < 3 || why.length > 200) return Promise.resolve({ error: 'note_required' });
      return rpc('admin_set_customer_phone', { p_user: userId, p_phone: ph, p_reason: why }, true).then(function (r) { return r && r.error ? r : { ok: true, phone: ph }; });
    },
    ownerInfo: function (storeId) { return sb.rpc('store_owner_info', { p_store: storeId }).then(function (r) { return r.error || !r.data || !r.data.length ? null : r.data[0]; }, function () { return null; }); },
    contactsOf: function (id) { return DB.contacts[id] || {}; },
    settings: function () { return DB.settings; },
    setSetting: function (key, value) { return rpc('set_setting', { p_key: key, p_value: +value }, true).then(function (r) { return r && r.error ? r : refresh(['misc']).then(function () { return { ok: true }; }); }); },
    myRating: function () { return DB.myRating; },
    /* ---------- support (customer) ---------- */
    wantSupport: function (hold) { if (hold) tixHold = true; if (!wantTix || hold) { wantTix = true; refresh(['misc']); } },
    supportInfo: function () { return { phone: DB.texts.support_phone || '', hours: DB.texts.support_hours || '' }; },
    tickets: function () { return DB.tickets.map(function (t) { return Object.assign({}, t, { unread: !!t.last_staff_at && Date.parse(t.last_staff_at) > Date.parse(t.customer_seen_at || 0) }); }); },
    ticketUnread: function () { return DB.tickets.filter(function (t) { return t.last_staff_at && Date.parse(t.last_staff_at) > Date.parse(t.customer_seen_at || 0); }).length; },
    ticketMessages: function (id) { return (DB.tmsgs[id] || []).slice(); },
    loadTicket: function (id, force) {
      var now = Date.now(), c = extraLoaded['t' + id];
      if (!force && c && now - c < 6000) return Promise.resolve(false);
      extraLoaded['t' + id] = now;
      return sb.from('ticket_messages').select('*').eq('ticket_id', id).order('created_at').limit(200).then(function (r) {
        if (r.error) return false;
        var k = JSON.stringify(r.data || []); if (JSON.stringify(DB.tmsgs[id] || []) === k) return false;
        DB.tmsgs[id] = r.data || []; fireSoon(); return true;
      }, function () { return false; });
    },
    ticketSeen: function (id) { return sb.rpc('ticket_seen', { p_ticket: id }).then(function () { return refresh(['misc']); }, function () { }); },
    createTicket: function (orderId, reason, message) {
      var m = String(message || '').trim();
      if (!m && reason !== 'other') m = String(t('rs_' + reason) || reason);      // no message typed: the first line of the conversation is the chosen reason
      if (['not_delivered', 'wrong_order', 'missing_items', 'quality', 'late', 'courier', 'restaurant', 'payment', 'other'].indexOf(reason) < 0 || m.length < (reason === 'other' ? 5 : 1) || m.length > 500) return Promise.resolve({ error: 'bad_value' });
      return sb.rpc('create_ticket', { p_order: orderId == null ? null : orderId, p_reason: reason, p_message: m }).then(function (r) {
        if (r.error) { console.error(r.error); return { error: errKey(r.error) }; }
        return refresh(['misc']).then(function () { return { id: r.data }; });
      }, function () { return { error: 'generic' }; });
    },
    ticketReply: function (id, body) {
      var m = String(body || '').trim(); if (!m || m.length > 500) return Promise.resolve({ error: 'bad_value' });
      return sb.rpc('ticket_reply', { p_ticket: id, p_body: m }).then(function (r) {
        if (r.error) { console.error(r.error); return { error: errKey(r.error) }; }
        extraLoaded['t' + id] = 0; return Promise.all([refresh(['misc']), TLBref.loadTicket(id, true)]).then(function () { return { ok: true }; });
      }, function () { return { error: 'generic' }; });
    },
    /* ---------- support (admin) ---------- */
    person: function (id) { return DB.people[id] || { name: '', phone: '' }; },
    adminTickets: function () { return DB.tickets.slice(); },
    ticketStaffReply: function (id, body) {
      var m = String(body || '').trim(); if (!m || m.length > 500) return Promise.resolve({ error: 'bad_value' });
      return sb.rpc('ticket_staff_reply', { p_ticket: id, p_body: m }).then(function (r) {
        if (r.error) { console.error(r.error); return { error: errKey(r.error) }; }
        extraLoaded['t' + id] = 0; return Promise.all([refresh(['misc']), TLBref.loadTicket(id, true)]).then(function () { return { ok: true }; });
      }, function () { return { error: 'generic' }; });
    },
    ticketSetStatus: function (id, status, note, refund) {
      var rf = refund === '' || refund == null ? null : num(refund);
      if (['open', 'in_progress', 'resolved', 'rejected'].indexOf(status) < 0 || (rf !== null && (isNaN(rf) || rf < 0))) return Promise.resolve({ error: 'bad_value' });
      if (status === 'rejected' && String(note || '').trim().length < 3) return Promise.resolve({ error: 'note_required' });
      return sb.rpc('ticket_set_status', { p_ticket: id, p_status: status, p_note: String(note || '').slice(0, 300), p_refund: rf }).then(function (r) {
        if (r.error) { console.error(r.error); return { error: errKey(r.error) }; }
        return refresh(['misc']).then(function () { return { ok: true }; });
      }, function () { return { error: 'generic' }; });
    },
    setText: function (key, value) { return rpc('set_text_setting', { p_key: key, p_value: String(value || '').slice(0, 60) }, true).then(function (r) { return r && r.error ? r : refresh(['misc']).then(function () { return { ok: true }; }); }); },
    /* ---------- another restaurant (owner) ---------- */
    myStoreRequests: function () { return DB.sreqs.filter(function (q) { return q.user_id === ME.id; }); },
    storeRequests: function () { return DB.sreqs.slice(); },
    requestStore: function (f) {
      var ph = normPhone(f.phone), name = String(f.name || '').replace(/\s+/g, ' ').trim(), lat = num(f.lat), lng = num(f.lng);
      if (name.length < 2 || name.length > 80 || ['rest', 'grocery', 'pharmacy', 'beauty', 'flowers', 'gifts', 'shops', 'sweets'].indexOf(f.category) < 0) return Promise.resolve({ error: 'bad_value' });
      if (!ph) return Promise.resolve({ error: 'bad_phone' });
      if (isNaN(lat) || isNaN(lng) || lat < -90 || lat > 90 || lng < -180 || lng > 180) return Promise.resolve({ error: 'bad_value' });
      return sb.rpc('request_store', { p_name: name, p_category: f.category, p_phone: ph, p_address: String(f.address || '').trim().slice(0, 200), p_lat: lat, p_lng: lng, p_note: String(f.note || '').trim().slice(0, 500) }).then(function (r) {
        if (r.error) { console.error(r.error); return { error: errKey(r.error) }; }
        return refresh(['misc']).then(function () { return { ok: true, id: r.data }; });
      }, function () { return { error: 'generic' }; });
    },
    decideStoreRequest: function (id, approve, note) {
      if (!approve && String(note || '').trim().length < 3) return Promise.resolve({ error: 'note_required' });
      return sb.rpc('decide_store_request', { p_id: id, p_approve: !!approve, p_note: String(note || '').slice(0, 300) }).then(function (r) {
        if (r.error) { console.error(r.error); return { error: errKey(r.error) }; }
        sigs = {}; return refresh().then(function () { return { ok: true, store: r.data }; });
      }, function () { return { error: 'generic' }; });
    },
    /* restaurant requests from the public partner page (patch 36): status by 'stores' staff, link to a store by the admin */
    leadDecide: function (id, action, arg) {
      var p = action === 'link' ? sb.rpc('lead_link', { p_id: id, p_store: arg }) :
        (action === 'contacted' || action === 'rejected') ? sb.rpc('lead_set_status', { p_id: id, p_status: action, p_note: String(arg || '').trim().slice(0, 300) }) : null;
      if (!p) return Promise.resolve({ error: 'bad_value' });
      if (action === 'rejected' && String(arg || '').trim().length < 3) return Promise.resolve({ error: 'note_required' });
      return p.then(function (r) { if (r.error) { console.error(r.error); return { error: errKey(r.error) }; } return refresh(['misc']).then(function () { return { ok: true }; }); },
        function () { return { error: 'generic' }; });
    },
    /* ---------- customers (admin) ---------- */
    customers: function (q, offset) {
      return sb.rpc('admin_customers', { p_q: String(q || '').trim().slice(0, 60) || null, p_limit: 30, p_offset: Math.max(0, Math.floor(+offset || 0)) }).then(function (r) { return r.error ? { error: errKey(r.error), rows: [] } : { rows: r.data || [] }; }, function () { return { error: 'generic', rows: [] }; });
    },
    /* one account's orders (by customer id, newest first), 50 at a time; .total = how many this account has in all (null if unknown) */
    customerOrders: function (id, from) {
      from = Math.max(0, Math.floor(+from || 0));
      return sb.from('orders').select('id,store_id,status,total,created_at', { count: 'exact' }).eq('customer_id', id).order('created_at', { ascending: false }).order('id', { ascending: false }).range(from, from + 49).then(function (r) {
        var a = (r.data || []).map(function (o) { return { id: o.id, store: storeName(o.store_id), status: o.status, total: +o.total, createdAt: Date.parse(o.created_at) }; });
        a.total = typeof r.count === 'number' ? r.count : null; a.failed = !!r.error; return a;
      }, function () { var a = []; a.total = null; a.failed = true; return a; });
    },
    setBan: function (id, banned, reason) {
      if (banned && String(reason || '').trim().length < 3) return Promise.resolve({ error: 'note_required' });
      return rpc('set_customer_ban', { p_id: id, p_banned: !!banned, p_reason: String(reason || '').slice(0, 200) }, true);
    },
    /* ---------- wallet ---------- */
    wallet: function () { return DB.wallet; },
    /* loyalty (patch 29): summary {balance, next_exp_at, next_exp_pts, earn_per_tjs, points_per_tjs, min_redeem, expiry_days, cashback_pct} */
    loyalty: function () { return DB.loyalty; },
    points: function () { return DB.pts; },
    /* each call is numbered: a reply that arrives after a newer call was started is ignored (never overwrites newer data) */
    loadPoints: function () {
      var n = ++ptsSeq;
      return sb.from('loyalty_ledger').select('*').eq('user_id', ME.id).order('created_at', { ascending: false }).limit(60).then(function (r) {
        if (n !== ptsSeq || r.error) return null;   // null = not applied (failed or superseded); true / false = applied, changed or not
        var nu = (r.data || []).map(function (e) { return { id: e.id, points: +e.points, kind: e.kind, orderId: e.order_id, at: Date.parse(e.created_at) }; });
        var ch = JSON.stringify(nu) !== JSON.stringify(DB.pts); DB.pts = nu; if (ch) fire(); return ch;
      }, function () { return null; });
    },
    /* UAT008 / 009: the points history and the points balance read as ONE consistent pair: ledger → balance → ledger again; when both
       ledger reads end at the same newest row, no movement was written in between, so the balance belongs to exactly those rows.
       Otherwise read again (at most 3 rounds). Each call is numbered: a reply that arrives after a newer call (or after pointsAbandon)
       is ignored. Resolves {rows, balance, consistent} or null (failed / superseded). */
    pointsSnapshot: function () {
      var n = ++ptsSeq, lg = function () { return sb.from('loyalty_ledger').select('*').eq('user_id', ME.id).order('id', { ascending: false }).limit(60); };
      var top = function (r) { return r.data && r.data.length ? +r.data[0].id : 0; };
      function round(k) {
        var a; return lg().then(function (r1) { if (r1.error) throw r1.error; a = r1; return sb.rpc('loyalty_summary'); }).then(function (rs) {
          if (rs.error) throw rs.error; return lg().then(function (r2) {
            if (r2.error) throw r2.error;
            if (top(a) !== top(r2) && k < 2) return round(k + 1);
            return { rows: r2.data || [], sum: rs.data, consistent: top(a) === top(r2) };
          });
        });
      }
      return round(0).then(function (x) {
        if (n !== ptsSeq) return null;
        var nu = x.rows.map(function (e) { return { id: e.id, points: +e.points, kind: e.kind, orderId: e.order_id, at: Date.parse(e.created_at) }; });
        var ch = JSON.stringify(nu) !== JSON.stringify(DB.pts) || JSON.stringify(x.sum) !== JSON.stringify(DB.loyalty);
        DB.pts = nu; if (x.sum) DB.loyalty = x.sum; if (ch) fire();
        return { rows: nu, balance: x.sum ? +x.sum.balance || 0 : null, consistent: x.consistent && !!x.sum };
      }, function () { return null; });
    },
    pointsAbandon: function () { ptsSeq++; },
    happyHours: function () { return DB.hh; },
    /* best-selling dishes of the last 30 days [{item_id, store_id, cnt}] and real preparation speed per store {min, n} (patch 32) */
    bestDishes: function () { return DB.best; },
    speed: function (storeId) { return DB.speed[storeId] || null; },
    isExpress: function (storeId) { var s = DB.speed[storeId]; return !!(s && s.n >= 3 && s.min <= 15); },
    setMyCashback: function (storeN, pct) { var s = storeByName(storeN); if (!s) return badStore(); return rpc('set_my_cashback', { p_store: s.id, p_pct: +pct }, true); },
    setMyFreeDelivery: function (storeN, min) { var s = storeByName(storeN); if (!s) return badStore(); return rpc('set_my_free_delivery', { p_store: s.id, p_min: +min || 0 }, true); },
    setStoreEarn: function (storeId, v) { var e = String(v == null ? '' : v).trim() === '' ? null : +v; if (e !== null && (!isFinite(e) || e < 0 || e > 1000 || e !== Math.floor(e))) return Promise.resolve({ error: 'bad_value' }); return rpc('set_store_earn', { p_store: storeId, p_earn: e }, true); },
    setStoreFreeDelivery: function (storeId, min) { return rpc('set_store_free_delivery', { p_store: storeId, p_min: +min || 0 }, true); },
    /* group (office) orders (patch 33): everything goes through the group_* functions; they answer the whole group */
    groupCreate: function (storeN) { var s = storeByName(storeN); if (!s) return Promise.resolve({ error: 'store_unavailable' }); return sb.rpc('group_create', { p_store: s.id }).then(grp); },
    groupGet: function (id) { if (!UUID.test(String(id))) return Promise.resolve({ error: 'bad_group' }); return sb.rpc('group_get', { p_id: id }).then(grp); },
    groupAdd: function (id, itemId, qty, opts, note) { return sb.rpc('group_add', { p_id: id, p_item: itemId, p_qty: Math.max(1, Math.min(20, Math.floor(+qty || 1))), p_options: opts || [], p_note: note ? String(note).slice(0, 120) : null }).then(grp); },
    groupRemove: function (line) { return sb.rpc('group_remove', { p_line: +line }).then(grp); },
    groupSet: function (id, status) { return sb.rpc('group_set', { p_id: id, p_status: status }).then(grp); },
    setStoreLoyalty: function (storeId, minOrder, cashback) { return rpc('set_store_loyalty', { p_store: storeId, p_min_order: minOrder === '' || minOrder == null ? null : +minOrder, p_cashback: cashback === '' || cashback == null ? null : +cashback }, true); },
    /* best happy-hour % for a store now (Dushanbe = UTC+5, no daylight saving) — same rule as happy_hour_pct() in SQL */
    hhPct: function (storeId, at) {
      var best = 0; hhOnNow(at).forEach(function (h) { if ((!h.store_id || h.store_id === storeId) && +h.discount_pct > best) best = +h.discount_pct; }); return best;
    },
    hhActive: function (at) { return hhOnNow(at); },
    /* when the current happy hour of a store ends (ms): the latest end among the windows running now (Dushanbe = UTC+5) */
    hhEnd: function (storeId, at) {
      var now = at || Date.now(), best = null;
      hhOnNow(now).forEach(function (h) {
        if (h.store_id && h.store_id !== storeId) return;
        var p = String(h.end_time || '0:0').split(':'), d = new Date(now + 5 * 3600000);
        var end = Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate(), +p[0] || 0, +p[1] || 0, +p[2] || 0) - 5 * 3600000;
        if (end <= now) end += 86400000;                                   // ends tomorrow (window past midnight)
        if (best == null || end > best) best = end;
      });
      return best;
    },
    saveHH: function (f) {
      var days = (f.days || []).map(Number).filter(function (d) { return d >= 1 && d <= 7; }), pct = Math.floor(+f.pct), title = String(f.title || '').trim();
      if (!title || title.length > 60 || !days.length || !(pct >= 1 && pct <= 90) || !/^\d{2}:\d{2}$/.test(f.start || '') || !/^\d{2}:\d{2}$/.test(f.end || '') || f.start === f.end) return badStore();
      var row = { title: title, store_id: f.store || null, days: days, start_time: f.start, end_time: f.end, discount_pct: pct, active: f.active !== false };
      var q = f.id ? sb.from('happy_hours').update(row).eq('id', f.id) : sb.from('happy_hours').insert(row);
      return q.then(function (r) { return r.error ? done(r) : refresh(['misc']).then(function () { toast(t('saved')); return { ok: true }; }); });
    },
    setHHActive: function (id, on) { return sb.from('happy_hours').update({ active: !!on }).eq('id', id).then(function (r) { return r.error ? done(r) : refresh(['misc']).then(function () { return { ok: true }; }); }); },
    deleteHH: function (id) { return sb.from('happy_hours').delete().eq('id', id).then(function (r) { return r.error ? done(r) : refresh(['misc']).then(function () { return { ok: true }; }); }); },
    loadWallet: function (force) {
      var now = Date.now(), k = 'wallet';
      if (!force && extraLoaded[k] && now - extraLoaded[k] < 6000) return Promise.resolve(false);
      extraLoaded[k] = now;
      return Promise.all([sb.from('wallet_entries').select('*').eq('user_id', ME.id).order('created_at', { ascending: false }).limit(60), sb.rpc('wallet_balance')]).then(function (r) {
        if (r[0].error) return null;   // null = not loaded (error); true / false = loaded, changed or not
        var key = JSON.stringify(r[0].data || []); var ch = JSON.stringify(DB.wallet.entries) !== key;
        DB.wallet.entries = (r[0].data || []).map(function (e) { return { id: e.id, amount: +e.amount, kind: e.kind, orderId: e.order_id, ticketId: e.ticket_id, note: e.note || '', at: Date.parse(e.created_at) }; });
        if (!r[1].error && r[1].data != null) DB.wallet.balance = Math.round(+r[1].data * 100) / 100;
        DB.wallet.loadedAt = Date.now(); if (ch) fireSoon(); return ch;
      }, function () { return null; });
    },
    walletOf: function (userId) {
      return Promise.all([sb.rpc('wallet_balance', { p_user: userId }), sb.from('wallet_entries').select('*').eq('user_id', userId).order('created_at', { ascending: false }).limit(30)]).then(function (r) {
        return { balance: r[0].error ? 0 : Math.round(+r[0].data * 100) / 100, entries: r[1].error ? [] : (r[1].data || []).map(function (e) { return { id: e.id, amount: +e.amount, kind: e.kind, orderId: e.order_id, ticketId: e.ticket_id, note: e.note || '', at: Date.parse(e.created_at) }; }) };
      }, function () { return { balance: 0, entries: [] }; });
    },
    walletAdjust: function (userId, amount, note) {
      var a = num(amount), n = String(note || '').trim();
      if (isNaN(a) || a === 0 || Math.abs(a) > 100000 || n.length < 3 || n.length > 200) return Promise.resolve({ error: 'bad_value' });
      return rpc('wallet_adjust', { p_user: userId, p_amount: Math.round(a * 100) / 100, p_note: n }, true);
    },
    audit: function (limit) {
      return sb.from('audit_log').select('*').order('at', { ascending: false }).limit(Math.min(200, limit || 100)).then(function (r) { return r.error ? [] : (r.data || []); });
    },
    clientErrors: function (limit) {
      return sb.from('client_errors').select('*').order('at', { ascending: false }).limit(Math.min(200, limit || 100)).then(function (r) { return r.error ? [] : (r.data || []); });
    },
    mapView: function (elId, points, center) {
      loadLeaflet(function () {
        var box = $(elId); if (!box) return;
        var map = L.map(elId).setView(center || [38.5598, 68.787], 12);
        L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '© OpenStreetMap', referrerPolicy: 'strict-origin-when-cross-origin' }).addTo(map);
        var group = [];
        (points || []).forEach(function (p) {
          if (!isFinite(+p.lat) || !isFinite(+p.lng)) return;
          var m = L.circleMarker([+p.lat, +p.lng], { radius: p.kind === 'store' ? 8 : 10, color: '#fff', weight: 2, fillColor: p.kind === 'store' ? (p.open ? '#1fa05a' : '#8b8f98') : (p.busy ? '#f59e0b' : '#f1511b'), fillOpacity: 1 }).addTo(map);
          var tip = document.createElement('div'); tip.textContent = String(p.label || ''); m.bindTooltip(tip, { permanent: true, direction: 'top', offset: [0, -6] });
          group.push([+p.lat, +p.lng]);
        });
        if (group.length) map.fitBounds(group, { padding: [30, 30], maxZoom: 15 });
        setTimeout(function () { map.invalidateSize(); }, 150);
      });
    },
    events: function (id) { return DB.events.filter(function (e) { return e.order_id == id; }); },
    cash: function (driverId) { return DB.cash[driverId] || 0; },
    myCash: function () { return ME ? (DB.cash[ME.id] || 0) : 0; },
    placeOrder: function (o) {
      var s = storeByName(o.store); if (!s) return Promise.resolve({ error: 'store_unavailable' });
      var items = linesOf(o.lines || o.cart, o.notes);
      if (!items) return Promise.resolve({ error: 'bad_value' });
      if (o.wallet != null && (isNaN(num(o.wallet)) || num(o.wallet) < 0 || num(o.wallet) > 1000000)) return Promise.resolve({ error: 'bad_value' });
      if (o.lat != null && (!(num(o.lat) >= -90 && num(o.lat) <= 90) || !(num(o.lng) >= -180 && num(o.lng) <= 180))) return Promise.resolve({ error: 'bad_value' });
      return rpc('place_order', { p_store: s.id, p_items: items, p_tip: o.tip || 0, p_payment: o.payment || '', p_address: String(o.address || '').slice(0, 200), p_lat: isNaN(num(o.lat)) ? null : num(o.lat), p_lng: isNaN(num(o.lng)) ? null : num(o.lng), p_promo: (o.promo && /^[A-Za-z0-9_-]{3,20}$/.test(o.promo)) ? o.promo : null, p_key: (o.key && /^[A-Za-z0-9_-]{8,64}$/.test(o.key)) ? o.key : null, p_fee: isNaN(num(o.fee)) ? null : num(o.fee), p_wallet: (isNaN(num(o.wallet)) || num(o.wallet) <= 0) ? null : Math.round(num(o.wallet) * 100) / 100, p_points: (o.points > 0 && o.points <= 100000000) ? Math.floor(o.points) : null, p_extra: o.extra || null })
        .then(function (r) { return r.error ? r : { id: r.data }; });
    },
    checkPromo: function (storeN, cart, code) {
      var s = storeByName(storeN), k = String(code || '').trim();
      if (!s || !/^[A-Za-z0-9_-]{3,20}$/.test(k)) return Promise.resolve({ error: 'promo_invalid' });
      var items = linesOf(cart, null);
      if (!items) return Promise.resolve({ error: 'promo_invalid' });
      return sb.rpc('check_promo', { p_code: k, p_store: s.id, p_items: items }).then(function (r) {
        if (r.error) return { error: errKey(r.error) };
        var d = r.data || {};
        return d.ok ? { discount: +d.discount, base: +d.base || 0 } : { error: errKey({ message: d.error }), min: +d.min || 0, have: +d.have || 0 };
      });
    },
    setStatus: function (id, to) { return rpc('set_order_status', { p_id: id, p_to: to }); },
    patch: function (id, f) { return rpc('set_prep_time', { p_id: id, p_min: f.prepTime }, true); },
    driverAccept: function (id) { return rpc('driver_accept', { p_id: id }).then(function (r) { return r.error ? r : (r.data === true ? { ok: true } : { error: 'taken' }); }); },
    deliver: function (id, cash, note, photo) { var a = { p_id: id, p_cash: cash, p_note: note || null }; if (photo) a.p_photo = photo; return rpc('deliver_order', a); },
    /* batch 2 (patch 34): courier arrival steps, photo proof (private bucket), restaurant cancel with a reason */
    driverArrived: function (id, where) { if (where !== 'store' && where !== 'customer') return Promise.resolve({ error: 'bad_value' }); return rpc('driver_arrived', { p_id: id, p_where: where }); },
    rejectOrder: function (id, reason, note) { if (['out_of_stock', 'too_busy', 'closing', 'other'].indexOf(reason) < 0) return Promise.resolve({ error: 'bad_value' }); return rpc('reject_order', { p_id: id, p_reason: reason, p_note: note ? String(note).slice(0, 200) : null }); },
    uploadProof: function (file, orderId) {
      return new Promise(function (resolve) {
        if (!file || !/^image\//.test(file.type || '') || file.size > 25 * 1024 * 1024) return resolve({ error: 'bad_value' });
        var fr = new FileReader(); fr.onerror = function () { resolve({ error: 'generic' }); };
        fr.onload = function () {
          var im = new Image(); im.onerror = function () { resolve({ error: 'bad_value' }); };
          im.onload = function () {
            var k = Math.min(1, 1000 / Math.max(im.width, im.height)), c = document.createElement('canvas');
            c.width = Math.max(1, Math.round(im.width * k)); c.height = Math.max(1, Math.round(im.height * k)); c.getContext('2d').drawImage(im, 0, 0, c.width, c.height);
            var preview = c.toDataURL('image/jpeg', 0.6);
            if (!c.toBlob || !sb || !sb.storage || !ME) return resolve({ error: 'generic' });
            c.toBlob(function (blob) {
              if (!blob) return resolve({ error: 'generic' });
              var id = ((window.crypto && crypto.randomUUID) ? crypto.randomUUID() : (Date.now().toString(36) + Math.random().toString(36).slice(2, 12))).replace(/[^A-Za-z0-9_-]/g, '');
              var path = ME.id + '/' + orderId + '/' + id + '.jpg';
              sb.storage.from('proofs').upload(path, blob, { contentType: 'image/jpeg', upsert: false }).then(function (r) {
                resolve(r.error ? { error: 'photo_upload' } : { path: path, preview: preview });
              }, function () { resolve({ error: 'photo_upload' }); });
            }, 'image/jpeg', 0.72);
          };
          im.src = fr.result;
        };
        fr.readAsDataURL(file);
      });
    },
    /* v81 (from v60, read-only): the wallet records of one order (returns, refunds), paged by id; null = could not read */
    orderWallet: function (orderId) {
      var all = [], page = function (after, k) {
        var q = sb.from('wallet_entries').select('*').eq('order_id', orderId); if (after != null) q = q.gt('id', after);
        return q.order('id', { ascending: true }).limit(51).then(function (r) {
          if (r.error) return null; var rows = r.data || [], more = rows.length > 50; rows = rows.slice(0, 50);
          rows.forEach(function (e) { all.push({ id: e.id, amount: +e.amount, kind: e.kind, orderId: e.order_id, ticketId: e.ticket_id, note: e.note || '', at: Date.parse(e.created_at) }); });
          if (more && k < 40) return page(rows[rows.length - 1].id, k + 1);
          if (more) all.partial = true; return all;
        }, function () { return null; });
      };
      return page(null, 0);
    },
    proofUrl: function (path) { if (!path || !sb || !sb.storage) return Promise.resolve(null); return sb.storage.from('proofs').createSignedUrl(path, 3600).then(function (r) { return r && r.data ? r.data.signedUrl : null; }, function () { return null; }); },
    leaflet: function (cb) { loadLeaflet(cb); },
    chat: function (id, sender, text) { return sb.from('order_chat').insert({ order_id: id, sender_id: ME.id, body: String(text).slice(0, 200) }).then(doneQ); },

    addItem: function (storeN, f) { var s = storeByName(storeN); if (!s || !validItem(f)) return badStore(); return sb.from('menu_items').insert({ store_id: s.id, name: f.name, price: f.price, image_url: f.image || null, popular: !!f.popular, section: cleanSection(f.section), discount_pct: cleanPct(f.discount) }).then(done); },
    updateItem: function (id, f) { f = Object.assign({}, f); if (!validItem(f)) return badStore(); if ('image' in f) { f.image_url = f.image || null; delete f.image; } if ('discount_pct' in f) { var dp = +f.discount_pct; if (!isFinite(dp) || dp < 0 || dp > 100) return badStore(); f.discount_pct = Math.round(dp * 100) / 100; } if ('section' in f) { if (String(f.section == null ? '' : f.section).trim().length > 40) return badStore(); f.section = cleanSection(f.section); } return sb.from('menu_items').update(f).eq('id', id).then(done); },
    deleteItem: function (id) { return sb.from('menu_items').delete().eq('id', id).then(done); },
    approveItem: function (id) { return sb.from('menu_items').update({ approved: true }).eq('id', id).then(done); },

    addStore: function (f) { var c = cleanStore(f); if (!validStore(c)) return badStore(); return sb.from('stores').insert(c).then(done); },
    updateStore: function (id, f) { var c = cleanStore(f); if (!validStore(c)) return badStore(); return sb.from('stores').update(c).eq('id', id).then(done); },
    refreshRating: function (storeId) {
      return sb.functions.invoke('google-rating', { body: { store_id: String(storeId) } }).then(function (r) {
        if (r.error || !r.data || r.data.ok !== true) { toast(t('err_rating_fail'), true); return { error: 'rating_fail', toasted: true }; }
        toast(t('saved')); return refresh().then(function () { return { ok: true }; });
      }).catch(function () { toast(t('err_rating_fail'), true); return { error: 'rating_fail', toasted: true }; });
    },
    setMyDiscount: function (storeN, pct) { var s = storeByName(storeN), v = +pct; if (!s || !isFinite(v) || v < 0 || v > 100) return Promise.resolve({ error: 'bad_value' }); return rpc('set_my_discount', { p_store: String(s.id), p_pct: v }, true); },
    updateMyStore: function (storeN, f) { var s = storeByName(storeN); if (!s) return Promise.resolve({ error: 'generic' }); return rpc('update_my_store', { p_store: s.id, p_description: f.description == null ? null : f.description, p_cover: f.cover || null, p_logo: f.logo || null }, true); },
    perms: function () { return MYPERMS.slice(); },
    isSuper: function () { return !!ME && ME.role === 'admin'; },
    can: function (p) { return MYPERMS.indexOf(p) >= 0; },
    staffList: function () { return sb.rpc('staff_list').then(function (r) { return r.error ? { error: errKey(r.error), rows: [] } : { rows: r.data || [] }; }); },
    staffSet: function (email, perms, active) {
      email = String(email || '').trim().toLowerCase();
      var ok = /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email) && email.length <= 120 && Array.isArray(perms) && perms.every(function (x) { return ALL_PERMS.indexOf(x) >= 0; }) && (perms.length > 0 || active === false);
      if (!ok) return Promise.resolve({ error: 'bad_value' });
      return rpc('staff_set', { p_email: email, p_perms: perms, p_active: active !== false }, true);
    },
    brandRoute: function (brand, lat, lng, names) { return sb.rpc('brand_route', { p_brand: brand, p_lat: lat, p_lng: lng, p_names: names || null }).then(function (r) { return r.error ? [] : (r.data || []); }); },
    brandStats: function (brand, days) { return sb.rpc('brand_stats', { p_brand: brand, p_days: days || 30 }).then(function (r) { return r.error ? null : r.data; }); },
    brandCreate: function (name, ownerEmail) { name = String(name || '').trim(); if (name.length < 2 || name.length > 60) return Promise.resolve({ error: 'bad_value' }); return rpc('brand_create', { p_name: name, p_owner_email: ownerEmail || null }, true); },
    brandAttach: function (storeId, brandId, branch) { if (!/^[0-9a-f-]{36}$/i.test(String(brandId))) return Promise.resolve({ error: 'bad_value' }); return rpc('brand_attach', { p_store: storeId, p_brand: brandId, p_branch: String(branch || '').trim().slice(0, 60) }, true); },
    brandDetach: function (storeId) { return rpc('brand_detach', { p_store: storeId }, true); },
    branchCreate: function (brand, branch, address, lat, lng, phone) { branch = String(branch || '').trim(); if (branch.length < 2 || branch.length > 60) return Promise.resolve({ error: 'bad_value' }); return rpc('branch_create', { p_brand: brand, p_branch: branch, p_address: String(address || '').trim().slice(0, 200), p_lat: lat, p_lng: lng, p_phone: String(phone || '').trim().slice(0, 30) }, true); },
    brandSyncMenu: function (from, to) { return rpc('brand_sync_menu', { p_from: from, p_to: to }, true); },
    brands: function () { return (DB.brands || []); },
    staffRemove: function (id) { if (!/^[0-9a-f-]{36}$/i.test(String(id))) return Promise.resolve({ error: 'bad_value' }); return rpc('staff_remove', { p_user: id }, true); },
    assignOwner: function (id, email) { return rpc('assign_owner', { p_store: id, p_email: email }, true); },
    setDriverStatus: function (id, st) { return sb.from('profiles').update({ driver_status: st }).eq('id', id).then(done); },
    setMyPhone: function (p) { p = normPhone(p); if (!p) return Promise.resolve({ error: 'bad_phone' }); return rpc('set_my_phone', { p_phone: p }, true).then(function (r) { return r.error ? r : { ok: true, phone: p }; }); },
    setDriverBlocked: function (id, v) { return sb.from('profiles').update({ accept_blocked: !!v }).eq('id', id).then(done); },
    setDriverLimit: function (id, v) { v = +v; if (!isFinite(v) || v <= 0 || v > 1000000) return badStore(); return sb.from('profiles').update({ cash_limit: v }).eq('id', id).then(done); },
    settleCash: function (driverId) {
      return sb.rpc('settle_driver_cash', { p_driver: driverId }).then(function (r) {
        if (r.error) { console.error(r.error); return { error: errKey(r.error) }; }
        toast(t('saved') + ' (' + (+r.data || 0) + ' TJS)'); return refresh().then(function () { return { ok: true }; });
      });
    },

    banners: function (all) { var now = Date.now(); return DB.banners.filter(function (b) { return all || (b.is_active && (!b.starts_at || Date.parse(b.starts_at) <= now) && (!b.ends_at || Date.parse(b.ends_at) > now)); }); },
    addBanner: function (f) { if (!validBanner(f)) return badBanner(); return sb.from('banners').insert(f).then(done); },
    updateBanner: function (id, f) { if (!validBanner(f)) return badBanner(); return sb.from('banners').update(f).eq('id', id).then(done); },
    deleteBanner: function (id) { return sb.from('banners').delete().eq('id', id).then(done); },
    promos: function () { return DB.promos; },
    addPromo: function (f) { if (!validPromo(f)) return badPromo(); return sb.from('promo_codes').insert(f).then(done); },
    updatePromo: function (id, f) { if (!validPromo(f)) return badPromo(); return sb.from('promo_codes').update(f).eq('id', id).then(done); },
    deletePromo: function (id) { return sb.from('promo_codes').delete().eq('id', id).then(done); },
    isFav: function (storeId) { return DB.favs.indexOf(storeId) >= 0; },
    toggleFav: function (storeId) {
      var has = DB.favs.indexOf(storeId) >= 0;
      DB.favs = has ? DB.favs.filter(function (x) { return x !== storeId; }) : DB.favs.concat([storeId]);
      fireSoon();
      var q = has ? sb.from('favorites').delete().eq('user_id', ME.id).eq('store_id', storeId) : sb.from('favorites').insert({ user_id: ME.id, store_id: storeId });
      return q.then(function (r) { if (r.error) console.error(r.error); sigs = {}; return refresh(['misc']); });
    }
  };
  TLBref = window.TLB;
})();
