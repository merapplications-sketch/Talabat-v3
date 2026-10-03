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
  function setLang(l) { lang = l; try { localStorage.setItem(LK, l); } catch (e) {} applyI18n(); var b = document.getElementById('tlb-lang'); if (b) b.textContent = l === 'ru' ? 'RU | en' : 'ru | EN'; fire(); }
  document.addEventListener('DOMContentLoaded', function () {
    var b = document.createElement('div'); b.id = 'tlb-lang';
    b.style.cssText = 'position:fixed;top:3px;left:50%;transform:translateX(-50%);z-index:9999;background:#000a;color:#fff;font:700 10px sans-serif;padding:3px 9px;border-radius:10px;cursor:pointer';
    b.textContent = lang === 'ru' ? 'RU | en' : 'ru | EN';
    b.onclick = function () { setLang(lang === 'ru' ? 'en' : 'ru'); };
    document.body.appendChild(b); applyI18n();
  });


  Object.assign(I.ru, { tagline: 'Доставка еды и продуктов', authNameL:'Ваше имя',authBadEmail:'Введите корректный email, например name@mail.com',authNameShort:'Введите имя (минимум 2 буквы)',authPwShort:'Пароль слишком короткий: минимум 8 символов',authPwHint:'Минимум 8 символов',authWrong:'Неверный email или пароль',authExists:'Этот email уже зарегистрирован. Перейдите на вкладку «Вход».',authRate:'Слишком много попыток или писем. Подождите несколько минут и попробуйте снова.',authUnconf:'Email не подтверждён. Откройте письмо от нас и нажмите на ссылку.',authNoSignup:'Регистрация сейчас отключена.',authSentT:'Проверьте почту',authSentS:'Мы отправили ссылку для подтверждения на адрес:',authResend:'Отправить письмо ещё раз',authResent:'Письмо отправлено. Проверьте и папку «Спам».',authBack:'Войти',authWait:'Подождите минуту перед повторной отправкой.',authWaitB:'Подождите…', login: 'Войти', signup: 'Регистрация', password: 'Пароль', logout: 'Выйти', wrongRole: 'Этот аккаунт не подходит для этого приложения. Выйдите и войдите другим аккаунтом.',
    pendingApp: 'Ваш аккаунт ожидает одобрения администратора.', signupOk: 'Аккаунт создан. Если нужно, подтвердите почту и войдите.', err_generic: 'Ошибка. Попробуйте ещё раз.', err_bad_phone: 'Введите корректный номер, например +992901234567.', err_bad_value: 'Проверьте значения: проценты 0–100, цены не меньше 0, телефон и координаты корректные.', err_discount_over_max: 'Скидка выше допустимого максимума.', err_bad_banner: 'Проверьте баннер: дата окончания должна быть позже даты начала.', err_promo_invalid: 'Промокод не найден или не действует.', err_bad_options: 'Выбор опций изменился или недоступен. Откройте блюдо и выберите заново.', err_no_offer: 'Это предложение уже недоступно.', err_busy: 'У вас уже есть активный заказ.', err_already_rated: 'Вы уже оценили этот заказ.', err_closed_now: 'Ресторан сейчас закрыт.', err_too_many_orders: 'У вас уже 5 незавершённых заказов. Дождитесь доставки.', err_rating_fail: 'Не удалось получить рейтинг из Google. Проверьте Place ID и настройку функции.', err_promo_offer: 'Промокод нельзя применить, пока у магазина действует своя скидка.', err_promo_min: 'Сумма заказа меньше минимальной для этого промокода.', err_promo_used: 'Вы уже использовали этот промокод.', err_promo_limit: 'Промокод больше недоступен.', err_too_many: 'Слишком много попыток. Попробуйте через 10 минут.', err_bad_promo: 'Проверьте промокод: код 3–20 символов (латиница, цифры), значение больше 0, процент не больше 100.',
    err_not_approved: 'Аккаунт курьера не одобрен', err_not_allowed: 'Недостаточно прав', err_store_unavailable: 'Магазин недоступен', err_auth: 'Войдите в аккаунт', err_user_not_found: 'Пользователь не найден' });
  Object.assign(I.en, { tagline: 'Food and grocery delivery', authNameL:'Your name',authBadEmail:'Enter a valid email, e.g. name@mail.com',authNameShort:'Enter your name (at least 2 letters)',authPwShort:'Password is too short: at least 8 characters',authPwHint:'At least 8 characters',authWrong:'Wrong email or password',authExists:'This email is already registered. Switch to the “Sign in” tab.',authRate:'Too many attempts or emails. Wait a few minutes and try again.',authUnconf:'Email not confirmed. Open our email and tap the link.',authNoSignup:'Sign-up is currently disabled.',authSentT:'Check your email',authSentS:'We sent a confirmation link to:',authResend:'Send the email again',authResent:'Email sent. Please check your Spam folder too.',authBack:'Sign in',authWait:'Wait a minute before sending again.',authWaitB:'Please wait…', login: 'Sign in', signup: 'Sign up', password: 'Password', logout: 'Sign out', wrongRole: 'This account does not fit this app. Sign out and use another account.',
    pendingApp: 'Your account is waiting for admin approval.', signupOk: 'Account created. If needed, confirm your email and sign in.', err_generic: 'Something went wrong. Try again.', err_bad_phone: 'Enter a valid phone number, e.g. +992901234567.', err_bad_value: 'Check the values: percentages 0–100, prices not negative, valid phone and coordinates.', err_discount_over_max: 'The discount is above the allowed maximum.', err_bad_banner: 'Check the banner: the end date must be after the start date.', err_promo_invalid: 'Promo code not found or not active.', err_bad_options: 'The selected options changed or are unavailable. Open the dish and choose again.', err_no_offer: 'This offer is no longer available.', err_busy: 'You already have an active order.', err_already_rated: 'You have already rated this order.', err_closed_now: 'The restaurant is closed right now.', err_too_many_orders: 'You already have 5 unfinished orders. Please wait for delivery.', err_rating_fail: 'Could not get the rating from Google. Check the Place ID and the function setup.', err_promo_offer: 'Promo codes cannot be used while the store has its own discount.', err_promo_min: 'The order is below the minimum for this promo code.', err_promo_used: 'You have already used this promo code.', err_promo_limit: 'This promo code is no longer available.', err_too_many: 'Too many attempts. Try again in 10 minutes.', err_bad_promo: 'Check the promo: code 3–20 characters (letters, digits), value above 0, percent up to 100.',
    err_not_approved: 'Courier account is not approved', err_not_allowed: 'Not allowed', err_store_unavailable: 'Store unavailable', err_auth: 'Please sign in', err_user_not_found: 'User not found' });

  /* ---------- Extra dictionary ---------- */
  Object.assign(I.ru, { saved: 'Сохранено ✓', apple: 'Apple Pay', card: 'Карта Alif', cash: 'Наличными', openMap: 'Открыть на карте', locTitle: 'Отправить местоположение',
    locHint: 'Передвиньте булавку или коснитесь карты, чтобы указать точное место.', locSend: 'Отправить это место', mapFail: 'Не удалось загрузить карту', chatClosed: 'Чат закрыт',
    err_blocked: 'Приём заказов остановлен администратором', err_cash_required: 'Укажите полученную сумму', err_note_required: 'Укажите причину, если сумма отличается' });
  Object.assign(I.en, { saved: 'Saved ✓', apple: 'Apple Pay', card: 'Alif card', cash: 'Cash', openMap: 'Open on map', locTitle: 'Send location',
    locHint: 'Drag the pin or tap the map to set the exact place.', locSend: 'Send this location', mapFail: 'Could not load the map', chatClosed: 'Chat closed',
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
      ov.innerHTML = '<div style="padding:14px;display:flex;justify-content:space-between;align-items:center;font-weight:700;font-size:16px"><span data-i18n="locTitle"></span><span id="tlb-lx" style="font-size:24px;cursor:pointer;padding:0 6px">✕</span></div><div id="tlb-map" style="flex:1;min-height:200px"></div><div style="padding:12px 14px 18px"><div data-i18n="locHint" style="font-size:12px;color:#718096;margin-bottom:10px"></div><button id="tlb-ls" data-i18n="locSend" ' + BT + '></button></div>';
      document.body.appendChild(ov); applyI18n();
      var st = (start && isFinite(+start[0]) && isFinite(+start[1])) ? [+start[0], +start[1]] : null;
      var map = L.map('tlb-map').setView(st || [38.5598, 68.787], st ? 17 : 14);
      L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '© OpenStreetMap' }).addTo(map);
      var mk = L.marker(map.getCenter(), { draggable: true, icon: L.divIcon({ html: '<div style="font-size:34px;line-height:34px">📍</div>', className: '', iconSize: [34, 34], iconAnchor: [17, 34] }) }).addTo(map);
      map.on('click', function (e) { mk.setLatLng(e.latlng); });
      setTimeout(function () { map.invalidateSize(); }, 150);
      if (!st && navigator.geolocation) navigator.geolocation.getCurrentPosition(function (p) { var ll = [p.coords.latitude, p.coords.longitude]; map.setView(ll, 17); mk.setLatLng(ll); }, function () { }, { enableHighAccuracy: true, timeout: 10000 });
      function close() { map.remove(); ov.remove(); }
      $('tlb-lx').onclick = close;
      $('tlb-ls').onclick = function () { var ll = mk.getLatLng(); close(); cb(ll.lat, ll.lng); };
    });
  }

  /* ---------- Supabase runtime ---------- */
  var sb = null, ME = null, need = '', onReady = null, sig = '', ORD = [], firstLoad = true;
  var DB = { stores: [], items: [], orders: [], oitems: [], chat: [], drivers: [], banners: [], favs: [], events: [], cash: {}, promos: [], myOffers: [], offersAll: [], ratings: [], groups: [], options: [] };
  var seenChat = {}, lastStatus = {}, unread = {};
  function storeName(id) { var s = DB.stores.find(function (x) { return x.id === id; }); return s ? s.name : '?'; }
  function storePhone(id) { var s = DB.stores.find(function (x) { return x.id === id; }); return s ? (s.phone || '') : ''; }
  var VERSION = 'v19';
  function groupsOf(id) { return DB.groups.filter(function (g) { return g.item_id === id; }); }
  function availOpts(g) { return DB.options.filter(function (o) { return o.group_id === g.id && o.available; }); }
  function shapeItem(i) { return { id: i.id, name: i.name, price: +i.price, image: i.image_url || '', available: i.available, popular: i.popular, approved: i.approved, section: i.section || '', discount: +i.discount_pct || 0, hasOpts: groupsOf(i.id).some(function (g) { return availOpts(g).length > 0; }), optsBlocked: groupsOf(i.id).some(function (g) { return g.required && availOpts(g).length === 0; }), store: storeName(i.store_id) }; }
  function shape() {
    return DB.orders.map(function (o) {
      return { id: o.id, store: storeName(o.store_id), storeId: o.store_id, storePhone: storePhone(o.store_id), status: o.status,
        items: DB.oitems.filter(function (i) { return i.order_id === o.id; }).map(function (i) { return { id: i.item_id, name: i.name, price: +i.price, qty: i.qty, note: i.note || '', opts: Array.isArray(i.options) ? i.options.map(function (x) { return { id: x.id, g: String(x.g || ''), n: String(x.n || ''), p: +x.p || 0 }; }) : [] }; }),
        subtotal: +o.subtotal, discount: +o.discount, promoDiscount: +o.promo_discount || 0, promoCode: o.promo_code || '', delivery: +o.delivery_fee, tip: +o.tip, total: +o.total, commission: +o.commission, commissionPct: +o.commission_pct,
        payment: o.payment || '', address: o.address, prepTime: o.prep_time, driver: o.driver_id, driverName: o.driver_name || '', payout: +o.driver_payout,
        cashCollected: o.cash_collected == null ? null : +o.cash_collected, cashNote: o.cash_note || '', cashSettled: !!o.cash_settled_at,
        client: { name: o.customer_name || '', phone: o.customer_phone || '' }, customerId: o.customer_id,
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
  function refresh() {
    if (!ME) return Promise.resolve();
    return Promise.all([
      sb.from('stores').select('*').order('created_at'),
      sb.from('menu_items').select('*').order('created_at'),
      sb.from('orders').select('*').order('created_at', { ascending: false }).limit(200),
      sb.from('order_items').select('*'),
      sb.from('order_chat').select('*').order('created_at'),
      ME.role === 'admin' ? sb.from('profiles').select('*').eq('role', 'driver') : Promise.resolve({ data: [] }),
      sb.from('banners').select('*').order('sort').order('created_at'),
      sb.from('favorites').select('store_id'),
      sb.from('order_events').select('*').order('at'),
      sb.rpc('cash_balances'),
      sb.from('profiles').select('*').eq('id', ME.id).single(),
      ME.role === 'admin' ? sb.from('promo_codes').select('*').order('created_at', { ascending: false }) : Promise.resolve({ data: [] }),
      ME.role === 'driver' ? sb.rpc('my_offers') : Promise.resolve({ data: [] }),
      ME.role === 'admin' ? sb.from('order_offers').select('*').order('offered_at', { ascending: false }).limit(300) : Promise.resolve({ data: [] }),
      (ME.role === 'admin' || ME.role === 'customer') ? sb.from('ratings').select('*').order('created_at', { ascending: false }).limit(300) : Promise.resolve({ data: [] }),
      sb.from('item_option_groups').select('*').order('sort').order('created_at'),
      sb.from('item_options').select('*').order('sort').order('name')
    ]).then(function (r) {
      var bad = r.slice(0, 6).find(function (x) { return x.error; });
      if (bad) { console.error(bad.error); return; }
      var s = JSON.stringify(r.map(function (x) { return x.data; }));
      if (s === sig) return;
      sig = s;
      DB.stores = r[0].data || []; DB.items = r[1].data || []; DB.orders = r[2].data || [];
      DB.oitems = r[3].data || []; DB.chat = r[4].data || []; DB.drivers = r[5].data || [];
      DB.banners = r[6].error ? [] : (r[6].data || []);
      DB.favs = r[7].error ? [] : (r[7].data || []).map(function (x) { return x.store_id; });
      DB.events = r[8].error ? [] : (r[8].data || []);
      DB.cash = {}; if (!r[9].error) (r[9].data || []).forEach(function (x) { DB.cash[x.driver_id] = +x.balance; });
      if (!r[10].error && r[10].data) ME = Object.assign(ME, r[10].data);
      DB.promos = r[11].error ? [] : (r[11].data || []);
      var gotAt = Date.now();
      DB.myOffers = r[12].error ? [] : (r[12].data || []).map(function (x) { return { order_id: x.order_id, mode: x.mode, rank: x.rank, dist: x.dist_km == null ? null : +x.dist_km, secs: +x.secs_left || 0, got: gotAt }; });
      DB.offersAll = r[13].error ? [] : (r[13].data || []);
      DB.ratings = r[14].error ? [] : (r[14].data || []);
      DB.groups = r[15].error ? [] : (r[15].data || []); DB.options = r[16].error ? [] : (r[16].data || []);
      ORD = shape(); notify(); fire(); maybeTick();
    });
  }
  /* Dispatch heartbeat: expires old offers and moves waiting orders to the next courier. Only when it can matter. */
  function maybeTick() {
    if (!ME || !sb) return;
    var need_ = ME.role === 'driver' ? !!ME.online : (ME.role === 'admin' || ME.role === 'merchant') ? DB.orders.some(function (o) { return !o.driver_id && (o.status === 'preparing' || o.status === 'ready'); }) : false;
    if (need_) sb.rpc('dispatch_tick').then(function () { }, function () { });
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
    var ks = ['bad_options', 'no_offer', 'busy', 'already_rated', 'too_many_orders', 'promo_offer', 'promo_invalid', 'promo_min', 'promo_used', 'promo_limit', 'too_many', 'discount_over_max', 'bad_value', 'bad_phone', 'store_unavailable', 'unavailable', 'closed', 'empty', 'bad_transition', 'not_approved', 'not_allowed', 'user_not_found', 'blocked', 'cash_required', 'note_required', 'auth'];
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
  function cleanStore(f) { var c = Object.assign({}, f); if (typeof c.phone === 'string') c.phone = c.phone.replace(/[\s()-]/g, '') || null; return c; }
  function validStore(f) {
    var n = function (k, lo, hi) { if (f[k] == null || f[k] === '') return true; var v = +f[k]; return isFinite(v) && v >= lo && v <= hi; };
    if (!(n('commission_pct', 0, 100) && n('discount_pct', 0, 100) && n('max_discount_pct', 0, 100) && n('fee_base', 0, 100000) && n('fee_per_km', 0, 100000) && n('lat', -90, 90) && n('lng', -180, 180) && n('rating', 0, 5) && n('rating_count', 0, 100000000))) return false;
    if (f.google_place_id != null && f.google_place_id !== '' && !/^[A-Za-z0-9_-]{10,200}$/.test(String(f.google_place_id))) return false;
    if ((f.lat == null) !== (f.lng == null) && ('lat' in f || 'lng' in f)) return false;
    if (f.name != null && (String(f.name).trim().length < 1 || String(f.name).length > 80)) return false;
    if (f.description != null && String(f.description).length > 500) return false;
    if (f.phone != null && f.phone !== '' && !/^\+?[0-9]{7,15}$/.test(String(f.phone))) return false;
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
  function cleanSection(v) { v = String(v == null ? '' : v).replace(/\s+/g, ' ').trim().slice(0, 40); return v || null; }
  function badStore() { toast(t('err_bad_value'), true); return Promise.resolve({ error: 'bad_value', toasted: true }); }
  function me() { return ME ? { id: ME.id, name: ME.name || ME.email, email: ME.email, phone: ME.phone || '', cashLimit: +ME.cash_limit || 1000, blocked: !!ME.accept_blocked } : null; }

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
    if (need !== 'customer') return '';
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
    var su = authMode === 'up' && need === 'customer';
    overlay(authTabs() +
      (su ? '<input id="tlb-nm" type="text" maxlength="40" autocomplete="name" data-i18n-ph="authNameL" ' + IN + '>' : '') +
      '<input id="tlb-em" type="email" autocomplete="username" autocapitalize="off" placeholder="Email" ' + IN + '>' +
      '<div style="position:relative"><input id="tlb-pw" type="password" autocomplete="' + (su ? 'new-password' : 'current-password') + '" data-i18n-ph="password" ' + IN.replace('padding:0 14px', 'padding:0 48px 0 14px') + '><button id="tlb-eye" type="button" aria-label="show" style="position:absolute;right:6px;top:4px;width:40px;height:40px;border:0;background:none;font-size:18px;cursor:pointer;color:#8b8f98">👁</button></div>' +
      (su ? '<div data-i18n="authPwHint" style="font-size:12px;color:#8b8f98;margin:-4px 0 8px"></div>' : '') +
      '<div id="tlb-er" role="alert" style="color:#d92d20;background:' + (msg ? '#fdeceb' : 'transparent') + ';border-radius:12px;padding:' + (msg ? '10px 12px' : '0') + ';font-size:13px;font-weight:600;margin-bottom:10px;min-height:0">' + esc(msg || '') + '</div>' +
      '<button id="tlb-go" ' + BT + '></button>', true);
    $('tlb-go').textContent = su ? t('signup') : t('login');
    var show = function (txt) { var e = $('tlb-er'); e.textContent = txt; e.style.background = txt ? '#fdeceb' : 'transparent'; e.style.padding = txt ? '10px 12px' : '0'; };
    if ($('tlb-t-in')) { $('tlb-t-in').onclick = function () { showLogin('', 'in'); }; $('tlb-t-up').onclick = function () { showLogin('', 'up'); }; }
    $('tlb-eye').onclick = function () { var p = $('tlb-pw'); p.type = p.type === 'password' ? 'text' : 'password'; };
    var busy = false;
    var go = function () {
      if (busy) return;
      var email = $('tlb-em').value.trim().toLowerCase(), pw = $('tlb-pw').value, name = su ? $('tlb-nm').value.trim() : '';
      show('');
      if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return show(t('authBadEmail'));
      if (su && name.length < 2) return show(t('authNameShort'));
      if (su && pw.length < 8) return show(t('authPwShort'));
      if (!pw) return show(t('authPwShort'));
      busy = true; $('tlb-go').disabled = true; $('tlb-go').textContent = t('authWaitB');
      var req = su ? sb.auth.signUp({ email: email, password: pw, options: { data: { name: name.slice(0, 40) } } }) : sb.auth.signInWithPassword({ email: email, password: pw });
      req.then(function (r) {
        busy = false;
        if (r.error) { $('tlb-go').disabled = false; $('tlb-go').textContent = su ? t('signup') : t('login'); return show(authErr(r.error)); }
        if (!r.data.session) { return showSignupDone(email); }
        enter(r.data.user);
      }, function () { busy = false; $('tlb-go').disabled = false; $('tlb-go').textContent = su ? t('signup') : t('login'); show(t('err_generic')); });
    };
    $('tlb-go').onclick = go;
    ['tlb-em', 'tlb-pw', 'tlb-nm'].forEach(function (id) { var e = $(id); if (e) e.onkeydown = function (ev) { if (ev.key === 'Enter') go(); }; });
  }
  function blocked(key) {
    overlay('<h3 style="margin-bottom:10px;color:#1a202c" data-i18n="' + key + '"></h3><p style="color:#718096;margin-bottom:14px;font-size:13px">' + esc(ME.email) + ' — ' + esc(ME.role) + '</p><button id="tlb-lo" data-i18n="logout" ' + BT + '></button>');
    $('tlb-lo').onclick = logout;
  }
  function logoutBtn() {
    if (!$('tlb-out')) {
      var b = document.createElement('div'); b.id = 'tlb-out'; b.setAttribute('data-i18n', 'logout'); b.textContent = t('logout');
      b.style.cssText = 'position:fixed;top:3px;right:6px;z-index:9999;background:#000a;color:#fff;font:700 10px sans-serif;padding:3px 9px;border-radius:10px;cursor:pointer';
      b.onclick = logout; document.body.appendChild(b);
    }
    applyChrome();
  }
  function enter(user) {
    return sb.from('profiles').select('*').eq('id', user.id).single().then(function (x) {
      if (x.error || !x.data) { showLogin(x.error ? x.error.message : 'profile'); return; }
      ME = Object.assign({ email: user.email }, x.data);
      logoutBtn();
      if (ME.role !== need) return blocked('wrongRole');
      if (need === 'driver' && ME.driver_status !== 'approved') return blocked('pendingApp');
      var o = $('tlb-ov'); if (o) o.remove();
      return refresh().then(function () {
        sb.channel('tlb').on('postgres_changes', { event: '*', schema: 'public' }, function () { refresh(); }).subscribe();
        setInterval(refresh, 4000);
        onReady(me());
      });
    });
  }

  /* ---------- API ---------- */
  window.TLB = {
    version: VERSION,
    t: t, esc: esc, applyI18n: applyI18n, setLang: setLang, lang: function () { return lang; },
    addDict: function (ru, en) { Object.assign(I.ru, ru); Object.assign(I.en, en); },
    on: function (f) { subs.push(f); },
    /* role: 'customer' | 'merchant' | 'driver' | 'admin'. Each role keeps its own session, so all 4 apps can be open in one browser. */
    start: function (role, cb) {
      need = role; onReady = cb;
      sb = window.supabase.createClient(SB_URL, SB_KEY, { auth: { storageKey: 'tlb-auth-' + role } });
      sb.auth.getSession().then(function (x) { if (x.data.session) enter(x.data.session.user); else showLogin(); });
    },
    me: me, logout: logout, toast: toast, beep: beep, fmtMsg: fmtMsg, pickLocation: pickLocation,
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
    sendLocation: function (lat, lng, acc) { if (!isFinite(lat) || !isFinite(lng)) return Promise.resolve({ ok: false }); return sb.rpc('driver_location', { p_lat: lat, p_lng: lng, p_acc: isFinite(acc) ? acc : null }).then(function (r) { return { ok: !r.error }; }, function () { return { ok: false }; }); },
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
      return rpc('place_order', { p_store: s.id, p_items: items, p_tip: o.tip || 0, p_payment: o.payment || '', p_address: o.address || '', p_lat: null, p_lng: null, p_promo: (o.promo && /^[A-Za-z0-9_-]{3,20}$/.test(o.promo)) ? o.promo : null })
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
    setMyPhone: function (p) { p = String(p || '').replace(/[\s()-]/g, ''); if (!/^\+?[0-9]{7,15}$/.test(p)) return Promise.resolve({ error: 'bad_phone' }); return rpc('set_my_phone', { p_phone: p }, true).then(function (r) { return r.error ? r : { ok: true, phone: p }; }); },
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
      fire();
      var q = has ? sb.from('favorites').delete().eq('user_id', ME.id).eq('store_id', storeId) : sb.from('favorites').insert({ user_id: ME.id, store_id: storeId });
      return q.then(function (r) { if (r.error) console.error(r.error); sig = ''; return refresh(); });
    }
  };
})();
