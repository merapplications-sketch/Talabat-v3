/* AH-06: presentation around original core auth nodes; no authentication/data API calls. */
(function () {
  'use strict';
  if (window.TALABOT_LOGIN_BANNERS) return;

  const ROLES = ['customer', 'driver', 'merchant', 'admin'];
  const role = ROLES.find(name => location.pathname.endsWith('/' + name + '.html')) || '';
  const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const words = {
    ru: {
      offers: 'Предложения Талабот', previous: 'Предыдущее предложение', next: 'Следующее предложение',
      view: 'Смотреть',
      pending: 'Войдите, чтобы открыть предложение.', unavailable: 'Это предложение больше недоступно.',
      error: 'Пока показываем подборку Талабот.', empty: 'Новые предложения — скоро',
      emptySub: 'А пока войдите в свой аккаунт.', loading: 'Подбираем предложения',
      free: ['Доставка\nбесплатно', 'Найдите рестораны с бесплатной доставкой.', 'Открыть рестораны'],
      happy: ['Счастливые\nчасы', 'Самое время открыть актуальные предложения.', 'Смотреть предложения'],
      dineout: ['Откройте\nDineOut', 'Любимые рестораны. Новые поводы встретиться.', 'Открыть DineOut']
    },
    en: {
      offers: 'Talabot offers', previous: 'Previous offer', next: 'Next offer',
      view: 'View',
      pending: 'Sign in to open this offer.', unavailable: 'This offer is no longer available.',
      error: 'Showing Talabot highlights for now.', empty: 'More good things soon',
      emptySub: 'In the meantime, sign in to your account.', loading: 'Finding your next favourite',
      free: ['Good food.\nFree delivery.', 'Find restaurants with free delivery.', 'Explore restaurants'],
      happy: ['Make it\nHappy Hours.', 'A good time to explore the latest offers.', 'Explore offers'],
      dineout: ['Discover\nDineOut', 'Favourite restaurants. More reasons to meet.', 'Explore DineOut']
    },
    tg: {
      offers: 'Пешниҳодҳои Талабот', previous: 'Пешниҳоди пешина', next: 'Пешниҳоди навбатӣ',
      view: 'Дидан',
      pending: 'Барои кушодани пешниҳод ворид шавед.', unavailable: 'Ин пешниҳод дигар дастрас нест.',
      error: 'Ҳоло интихоби Талаботро нишон медиҳем.', empty: 'Пешниҳодҳои нав — ба зудӣ',
      emptySub: 'Ҳоло ба ҳисоби худ ворид шавед.', loading: 'Пешниҳодҳоро интихоб мекунем',
      free: ['Расондан\nройгон', 'Тарабхонаҳоро бо расондани ройгон ёбед.', 'Кушодани тарабхонаҳо'],
      happy: ['Соатҳои\nхушбахтӣ', 'Вақти дидани пешниҳодҳои ҷорӣ расид.', 'Дидани пешниҳодҳо'],
      dineout: ['DineOut-ро\nкашф кунед', 'Тарабхонаҳои дӯстдошта. Баҳонаҳои нав барои вохӯрӣ.', 'Кушодани DineOut']
    }
  };
  const language = () => ['ru', 'en', 'tg'].includes(window.TLB?.lang()) ? TLB.lang() : 'ru';
  const copy = () => words[language()];
  const helpers = () => window.TALABOT_BANNERS;
  let source = {mode: 'fallback', banners: [], settings: {}};
  let request = null, generation = 0, scene = null, pending = null, readyRole = '';
  let frame = 0, queued = false, deadlineTimer = 0, restingHeight = window.innerHeight;
  const failedImages = new Set();

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }
  function safeURL(value) {
    return helpers()?.safeLink(value) || '';
  }
  function fallbackEntries() {
    const lang = language(), text = copy();
    const staff = ['driver', 'merchant', 'admin'].includes(role);
    const customerEntry = {
      ru: ['Предложения в приложении клиента. Нужен аккаунт клиента.', 'Открыть приложение клиента'],
      en: ['Offers open in the customer app. A customer account is required.', 'Open customer app'],
      tg: ['Пешниҳодҳо дар барномаи муштарӣ. Ҳисоби муштарӣ лозим аст.', 'Кушодани барномаи муштарӣ']
    }[lang];
    return ['free', 'happy', 'dineout'].map(kind => {
      const url = new URL('customer.html', location.href);
      url.searchParams.set('login_offer', kind); url.searchParams.set('lang', lang);
      return {id: 'ah06-fallback-' + kind, kind: 'fallback', theme: kind, href: url.href,
        access: staff ? 'public' : 'after_auth', headline: text[kind][0],
        subtitle: staff ? customerEntry[0] : text[kind][1], label: text.view,
        image: kind === 'dineout' ? 'assets/customer-c/dineout-header-' + (lang === 'en' ? 'en' : 'ru') + '.webp' :
          'assets/3d/' + (kind === 'free' ? 'motor-scooter' : 'hamburger') + '.webp'};
    });
  }
  function entries() {
    if (source.mode === 'loading') return [];
    if (source.mode !== 'connected') return fallbackEntries().filter(item => !failedImages.has(item.image));
    const api = helpers(), lang = language();
    if (!api) return [];
    const ids = new Set();
    return api.list(source.banners, 'login', source.settings).flatMap((row, index) => {
      const cfg = api.config(row), href = cfg.action === 'link' ? safeURL(cfg.url) : '';
      const image = api.image(row, lang), id = String(row.id ?? '');
      if (!id || ids.has(id) || !href || !image || failedImages.has(image)) return [];
      ids.add(id);
      return [{id, kind: 'connected', theme: ['free', 'happy', 'dineout'][index % 3], href,
        access: api.loginAccess(row), headline: api.headline(row, lang) || String(row.title || ''),
        subtitle: api.subtitle(row, lang), label: api.label(row, lang) || copy().view, image}];
    });
  }
  function duration() {
    const seconds = Number(source.settings.banner_rotation_login_seconds);
    return source.mode === 'connected' && Number.isFinite(seconds) && seconds >= 1 && seconds <= 60 ?
      helpers().rotationMs('login', source.settings) : 5000;
  }
  function armDeadline() {
    clearTimeout(deadlineTimer); deadlineTimer = 0;
    if (source.mode !== 'connected') return;
    const now = Date.now(), dates = source.banners.flatMap(row => [Date.parse(row.starts_at), Date.parse(row.ends_at)])
      .filter(time => Number.isFinite(time) && time > now);
    if (dates.length) deadlineTimer = setTimeout(() => {syncStories(); armDeadline();}, Math.min(2147483647, Math.min(...dates) - now + 1));
  }

  function consumePending() {
    if (!pending || readyRole !== role || pending.role !== role || source.mode === 'loading') return false;
    const intent = pending; pending = null;
    const current = entries().find(item => item.id === intent.id && item.kind === intent.kind);
    const url = current && safeURL(current.href);
    if (!url || (current.kind !== 'fallback' && url !== intent.href)) return false;
    location.assign(url);
    return true;
  }
  function activate(id) {
    const item = entries().find(entry => entry.id === id);
    const url = item && safeURL(item.href);
    if (!url) {if (scene) scene.feedback.textContent = copy().unavailable; syncStories(); return;}
    if (item.access === 'public') {location.assign(url); return;}
    pending = {role, id: item.id, kind: item.kind, href: url};
    if (!consumePending() && scene) scene.feedback.textContent = copy().pending;
  }
  function ready(appRole) {
    if (!role || appRole !== role || !ROLES.includes(appRole)) return false;
    readyRole = appRole;
    return consumePending();
  }
  async function connect(provider) {
    const version = ++generation;
    request?.abort(); request = null;
    if (provider == null) {
      source = {mode: 'fallback', banners: [], settings: {}};
      failedImages.clear(); armDeadline(); syncStories(); consumePending(); return true;
    }
    if (typeof provider !== 'function') throw new TypeError('AH-06 connect expects a provider function');
    const controller = new AbortController(); request = controller;
    source = {mode: 'loading', banners: [], settings: {}};
    armDeadline(); syncStories();
    try {
      const feed = await provider({signal: controller.signal});
      if (controller.signal.aborted || version !== generation) return false;
      if (!feed || feed.version !== 1 || !Array.isArray(feed.banners)) throw new TypeError('Invalid login banner feed');
      source = {mode: 'connected', banners: feed.banners.filter(row => row && typeof row === 'object'),
        settings: feed.settings && typeof feed.settings === 'object' && !Array.isArray(feed.settings) ? feed.settings : {}};
      failedImages.clear(); armDeadline(); syncStories(); consumePending(); return true;
    } catch (error) {
      if (controller.signal.aborted || version !== generation) return false;
      source = {mode: 'error', banners: [], settings: {}};
      armDeadline(); syncStories(); consumePending(); return false;
    } finally {if (request === controller) request = null;}
  }

  function canRun() {
    return scene && scene.root.isConnected && scene.items.length > 1 && !motion.matches &&
      !document.hidden && !scene.pointers.size && !scene.stage.contains(document.activeElement);
  }
  function progress() {
    if (!scene) return;
    const fraction = Math.min(1, scene.elapsed / duration());
    [...scene.bars.children].forEach((bar, index) => {
      bar.firstElementChild.style.transform = 'scaleX(' + (index < scene.index ? 1 : index === scene.index ? fraction : 0) + ')';
    });
  }
  function animate(time) {
    frame = 0;
    if (!canRun()) return;
    if (scene.lastAt) scene.elapsed += Math.max(0, time - scene.lastAt);
    scene.lastAt = time;
    if (scene.elapsed >= duration()) select(scene.index + 1);
    progress();
    if (canRun() && !frame) frame = requestAnimationFrame(animate);
  }
  function runClock() {
    if (frame) cancelAnimationFrame(frame);
    frame = 0;
    if (scene) scene.lastAt = 0;
    if (canRun()) frame = requestAnimationFrame(animate);
  }
  function select(index) {
    if (!scene?.items.length) return;
    scene.index = (index + scene.items.length) % scene.items.length;
    scene.elapsed = 0; scene.lastAt = 0;
    paintActive(); runClock();
  }
  function paintActive() {
    if (!scene) return;
    const active = scene.items[scene.index];
    scene.section.dataset.activeId = active?.id || '';
    scene.section.dataset.theme = active?.theme || 'free';
    scene.section.dataset.managed = String(active?.kind === 'connected');
    [...scene.stage.children].forEach((slide, index) => {
      const on = index === scene.index;
      slide.classList.toggle('is-active', on); slide.setAttribute('aria-hidden', String(!on)); slide.inert = !on;
    });
    progress();
  }
  function slideFor(item) {
    const slide = element('article', 'ah06-slide ah06-slide--' + item.theme);
    slide.dataset.bannerId = item.id;
    if (item.kind === 'connected') slide.classList.add('ah06-slide--managed');
    const text = element('div', 'ah06-copy');
    text.append(element('h2', 'ah06-headline', item.headline), element('p', 'ah06-subtitle', item.subtitle));
    const art = element('div', 'ah06-art'), image = element('img');
    image.src = item.image; image.alt = ''; image.draggable = false; image.decoding = 'async';
    image.addEventListener('error', () => {failedImages.add(item.image); syncStories();}, {once: true});
    art.append(image);
    const button = element('button', 'ah06-cta', item.label); button.type = 'button'; button.dataset.bannerId = item.id;
    slide.append(text, art, button);
    return slide;
  }
  function syncStories() {
    if (!scene) return;
    const items = entries(), mode = source.mode === 'connected' && !items.length ? 'empty' : source.mode;
    const signature = JSON.stringify([mode, language(), duration(), items]);
    if (signature === scene.signature) return;
    const activeId = scene.items[scene.index]?.id;
    scene.signature = signature; scene.items = items;
    scene.index = Math.max(0, items.findIndex(item => item.id === activeId));
    scene.section.dataset.mode = mode; scene.section.setAttribute('aria-label', copy().offers);
    scene.previous.setAttribute('aria-label', copy().previous); scene.next.setAttribute('aria-label', copy().next);
    scene.stage.replaceChildren(...items.map(slideFor));
    scene.bars.replaceChildren(...items.map(item => {
      const bar = element('span', 'ah06-progress-step'); bar.dataset.bannerId = item.id; bar.append(element('i')); return bar;
    }));
    scene.previous.hidden = scene.next.hidden = items.length < 2;
    scene.bars.hidden = !items.length;
    scene.empty.hidden = !!items.length;
    scene.empty.firstElementChild.textContent = mode === 'loading' ? copy().loading : copy().empty;
    scene.empty.lastElementChild.textContent = copy().emptySub;
    scene.note.textContent = mode === 'error' ? copy().error : '';
    scene.note.hidden = mode !== 'error';
    scene.feedback.textContent = pending ? copy().pending : '';
    scene.elapsed = activeId && items.some(item => item.id === activeId) ? Math.min(scene.elapsed, duration()) : 0;
    paintActive(); runClock();
  }
  function buildScene(root) {
    const section = element('section', 'ah06-stories'); section.setAttribute('aria-roledescription', 'carousel');
    const bars = element('div', 'ah06-progress'); bars.setAttribute('aria-hidden', 'true');
    const stage = element('div', 'ah06-stage');
    const buttons = ['previous', 'next'].map(action => {
      const button = element('button', 'ah06-edge'); button.type = 'button';
      button.dataset.ah06Action = action === 'previous' ? 'prev' : action; return button;
    });
    const empty = element('div', 'ah06-empty'); empty.append(element('h2'), element('p'));
    const note = element('p', 'ah06-feed-note'), feedback = element('p', 'ah06-feedback'); feedback.setAttribute('role', 'status');
    section.append(stage, empty, bars, ...buttons, note, feedback);
    const result = {root, card: null, section, bars, stage, empty, note, feedback,
      previous: buttons[0], next: buttons[1], items: [], index: 0, elapsed: 0, lastAt: 0,
      keyboard: false, pointers: new Map(), multiPointer: false, signature: '', controller: new AbortController(), suppressClickUntil: 0};
    const signal = result.controller.signal;
    section.addEventListener('click', event => {
      const button = event.target.closest('button'); if (!button) return;
      if (performance.now() < result.suppressClickUntil) {event.preventDefault(); return;}
      const action = button.dataset.ah06Action;
      if (action) select(result.index + (action === 'next' ? 1 : -1));
      else if (button.dataset.bannerId) activate(button.dataset.bannerId);
    }, {signal});
    section.addEventListener('pointerdown', event => {
      if (event.button !== 0) return;
      result.pointers.set(event.pointerId, {x: event.clientX, y: event.clientY});
      if (result.pointers.size > 1) result.multiPointer = true;
      runClock();
    }, {passive: true, signal});
    const release = event => {
      const start = result.pointers.get(event.pointerId); if (!start) return;
      result.pointers.delete(event.pointerId);
      const dx = event.clientX - start.x, dy = event.clientY - start.y;
      if (!result.multiPointer && event.type === 'pointerup' && Math.abs(dx) > 42 && Math.abs(dx) > Math.abs(dy) * 1.25) {
        result.suppressClickUntil = performance.now() + 350; select(result.index + (dx < 0 ? 1 : -1));
      }
      if (!result.pointers.size) result.multiPointer = false;
      runClock();
    };
    window.addEventListener('pointerup', release, {passive: true, signal});
    window.addEventListener('pointercancel', release, {passive: true, signal});
    window.addEventListener('blur', () => {result.pointers.clear(); runClock();}, {signal});
    section.addEventListener('focusin', runClock, {signal});
    section.addEventListener('focusout', () => queueMicrotask(runClock), {signal});
    return result;
  }
  function viewport() {
    if (!scene) return;
    const vv = window.visualViewport, height = vv?.height || innerHeight;
    const input = scene.root.contains(document.activeElement) && /^(INPUT|TEXTAREA)$/.test(document.activeElement?.tagName);
    if (input && height < restingHeight * .78) scene.keyboard = true;
    // Blurring an input can precede pointerup on Submit. Keep the compact
    // layout until the viewport actually recovers, so the button cannot move
    // away between pointerdown and click while the keyboard is still present.
    if (scene.keyboard) {
      if (height >= restingHeight * .9) {scene.keyboard = false; restingHeight = height;}
    } else if (!input) restingHeight = height;
    scene.root.style.setProperty('--ah06-vh', height + 'px');
    scene.root.style.setProperty('--ah06-vtop', (vv?.offsetTop || 0) + 'px');
    scene.root.toggleAttribute('data-ah06-keyboard', scene.keyboard);
  }
  function destroyScene() {
    if (!scene) return;
    if (frame) cancelAnimationFrame(frame); frame = 0;
    scene.controller.abort(); scene.section.remove(); scene.root.classList.remove('ah06-auth');
    scene.root.style.removeProperty('--ah06-vh'); scene.root.style.removeProperty('--ah06-vtop');
    scene.root.removeAttribute('data-ah06-keyboard'); scene = null;
  }
  function reconcile() {
    queued = false;
    const root = document.getElementById('tlb-ov'), email = root?.querySelector('#tlb-em'), password = root?.querySelector('#tlb-pw');
    if (!root || !email || !password || !window.TALABOT_BRAND?.pill) {destroyScene(); return;}
    let card = email.parentElement;
    while (card && card.parentElement !== root) card = card.parentElement;
    if (!card || !card.contains(password)) return;
    if (scene && scene.root !== root) destroyScene();
    if (!scene) scene = buildScene(root);
    root.classList.add('ah06-auth');
    for (const child of root.children) {
      if (child !== card && child !== scene.section &&
          (child.classList.contains('a-auth-brand') || child.style.textAlign === 'center')) child.classList.add('ah06-legacy-brand');
    }
    if (scene.card !== card) {
      // A newly displayed core login is a new authentication attempt. A prior
      // successful callback must never authorize this screen's deferred CTA.
      readyRole = '';
      scene.card = card; card.classList.add('ah06-sheet');
      const slot = element('div', 'ah06-brand-slot'); slot.append(TALABOT_BRAND.pill('ah06-brand-pill')); card.prepend(slot);
    }
    if (scene.section.parentElement !== root) root.insertBefore(scene.section, card);
    syncStories(); viewport();
  }
  function queueReconcile() {
    if (!queued) {queued = true; queueMicrotask(reconcile);}
  }
  const observer = new MutationObserver(records => {
    if (records.some(record => record.target === document.body || record.target.id === 'tlb-ov' ||
        [...record.addedNodes, ...record.removedNodes].some(node => node.nodeType === 1 && node.id === 'tlb-ov'))) queueReconcile();
  });
  observer.observe(document.body, {childList: true, subtree: true});
  TLB.on(() => {syncStories(); queueReconcile();});
  document.addEventListener('visibilitychange', () => {if (scene) scene.pointers.clear(); runClock();});
  document.addEventListener('focusin', viewport); document.addEventListener('focusout', () => queueMicrotask(viewport));
  window.addEventListener('resize', viewport, {passive: true});
  window.visualViewport?.addEventListener('resize', viewport, {passive: true});
  window.visualViewport?.addEventListener('scroll', viewport, {passive: true});
  motion.addEventListener('change', runClock);
  window.TALABOT_LOGIN_BANNERS = Object.freeze({connect, ready});
  reconcile();
}());
