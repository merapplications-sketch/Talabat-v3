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


  Object.assign(I.ru, { login: 'Войти', signup: 'Регистрация', password: 'Пароль', logout: 'Выйти', wrongRole: 'Этот аккаунт не подходит для этого приложения. Выйдите и войдите другим аккаунтом.',
    pendingApp: 'Ваш аккаунт ожидает одобрения администратора.', signupOk: 'Аккаунт создан. Если нужно, подтвердите почту и войдите.', err_generic: 'Ошибка. Попробуйте ещё раз.', err_bad_phone: 'Введите корректный номер, например +992901234567.', err_bad_value: 'Проверьте значения: проценты 0–100, цены не меньше 0, телефон и координаты корректные.', err_discount_over_max: 'Скидка выше допустимого максимума.', err_bad_banner: 'Проверьте баннер: дата окончания должна быть позже даты начала.',
    err_not_approved: 'Аккаунт курьера не одобрен', err_not_allowed: 'Недостаточно прав', err_store_unavailable: 'Магазин недоступен', err_auth: 'Войдите в аккаунт', err_user_not_found: 'Пользователь не найден' });
  Object.assign(I.en, { login: 'Sign in', signup: 'Sign up', password: 'Password', logout: 'Sign out', wrongRole: 'This account does not fit this app. Sign out and use another account.',
    pendingApp: 'Your account is waiting for admin approval.', signupOk: 'Account created. If needed, confirm your email and sign in.', err_generic: 'Something went wrong. Try again.', err_bad_phone: 'Enter a valid phone number, e.g. +992901234567.', err_bad_value: 'Check the values: percentages 0–100, prices not negative, valid phone and coordinates.', err_discount_over_max: 'The discount is above the allowed maximum.', err_bad_banner: 'Check the banner: the end date must be after the start date.',
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
  var DB = { stores: [], items: [], orders: [], oitems: [], chat: [], drivers: [], banners: [], favs: [], events: [], cash: {} };
  var seenChat = {}, lastStatus = {}, unread = {};
  function storeName(id) { var s = DB.stores.find(function (x) { return x.id === id; }); return s ? s.name : '?'; }
  function storePhone(id) { var s = DB.stores.find(function (x) { return x.id === id; }); return s ? (s.phone || '') : ''; }
  function shapeItem(i) { return { id: i.id, name: i.name, price: +i.price, image: i.image_url || '', available: i.available, popular: i.popular, approved: i.approved, store: storeName(i.store_id) }; }
  function shape() {
    return DB.orders.map(function (o) {
      return { id: o.id, store: storeName(o.store_id), storeId: o.store_id, storePhone: storePhone(o.store_id), status: o.status,
        items: DB.oitems.filter(function (i) { return i.order_id === o.id; }).map(function (i) { return { id: i.item_id, name: i.name, price: +i.price, qty: i.qty, note: i.note || '' }; }),
        subtotal: +o.subtotal, discount: +o.discount, delivery: +o.delivery_fee, tip: +o.tip, total: +o.total, commission: +o.commission, commissionPct: +o.commission_pct,
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
      sb.from('profiles').select('*').eq('id', ME.id).single()
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
      ORD = shape(); notify(); fire();
    });
  }
  function errKey(e) {
    var m = String((e && e.message) || '').toLowerCase();
    var ks = ['discount_over_max', 'bad_value', 'bad_phone', 'store_unavailable', 'unavailable', 'closed', 'empty', 'bad_transition', 'not_approved', 'not_allowed', 'user_not_found', 'blocked', 'cash_required', 'note_required', 'auth'];
    for (var i = 0; i < ks.length; i++) if (m.indexOf(ks[i]) >= 0) return ks[i];
    return 'generic';
  }
  function rpc(name, args, okToast) {
    return sb.rpc(name, args).then(function (r) {
      if (r.error) { console.error(r.error); return { error: errKey(r.error) }; }
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
    if (!(n('commission_pct', 0, 100) && n('discount_pct', 0, 100) && n('max_discount_pct', 0, 100) && n('fee_base', 0, 100000) && n('fee_per_km', 0, 100000) && n('lat', -90, 90) && n('lng', -180, 180))) return false;
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
  function badBanner() { toast(t('err_bad_banner'), true); return Promise.resolve({ error: 'bad_banner', toasted: true }); }
  function badStore() { toast(t('err_bad_value'), true); return Promise.resolve({ error: 'bad_value', toasted: true }); }
  function me() { return ME ? { id: ME.id, name: ME.name || ME.email, email: ME.email, phone: ME.phone || '', cashLimit: +ME.cash_limit || 1000, blocked: !!ME.accept_blocked } : null; }

  /* ---------- login screens ---------- */
  var IN = 'style="width:100%;padding:12px;margin-bottom:10px;border:1px solid #cbd5e1;border-radius:10px;font-size:15px"';
  var BT = 'style="width:100%;padding:13px;border:0;border-radius:10px;background:#ff5a00;color:#fff;font-weight:700;font-size:15px;margin-top:6px"';
  function overlay(html) {
    var d = $('tlb-ov');
    if (!d) { d = document.createElement('div'); d.id = 'tlb-ov'; d.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;z-index:9998;background:#f4f6f8;display:flex;align-items:center;justify-content:center;padding:20px;font:14px -apple-system,BlinkMacSystemFont,sans-serif'; document.body.appendChild(d); }
    d.innerHTML = '<div style="background:#fff;border-radius:16px;padding:22px;width:100%;max-width:340px;box-shadow:0 4px 20px #0002">' + html + '</div>';
    applyI18n();
  }
  function logout() { sb.auth.signOut().then(function () { location.reload(); }); }
  function showLogin(msg) {
    overlay('<h2 style="color:#ff5a00;margin-bottom:14px">Talabat</h2><input id="tlb-em" type="email" autocomplete="username" placeholder="Email" ' + IN + '><input id="tlb-pw" type="password" autocomplete="current-password" data-i18n-ph="password" ' + IN + '><div id="tlb-er" style="color:#e74c3c;font-size:12px;margin-bottom:8px;min-height:14px">' + esc(msg || '') + '</div><button id="tlb-go" data-i18n="login" ' + BT + '></button>' +
      (need === 'customer' ? '<button id="tlb-su" data-i18n="signup" ' + BT.replace('#ff5a00', '#edf2f7').replace('#fff', '#2d3748') + '></button>' : ''));
    var go = function (signup) {
      var args = { email: $('tlb-em').value.trim(), password: $('tlb-pw').value };
      $('tlb-er').textContent = '';
      (signup ? sb.auth.signUp(args) : sb.auth.signInWithPassword(args)).then(function (r) {
        if (r.error) { $('tlb-er').textContent = r.error.message; return; }
        if (!r.data.session) { $('tlb-er').textContent = t('signupOk'); return; }
        enter(r.data.user);
      });
    };
    $('tlb-go').onclick = function () { go(false); };
    if ($('tlb-su')) $('tlb-su').onclick = function () { go(true); };
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
    getMenu: function (n) { return this.allMenus(false)[n] || []; },
    isOpen: function (n) { var s = storeByName(n); return !!s && s.is_open && s.is_active; },
    setOpen: function (n, v) { var s = storeByName(n); return s ? rpc('set_store_open', { p_store: s.id, p_open: !!v }, true) : Promise.resolve({ error: 'generic' }); },

    order: function (id) { return ORD.find(function (o) { return o.id == id; }) || null; },
    orders: function (fn) { return ORD.filter(fn || function () { return true; }); },
    offers: function () { return ORD.filter(function (o) { return !o.driver && (o.status === 'preparing' || o.status === 'ready'); }); },
    events: function (id) { return DB.events.filter(function (e) { return e.order_id == id; }); },
    cash: function (driverId) { return DB.cash[driverId] || 0; },
    myCash: function () { return ME ? (DB.cash[ME.id] || 0) : 0; },
    placeOrder: function (o) {
      var s = storeByName(o.store); if (!s) return Promise.resolve({ error: 'store_unavailable' });
      var items = Object.keys(o.cart).map(function (id) { return { item_id: id, qty: o.cart[id], note: (o.notes || {})[id] || '' }; });
      return rpc('place_order', { p_store: s.id, p_items: items, p_tip: o.tip || 0, p_payment: o.payment || '', p_address: o.address || '', p_lat: null, p_lng: null })
        .then(function (r) { return r.error ? r : { id: r.data }; });
    },
    setStatus: function (id, to) { return rpc('set_order_status', { p_id: id, p_to: to }); },
    patch: function (id, f) { return rpc('set_prep_time', { p_id: id, p_min: f.prepTime }, true); },
    driverAccept: function (id) { return rpc('driver_accept', { p_id: id }).then(function (r) { return r.error ? r : (r.data === true ? { ok: true } : { error: 'taken' }); }); },
    deliver: function (id, cash, note) { return rpc('deliver_order', { p_id: id, p_cash: cash, p_note: note || null }); },
    chat: function (id, sender, text) { return sb.from('order_chat').insert({ order_id: id, sender_id: ME.id, body: String(text).slice(0, 200) }).then(doneQ); },

    addItem: function (storeN, f) { var s = storeByName(storeN); return sb.from('menu_items').insert({ store_id: s.id, name: f.name, price: f.price, image_url: f.image || null, popular: !!f.popular }).then(done); },
    updateItem: function (id, f) { return sb.from('menu_items').update(f).eq('id', id).then(done); },
    deleteItem: function (id) { return sb.from('menu_items').delete().eq('id', id).then(done); },
    approveItem: function (id) { return sb.from('menu_items').update({ approved: true }).eq('id', id).then(done); },

    addStore: function (f) { var c = cleanStore(f); if (!validStore(c)) return badStore(); return sb.from('stores').insert(c).then(done); },
    updateStore: function (id, f) { var c = cleanStore(f); if (!validStore(c)) return badStore(); return sb.from('stores').update(c).eq('id', id).then(done); },
    setMyDiscount: function (storeN, pct) { var s = storeByName(storeN), v = +pct; if (!s || !isFinite(v) || v < 0 || v > 100) return Promise.resolve({ error: 'bad_value' }); return rpc('set_my_discount', { p_store: String(s.id), p_pct: v }, true); },
    updateMyStore: function (storeN, f) { var s = storeByName(storeN); if (!s) return Promise.resolve({ error: 'generic' }); return rpc('update_my_store', { p_store: s.id, p_description: f.description == null ? null : f.description, p_cover: f.cover || null }, true); },
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
