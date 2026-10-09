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
      err_closed: 'Ресторан сейчас закрыт', err_unavailable: 'Товар недоступен', err_empty: 'Корзина пуста', err_bad_transition: 'Действие недоступно', err_taken: 'Заказ уже взят другим курьером',
      confirm_cancel: 'Отменить заказ?', clear_cart: 'В корзине товары другого магазина. Очистить корзину?', accept: 'Принять', reject: 'Отклонить', add: 'Добавить', cart: 'Корзина', pay: 'Оплатить заказ', online: 'На линии', offline: 'Не в сети' },
    en: { pending: 'Waiting for confirmation', preparing: 'Preparing', ready: 'Ready for courier pickup', pickedup: 'Courier on the way', delivered: 'Delivered', rejected: 'Rejected by restaurant', cancelled: 'Cancelled',
      err_closed: 'The restaurant is closed right now', err_unavailable: 'Item unavailable', err_empty: 'Cart is empty', err_bad_transition: 'Action not allowed', err_taken: 'Order already taken by another courier',
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
    chromeBar().appendChild(b); applyI18n();
  });


  Object.assign(I.ru, { tagline: 'Доставка еды и продуктов', loadFail:'Не удалось загрузить данные',dbOldW:'База данных не обновлена: выполните последний SQL-патч в Supabase. Часть функций не работает.', offline:'Нет интернета — данные не обновляются', loading:'Загрузка…',bootT:'Не удалось загрузить приложение',bootS:'Проверьте интернет и нажмите «Обновить». Если не помогает — выйдите и войдите снова.',bootReload:'Обновить',bootSignout:'Выйти и войти заново',applyT:'Стать курьером',applyS:'Укажите ваш номер телефона. Администратор рассмотрит заявку и откроет вам доступ.',applyB:'Подать заявку',notLinked:'Ваш аккаунт ещё не привязан к ресторану. Сообщите администратору ваш email — он привяжет аккаунт к вашему ресторану.',authPwHint2:'Минимум 8 символов. Придумайте новый пароль для Talabat — не используйте пароль от почты.',authPhoneL:'Телефон (+992…)', authNameL:'Ваше имя',authBadEmail:'Введите корректный email, например name@mail.com',authNameShort:'Введите имя (минимум 2 буквы)',authPwShort:'Пароль слишком короткий: минимум 8 символов',authPwHint:'Минимум 8 символов',authWrong:'Неверный email или пароль',authExists:'Этот email уже зарегистрирован. Перейдите на вкладку «Вход».',authRate:'Слишком много попыток или писем. Подождите несколько минут и попробуйте снова.',authUnconf:'Email не подтверждён. Откройте письмо от нас и нажмите на ссылку.',authNoSignup:'Регистрация сейчас отключена.',authSentT:'Проверьте почту',authSentS:'Мы отправили ссылку для подтверждения на адрес:',authResend:'Отправить письмо ещё раз',authResent:'Письмо отправлено. Проверьте и папку «Спам».',authBack:'Войти',authWait:'Подождите минуту перед повторной отправкой.',authWaitB:'Подождите…', login: 'Войти', signup: 'Регистрация', password: 'Пароль', logout: 'Выйти', wrongRole: 'Этот аккаунт не подходит для этого приложения. Выйдите и войдите другим аккаунтом.',
    authLock: 'Слишком много попыток. Подождите {s} сек.',
    pendingApp: 'Ваш аккаунт ожидает одобрения администратора.', signupOk: 'Аккаунт создан. Если нужно, подтвердите почту и войдите.', err_generic: 'Ошибка. Попробуйте ещё раз.', err_bad_value: 'Проверьте значения: проценты 0–100, цены не меньше 0, телефон и координаты корректные.', err_discount_over_max: 'Скидка выше допустимого максимума.', err_bad_banner: 'Проверьте баннер: дата окончания должна быть позже даты начала.', err_promo_invalid: 'Промокод не найден или не действует.', err_refund_too_high: 'Сумма возврата больше суммы заказа (с учётом уже возвращённого по нему).', err_refund_needs_order: 'Возврат возможен только по обращению, связанному с заказом.', err_wallet_changed: 'Баланс кошелька изменился. Проверьте сумму и подтвердите заказ ещё раз.', err_insufficient_funds: 'Недостаточно средств в кошельке.', err_already_refunded: 'Возврат по этому обращению уже зачислен.', err_phone_locked: 'Номер нельзя менять, пока есть активный заказ.', err_phone_cooldown: 'Номер можно менять не чаще одного раза в 30 дней. Обратитесь в поддержку.', err_account_blocked: 'Аккаунт приостановлен. Свяжитесь с поддержкой.', err_ticket_expired: 'Срок обращения по этому заказу (48 часов) истёк.', err_ticket_exists: 'По этому заказу уже есть открытое обращение.', err_ticket_closed: 'Обращение закрыто. Создайте новое, если проблема осталась.', err_not_found: 'Не найдено.',  err_fee_changed: 'Стоимость доставки изменилась. Проверьте сумму и подтвердите заказ ещё раз.', err_too_far: 'Адрес слишком далеко от ресторана. Выберите другой адрес или ресторан поближе.', err_phone_required: 'Укажите номер телефона (+992…) в профиле.', err_bad_phone: 'Введите номер Таджикистана: +992 и 9 цифр.', err_address_required: 'Добавьте адрес доставки на карте.', err_bad_options: 'Выбор опций изменился или недоступен. Откройте блюдо и выберите заново.', err_no_offer: 'Это предложение уже недоступно.', err_busy: 'У вас уже есть активный заказ.', err_already_rated: 'Вы уже оценили этот заказ.', err_closed_now: 'Ресторан сейчас закрыт.', err_too_many_orders: 'У вас уже 5 незавершённых заказов. Дождитесь доставки.', err_rating_fail: 'Не удалось получить рейтинг из Google. Проверьте Place ID и настройку функции.', err_promo_offer: 'Промокод нельзя применить, пока у магазина действует своя скидка.', err_promo_min: 'Сумма заказа меньше минимальной для этого промокода.', err_promo_used: 'Вы уже использовали этот промокод.', err_promo_limit: 'Промокод больше недоступен.', err_too_many: 'Слишком много попыток. Попробуйте через 10 минут.', err_bad_promo: 'Проверьте промокод: код 3–20 символов (латиница, цифры), значение больше 0, процент не больше 100.',
    err_not_approved: 'Аккаунт курьера не одобрен', err_not_allowed: 'Недостаточно прав', err_store_unavailable: 'Магазин недоступен', err_auth: 'Войдите в аккаунт', err_user_not_found: 'Пользователь не найден' });
  Object.assign(I.en, { tagline: 'Food and grocery delivery', loadFail:'Could not load the data',dbOldW:'The database is not up to date: run the latest SQL patch in Supabase. Some features do not work.', offline:'No internet — data is not updating', loading:'Loading…',bootT:'Could not load the app',bootS:'Check your internet and tap “Reload”. If it does not help, sign out and sign in again.',bootReload:'Reload',bootSignout:'Sign out and sign in again',applyT:'Become a courier',applyS:'Enter your phone number. The admin will review your request and open access for you.',applyB:'Apply',notLinked:'Your account is not linked to a restaurant yet. Send your email to the administrator — they will link the account to your restaurant.',authPwHint2:'At least 8 characters. Create a NEW password for Talabat — do not use your email password.',authPhoneL:'Phone (+992…)', authNameL:'Your name',authBadEmail:'Enter a valid email, e.g. name@mail.com',authNameShort:'Enter your name (at least 2 letters)',authPwShort:'Password is too short: at least 8 characters',authPwHint:'At least 8 characters',authWrong:'Wrong email or password',authExists:'This email is already registered. Switch to the “Sign in” tab.',authRate:'Too many attempts or emails. Wait a few minutes and try again.',authUnconf:'Email not confirmed. Open our email and tap the link.',authNoSignup:'Sign-up is currently disabled.',authSentT:'Check your email',authSentS:'We sent a confirmation link to:',authResend:'Send the email again',authResent:'Email sent. Please check your Spam folder too.',authBack:'Sign in',authWait:'Wait a minute before sending again.',authWaitB:'Please wait…', login: 'Sign in', signup: 'Sign up', password: 'Password', logout: 'Sign out', wrongRole: 'This account does not fit this app. Sign out and use another account.',
    authLock: 'Too many attempts. Wait {s} s.',
    pendingApp: 'Your account is waiting for admin approval.', signupOk: 'Account created. If needed, confirm your email and sign in.', err_generic: 'Something went wrong. Try again.', err_bad_value: 'Check the values: percentages 0–100, prices not negative, valid phone and coordinates.', err_discount_over_max: 'The discount is above the allowed maximum.', err_bad_banner: 'Check the banner: the end date must be after the start date.', err_promo_invalid: 'Promo code not found or not active.', err_refund_too_high: 'The refund is more than the order was worth (counting what was already refunded on it).', err_refund_needs_order: 'A refund is possible only on a request linked to an order.', err_wallet_changed: 'The wallet balance has changed. Check the amount and confirm the order again.', err_insufficient_funds: 'Not enough funds in the wallet.', err_already_refunded: 'The refund for this request has already been credited.', err_phone_locked: 'You cannot change the number while you have an active order.', err_phone_cooldown: 'The number can be changed only once every 30 days. Contact support.', err_account_blocked: 'Your account is suspended. Please contact support.', err_ticket_expired: 'The 48-hour window for this order has passed.', err_ticket_exists: 'There is already an open request for this order.', err_ticket_closed: 'This request is closed. Create a new one if the problem remains.', err_not_found: 'Not found.',  err_fee_changed: 'The delivery fee has changed. Check the total and confirm the order again.', err_too_far: 'The address is too far from the restaurant. Choose another address or a closer restaurant.', err_phone_required: 'Add your phone number (+992…) in your profile.', err_bad_phone: 'Enter a Tajikistan number: +992 and 9 digits.', err_address_required: 'Add a delivery address on the map.', err_bad_options: 'The selected options changed or are unavailable. Open the dish and choose again.', err_no_offer: 'This offer is no longer available.', err_busy: 'You already have an active order.', err_already_rated: 'You have already rated this order.', err_closed_now: 'The restaurant is closed right now.', err_too_many_orders: 'You already have 5 unfinished orders. Please wait for delivery.', err_rating_fail: 'Could not get the rating from Google. Check the Place ID and the function setup.', err_promo_offer: 'Promo codes cannot be used while the store has its own discount.', err_promo_min: 'The order is below the minimum for this promo code.', err_promo_used: 'You have already used this promo code.', err_promo_limit: 'This promo code is no longer available.', err_too_many: 'Too many attempts. Try again in 10 minutes.', err_bad_promo: 'Check the promo: code 3–20 characters (letters, digits), value above 0, percent up to 100.',
    err_not_approved: 'Courier account is not approved', err_not_allowed: 'Not allowed', err_store_unavailable: 'Store unavailable', err_auth: 'Please sign in', err_user_not_found: 'User not found' });

  /* ---------- Extra dictionary ---------- */
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
  function unlock() { try { if (!AC) AC = new (window.AudioContext || window.webkitAudioContext)(); if (AC.state === 'suspended') AC.resume(); } catch (e) { } }
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
    if (m) return '<a href="https://www.google.com/maps?q=' + m[1] + ',' + m[2] + '" target="_blank" rel="noopener" style="color:inherit;font-weight:700;text-decoration:underline">📍 ' + esc(t('openMap')) + '</a>';
    return esc(txt);
  }
  function loadLeaflet(cb) {
    if (window.L) return cb();
    var l = document.createElement('link'); l.rel = 'stylesheet'; l.href = 'https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css'; document.head.appendChild(l);
    var s = document.createElement('script'); s.src = 'https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js';
    s.onload = cb; s.onerror = function () { toast(t('mapFail'), true); }; document.head.appendChild(s);
  }
  /* One-time (not live) location: map opens on the device position, the user can drag the pin or tap the map. */
  function pickLocation(cb, start) {
    loadLeaflet(function () {
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
      L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '\u00a9 OpenStreetMap' }).addTo(map);
      var show = function () { var c = map.getCenter(); $('tlb-co').textContent = c.lat.toFixed(6) + ', ' + c.lng.toFixed(6); };
      map.on('movestart', function () { var p = $('tlb-pin'); if (p) p.style.transform = 'translateY(-10px)'; });
      map.on('move', show);
      map.on('moveend', function () { var p = $('tlb-pin'); if (p) p.style.transform = ''; show(); });
      setTimeout(function () { map.invalidateSize(); show(); }, 150);
      function locate(silent) {
        $('tlb-lm').textContent = '';
        if (!navigator.geolocation) { if (!silent) $('tlb-lm').textContent = t('locNA'); return; }
        navigator.geolocation.getCurrentPosition(function (p) { map.setView([p.coords.latitude, p.coords.longitude], 17); show(); },
          function (e) { if (!silent) $('tlb-lm').textContent = (e && e.code === 1) ? t('locDenied') : t('locFail'); }, { enableHighAccuracy: true, timeout: 12000, maximumAge: 5000 });
      }
      if (!st) locate(true);
      $('tlb-me').onclick = function () { locate(false); };
      function close() { map.remove(); ov.remove(); }
      $('tlb-lx').onclick = close;
      $('tlb-ls').onclick = function () { var c = map.getCenter(); close(); cb(c.lat, c.lng); };
    });
  }

  /* ---------- Supabase runtime ---------- */
  var sb = null, ME = null, need = '', onReady = null, sig = '', ORD = [], firstLoad = true;
  var DB = { stores: [], items: [], orders: [], oitems: [], chat: [], drivers: [], banners: [], favs: [], events: [], cash: {}, promos: [], myOffers: [], offersAll: [], ratings: [], groups: [], options: [], addresses: [], contacts: {}, settings: {}, myRating: null, tickets: [], tmsgs: {}, texts: {}, sreqs: [], people: {}, wallet: { balance: 0, entries: [] }, pages: {} };
  var seenChat = {}, lastStatus = {}, unread = {};
  var walletStale = true, wantTix = false, tixHold = false, sigs = {}, secRun = {}, secT0 = {}, secFail = {}, extraLoaded = {}, extraOrders = {}, kicks = {}, offlineNow = false, lastProbe = 0, lastTick = 0, fireT = null, errSent = 0;
  function storeName(id) { var s = DB.stores.find(function (x) { return x.id === id; }); return s ? s.name : '?'; }
  function storePhone(id) { var s = DB.stores.find(function (x) { return x.id === id; }); return s ? (s.phone || '') : ''; }
  var VERSION = 'v30';
  function groupsOf(id) { return DB.groups.filter(function (g) { return g.item_id === id; }); }
  function availOpts(g) { return DB.options.filter(function (o) { return o.group_id === g.id && o.available; }); }
  function shapeItem(i) { return { id: i.id, name: i.name, price: +i.price, image: i.image_url || '', available: i.available, popular: i.popular, approved: i.approved, section: i.section || '', discount: +i.discount_pct || 0, hasOpts: groupsOf(i.id).some(function (g) { return availOpts(g).length > 0; }), optsBlocked: groupsOf(i.id).some(function (g) { return g.required && availOpts(g).length === 0; }), store: storeName(i.store_id) }; }
  function shape() {
    return DB.orders.map(function (o) {
      return { id: o.id, store: storeName(o.store_id), storeId: o.store_id, storePhone: storePhone(o.store_id), status: o.status,
        items: DB.oitems.filter(function (i) { return i.order_id === o.id; }).map(function (i) { return { id: i.item_id, name: i.name, price: +i.price, qty: i.qty, note: i.note || '', opts: Array.isArray(i.options) ? i.options.map(function (x) { return { id: x.id, g: String(x.g || ''), n: String(x.n || ''), p: +x.p || 0 }; }) : [] }; }),
        subtotal: +o.subtotal, discount: +o.discount, promoDiscount: +o.promo_discount || 0, promoCode: o.promo_code || '', delivery: +o.delivery_fee, tip: +o.tip, total: +o.total, commission: +o.commission, commissionPct: +o.commission_pct,
        payment: o.payment || '', address: o.address, deliveryBase: o.delivery_base == null ? null : +o.delivery_base, deliveryExtra: +o.delivery_extra || 0, deliveryKm: o.delivery_km == null ? null : +o.delivery_km, walletUsed: +o.wallet_used || 0, lat: o.lat == null ? null : +o.lat, lng: o.lng == null ? null : +o.lng, prepTime: o.prep_time, driver: o.driver_id, driverName: o.driver_name || '', payout: +o.driver_payout,
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
  var STORE_COLS = 'id,name,category,description,logo_url,cover_url,address,lat,lng,fee_type,fee_base,fee_per_km,fee_free_km,discount_pct,is_open,is_active,is_featured,created_at,phone,free_first_delivery,google_place_id,rating,rating_count,rating_updated_at,app_rating,app_rating_count';
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
        if (res.error && (res.error.code === '42703' || /does not exist/i.test(String(res.error.message || '')))) { dbOld = true; return storesQuery(STORE_COLS_BASE); }
        return res;
      }),
      sb.from('menu_items').select('*').order('created_at').limit(5000),
      sb.from('banners').select('*').order('sort').order('created_at').limit(100),
      sb.from('item_option_groups').select('*').order('sort').order('created_at').limit(5000),
      sb.from('item_options').select('*').order('sort').order('name').limit(20000),
      (ME.role === 'admin' || ME.role === 'merchant') ? sb.rpc('store_private') : Promise.resolve({ data: [] })
    ]).then(function (r) {
      if (r[0].error || r[1].error) throw (r[0].error || r[1].error);
      if (dbOld && (ME.role === 'admin' || ME.role === 'merchant')) banner('tlb-old', t('dbOldW'), '#c2410c', 150);
      var priv = {}; (r[5].error ? [] : (r[5].data || [])).forEach(function (p) { priv[p.id] = p; });
      var stores = (r[0].data || []).map(function (x) { var p = priv[x.id]; return p ? Object.assign({}, x, { owner_id: p.owner_id, commission_pct: p.commission_pct, max_discount_pct: p.max_discount_pct }) : x; });
      var pack = [stores, r[1].data, r[2].error ? [] : r[2].data, r[3].error ? [] : r[3].data, r[4].error ? [] : r[4].data];
      if (!changed('stat', pack)) return false;
      DB.stores = pack[0] || []; DB.items = pack[1] || []; DB.banners = pack[2] || []; DB.groups = pack[3] || []; DB.options = pack[4] || [];
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
        ME.role === 'admin' ? Promise.resolve({ data: null }) : sb.rpc('active_contacts')
      ]).then(function (x) {
        if (x[0].error) throw x[0].error;
        var cash = {}; if (!x[2].error) (x[2].data || []).forEach(function (c) { cash[c.driver_id] = +c.balance; });
        // chat of orders opened on demand (admin detail) that are no longer "live" stays in memory
        var keepChat = DB.chat.filter(function (c) { return live.indexOf(c.order_id) < 0 && extraOrders[c.order_id]; });
        var chat = (x[1].error ? [] : (x[1].data || [])).concat(keepChat);
        var contacts = {}; if (x[3] && !x[3].error) (x[3].data || []).forEach(function (c) { contacts[c.order_id] = { customer_phone: c.customer_phone || '', driver_phone: c.driver_phone || '' }; });
        if (ME.role === 'admin') contacts = DB.contacts;                       // the admin loads phones on demand (opened order, low ratings)
        if (!changed('orders', [rows, x[0].data, chat, cash, contacts])) return false;
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
      admin ? sb.from('app_settings').select('*') : Promise.resolve({ data: [] }),
      ME.role === 'driver' ? sb.rpc('my_rating') : Promise.resolve({ data: null }),
      // a customer's tickets and the support phone are fetched only when he has a ticket or opened the support screen (keeps an idle customer cheap)
      (admin || (cust && (DB.tickets.length || wantTix))) ? sb.from('support_tickets').select('*').order('updated_at', { ascending: false }).limit(admin ? 200 : 30) : Promise.resolve({ data: cust ? DB.tickets : [] }),
      (admin || (cust && (DB.tickets.length || wantTix))) ? sb.from('app_texts').select('*') : Promise.resolve({ data: Object.keys(DB.texts).map(function (k) { return { key: k, value: DB.texts[k] }; }) }),
      (admin || ME.role === 'merchant') ? sb.from('store_requests').select('*').order('created_at', { ascending: false }).limit(admin ? 100 : 20) : Promise.resolve({ data: [] }),
      // the balance is fetched once, then only after a wallet event (realtime), coming back to the app, or an order that used it: an idle customer costs nothing
      cust ? (walletStale ? sb.rpc('wallet_balance') : Promise.resolve({ data: DB.wallet.balance })) : Promise.resolve({ data: null })
    ]).then(function (r) {
      if (r[0].error && r[1].error) throw r[0].error;
      var pack = [r[0].data, r[1].error ? [] : r[1].data, r[2].error ? [] : r[2].data, r[3].error ? [] : r[3].data, r[4].error ? [] : r[4].data, r[5].error ? [] : r[5].data, r[6].error ? [] : r[6].data, r[7].error ? [] : r[7].data, r[8].error ? null : r[8].data, r[9].error ? [] : r[9].data, r[10].error ? [] : r[10].data, r[11].error ? [] : r[11].data, r[12].error ? null : r[12].data];
      if (!changed('misc', pack)) return false;
      if (pack[0]) ME = Object.assign(ME, pack[0]);
      DB.favs = (pack[1] || []).map(function (x) { return x.store_id; });
      DB.ratings = pack[2] || []; DB.addresses = pack[3] || []; DB.promos = pack[4] || []; DB.drivers = pack[5] || []; DB.offersAll = pack[6] || [];
      var st = {}; (pack[7] || []).forEach(function (x) { st[x.key] = +x.value; }); DB.settings = st;
      DB.myRating = pack[8] && pack[8].count != null ? { avg: pack[8].avg == null ? null : +pack[8].avg, count: +pack[8].count || 0 } : null;
      DB.tickets = pack[9] || []; DB.sreqs = pack[11] || [];
      if (ME.role === 'customer') { DB.wallet.balance = pack[12] == null ? 0 : Math.round(+pack[12] * 100) / 100; if (!r[12].error) walletStale = false; }
      if (ME.role === 'customer' && !DB.tickets.length && !tixHold) wantTix = false;   // nothing to follow: stop fetching until he opens support
      var tx = {}; (pack[10] || []).forEach(function (x) { tx[x.key] = x.value || ''; }); DB.texts = tx;
      return true;
    }).then(function (ch) {
      if (ME.role !== 'admin') return ch;
      var need = {}; DB.tickets.forEach(function (t) { if (!DB.people[t.customer_id]) need[t.customer_id] = 1; }); DB.sreqs.forEach(function (q) { if (!DB.people[q.user_id]) need[q.user_id] = 1; });
      var pids = Object.keys(need).slice(0, 100);
      if (pids.length) return sb.from('profiles').select('id,name,phone').in('id', pids).then(function (pr) { (pr.data || []).forEach(function (p) { DB.people[p.id] = { name: p.name || '', phone: p.phone || '' }; }); return true; }, function () { return ch; }).then(function (more) { return afterAdminMisc(ch || more); });
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
    secRun[name] = p.then(function (ch) { secFail[name] = 0; if (!secFail.stat && !secFail.orders) unbanner('tlb-err'); return !!ch; }, function (e) {
      secFail[name] = (secFail[name] || 0) + 1; console.error(name, e); lastErr = String((e && e.message) || e);
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
    on('orders', 'orders'); on('order_chat', 'orders');
    if (ME.role === 'driver') on('order_offers', 'offers');
    if (ME.role === 'admin') { on('ratings', 'misc'); on('order_offers', 'misc'); on('support_tickets', 'misc'); on('ticket_messages', 'misc'); on('store_requests', 'misc'); }
    if (ME.role === 'customer') { on('support_tickets', 'misc'); ch.on('postgres_changes', { event: '*', schema: 'public', table: 'wallet_entries' }, function () { walletStale = true; kick('misc'); }); }
    if (ME.role === 'merchant') { on('store_requests', 'misc'); }
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
  function setOffline(on) {
    var b = $('tlb-off');
    if (on) {
      offlineNow = true;
      if (!b) {
        b = document.createElement('div'); b.id = 'tlb-off'; b.setAttribute('data-i18n', 'offline');
        b.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:10002;background:#1c1c21;color:#fff;font:600 13px -apple-system,sans-serif;text-align:center;padding:calc(6px + env(safe-area-inset-top,0px)) 8px 6px';
        document.body.appendChild(b); applyI18n();
      }
    } else if (offlineNow || b) { offlineNow = false; if (b) b.remove(); refresh(); }
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
    var ks = ['refund_too_high', 'refund_needs_order', 'wallet_changed', 'insufficient_funds', 'already_refunded', 'note_required', 'phone_locked', 'phone_cooldown', 'account_blocked', 'ticket_expired', 'ticket_exists', 'ticket_closed', 'not_found', 'fee_changed', 'too_far', 'phone_required', 'address_required', 'bad_options', 'no_offer', 'busy', 'already_rated', 'too_many_orders', 'promo_offer', 'promo_invalid', 'promo_min', 'promo_used', 'promo_limit', 'too_many', 'discount_over_max', 'bad_value', 'bad_phone', 'store_unavailable', 'unavailable', 'closed', 'empty', 'bad_transition', 'not_approved', 'not_allowed', 'user_not_found', 'blocked', 'cash_required', 'note_required', 'auth'];
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
  function logout() { sb.auth.signOut().then(function () { location.reload(); }); }
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
  function blocked(key) {
    overlay('<h3 style="margin-bottom:10px;color:#1a202c" data-i18n="' + key + '"></h3><p style="color:#718096;margin-bottom:14px;font-size:13px">' + esc(ME.email) + ' — ' + esc(ME.role) + '</p><button id="tlb-lo" data-i18n="logout" ' + BT + '></button>');
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
      if (ME.role !== need) { bootHide(); return blocked('wrongRole'); }
      if (need === 'driver' && ME.driver_status !== 'approved') { bootHide(); return blocked('pendingApp'); }
      var o = $('tlb-ov'); if (o) o.remove();
      return refresh().then(function () {
        try { subscribeRealtime(); } catch (e) { console.error(e); }
        startScheduler();
        bootHide();
        onReady(me());
      });
    }).catch(function (e) { console.error(e); bootFail(e); });
  }

  /* ---------- API ---------- */
  var TLBref = null;
  window.TLB = {
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
    me: me, logout: logout, toast: toast, beep: beep, ring: ring, audioReady: audioOk, unlockAudio: unlockNow, testSound: function () { unlockNow(); ringBeep(); }, fmtMsg: fmtMsg, pickLocation: pickLocation,
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
    orders: function (fn) { return ORD.filter(fn || function () { return true; }); },
    offers: function () {
      return DB.myOffers.map(function (f) {
        var o = ORD.filter(function (x) { return x.id === f.order_id; })[0]; if (!o) return null;
        return Object.assign({}, o, { offer: { mode: f.mode, rank: f.rank, dist: f.dist, left: Math.max(0, f.secs - (Date.now() - f.got) / 1000) } });
      }).filter(Boolean);
    },
    decline: function (id) { return sb.rpc('driver_decline', { p_id: id }).then(function (r) { return refresh().then(function () { return r.error ? { error: errKey(r.error) } : { ok: true }; }); }); },
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
    loadPages: function (force) {
      var now = Date.now();
      if (!force && extraLoaded.pages && now - extraLoaded.pages < 30000) return Promise.resolve(false);
      extraLoaded.pages = now;
      return sb.from('app_pages').select('slug,body_ru,body_en').then(function (r) {
        if (r.error) return false;
        var o = {}; (r.data || []).forEach(function (p) { o[p.slug] = { ru: p.body_ru || '', en: p.body_en || '' }; });
        if (JSON.stringify(o) === JSON.stringify(DB.pages)) return false;
        DB.pages = o; fireSoon(); return true;
      }, function () { return false; });
    },
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
    /* ---------- customers (admin) ---------- */
    customers: function (q, offset) {
      return sb.rpc('admin_customers', { p_q: String(q || '').trim().slice(0, 60) || null, p_limit: 30, p_offset: Math.max(0, Math.floor(+offset || 0)) }).then(function (r) { return r.error ? { error: errKey(r.error), rows: [] } : { rows: r.data || [] }; }, function () { return { error: 'generic', rows: [] }; });
    },
    customerOrders: function (id) {
      return sb.from('orders').select('id,store_id,status,total,created_at').eq('customer_id', id).order('created_at', { ascending: false }).limit(50).then(function (r) {
        return (r.data || []).map(function (o) { return { id: o.id, store: storeName(o.store_id), status: o.status, total: +o.total, createdAt: Date.parse(o.created_at) }; });
      }, function () { return []; });
    },
    setBan: function (id, banned, reason) {
      if (banned && String(reason || '').trim().length < 3) return Promise.resolve({ error: 'note_required' });
      return rpc('set_customer_ban', { p_id: id, p_banned: !!banned, p_reason: String(reason || '').slice(0, 200) }, true);
    },
    /* ---------- wallet ---------- */
    wallet: function () { return DB.wallet; },
    loadWallet: function (force) {
      var now = Date.now(), k = 'wallet';
      if (!force && extraLoaded[k] && now - extraLoaded[k] < 6000) return Promise.resolve(false);
      extraLoaded[k] = now;
      return Promise.all([sb.from('wallet_entries').select('*').eq('user_id', ME.id).order('created_at', { ascending: false }).limit(60), sb.rpc('wallet_balance')]).then(function (r) {
        if (r[0].error) return false;
        var key = JSON.stringify(r[0].data || []); var ch = JSON.stringify(DB.wallet.entries) !== key;
        DB.wallet.entries = (r[0].data || []).map(function (e) { return { id: e.id, amount: +e.amount, kind: e.kind, orderId: e.order_id, ticketId: e.ticket_id, note: e.note || '', at: Date.parse(e.created_at) }; });
        if (!r[1].error && r[1].data != null) DB.wallet.balance = Math.round(+r[1].data * 100) / 100;
        if (ch) fireSoon(); return ch;
      }, function () { return false; });
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
        L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '© OpenStreetMap' }).addTo(map);
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
      return rpc('place_order', { p_store: s.id, p_items: items, p_tip: o.tip || 0, p_payment: o.payment || '', p_address: String(o.address || '').slice(0, 200), p_lat: isNaN(num(o.lat)) ? null : num(o.lat), p_lng: isNaN(num(o.lng)) ? null : num(o.lng), p_promo: (o.promo && /^[A-Za-z0-9_-]{3,20}$/.test(o.promo)) ? o.promo : null, p_fee: isNaN(num(o.fee)) ? null : num(o.fee), p_wallet: (isNaN(num(o.wallet)) || num(o.wallet) <= 0) ? null : Math.round(num(o.wallet) * 100) / 100 })
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
    deliver: function (id, cash, note) { return rpc('deliver_order', { p_id: id, p_cash: cash, p_note: note || null }); },
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
