/* TALABOT driver — waiting-map provider (technical binding for driver A WAIT-HOME-01).
   Implements the local contract window.TALABOT_WAITING_MAP_UI used by assets/driver-a/driver-a.js.
   - Location: read only through getLocation() (= the existing GEO of driver.html). No second watcher, no location write.
   - Map: the existing Leaflet 1.9.4 + OSM tiles (same CDN, same referrerPolicy as the mission map). One loader, one map per mount.
   - Restaurants: TLB.stores() (active records the app already loads for this account), only those with valid coordinates.
     No geocoding, no midpoint fill-in. «Nearby» has NO radius: no approved rule exists (decision D-W1 pending), so the
     map shows every active restaurant with coordinates and the user's view decides what is near. No ranking, no ETA,
     no order / dispatch meaning.
   - States are from real data only: map loading / ready / error (H8: message + retry in the map area); nearby loading /
     ready — never «empty / none nearby» until D-W1 defines «nearby». onViewChange fires only when one of these states
     changes (never on resize or map movement). */
(function () {
  'use strict';
  var LEAFLET = 'https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js';
  var LEAFLET_CSS = 'https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css';
  var CITY = [38.5598, 68.787];          /* the app's existing default map view (not a location of anybody) */
  var loading = null;                    /* one shared loader promise */

  function loadLeaflet() {
    if (window.L && window.L.map) return Promise.resolve();
    if (loading) return loading;
    loading = new Promise(function (ok, bad) {
      if (!document.querySelector('link[href="' + LEAFLET_CSS + '"]')) {
        var l = document.createElement('link'); l.rel = 'stylesheet'; l.href = LEAFLET_CSS; document.head.appendChild(l);
      }
      /* the mission map (core loader) may already be loading the same script: wait for it instead of adding another */
      var s = document.querySelector('script[src="' + LEAFLET + '"]'), fresh = !s;
      if (fresh) { s = document.createElement('script'); s.src = LEAFLET; }
      /* a failed tag is removed so that «retry» adds a fresh one instead of waiting on a dead tag */
      function drop(e) { clearTimeout(timer); if (s.parentNode) s.parentNode.removeChild(s); bad(e); }
      var timer = setTimeout(function () { drop(new Error('timeout')); }, 20000);
      s.addEventListener('load', function () { clearTimeout(timer); window.L ? ok() : drop(new Error('no L')); });
      s.addEventListener('error', function () { drop(new Error('load')); });
      if (fresh) document.head.appendChild(s);
    }).catch(function (e) { loading = null; throw e; });  /* a later mount may try again (e.g. after the connection returns) */
    return loading;
  }

  function validLL(lat, lng) {
    lat = +lat; lng = +lng;
    return lat !== null && lng !== null && isFinite(lat) && isFinite(lng) &&
      lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180 && !(lat === 0 && lng === 0);
  }
  function stores() {
    var all = [];
    try { all = (window.TLB && TLB.stores) ? TLB.stores() : []; } catch (e) { all = []; }
    return all.filter(function (s) { return s && s.is_active !== false && s.lat != null && s.lng != null && validLL(s.lat, s.lng); });
  }
  function storesLoaded() { try { return !!(window.TLB && TLB.me && TLB.me()); } catch (e) { return false; } }
  function icon(name, size) { try { return typeof ico === 'function' ? ico(name, size) : ''; } catch (e) { return ''; } }   /* driver.html's ico is a top-level const, not a window property */
  function esc(v) { return String(v == null ? '' : v).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }

  /* H8 texts (provider's own; the screen's other texts stay in driver-a.js) */
  try { TLB.addDict({ wMapFail: 'Карта не загрузилась', wMapFailHint: 'Заказы продолжают приходить. Проверьте интернет и повторите.', wMapRetry: 'Повторить', wMapPartial: 'Часть карты не загрузилась', wMapPartialRetry: 'Обновить' },
                    { wMapFail: 'The map did not load', wMapFailHint: 'Orders keep arriving. Check the internet and try again.', wMapRetry: 'Retry', wMapPartial: 'Part of the map did not load', wMapPartialRetry: 'Reload' }); } catch (e) {}
  function tx(k) { try { return typeof t === 'function' ? t(k) : k; } catch (e) { return k; } }
  /* shared state read by the waiting screen (read() is called on every render: cheap, no side effects) */
  var S = { map: 'loading', nearby: 'loading', mounted: false };

  function read() {
    if (!S.mounted) return { map: 'loading', nearby: 'loading' };
    return { map: S.map, nearby: S.nearby };
  }

  function mount(node, opts) {
    opts = opts || {};
    var getLocation = typeof opts.getLocation === 'function' ? opts.getLocation : function () { return {}; };
    var onViewChange = typeof opts.onViewChange === 'function' ? opts.onViewChange : function () {};
    var map = null, layerStores = null, meMarker = null, accCircle = null, dead = false;
    var storesKey = '', placedWithDriver = false, tilesOk = 0, tilesBad = 0, fitTimer = 0;
    /* view mode: 'fit' = driver + restaurants fitted into the uncovered strip (start); 'me' = «my location» pressed;
       'free' = the user moved the map (nothing moves it back except «my location») */
    var mode = 'fit';
    var visible = { top: 0, bottom: 0 }, sizeFrame = 0, notifyQueued = false;

    S.mounted = true; S.map = 'loading'; S.nearby = 'loading';
    node.replaceChildren();
    var box = document.createElement('div'); box.className = 'w-leaflet'; box.style.cssText = 'position:absolute;inset:0';
    node.appendChild(box);

    function setState(k, v) {
      if (S[k] === v) return;
      S[k] = v;
      if (!notifyQueued) { notifyQueued = true; Promise.resolve().then(function () { notifyQueued = false; if (!dead) onViewChange(); }); }
    }
    function loc() {
      var g = {}; try { g = getLocation() || {}; } catch (e) { g = {}; }
      return { ok: g.state === 'ok' && validLL(g.lat, g.lng), lat: +g.lat, lng: +g.lng, acc: +g.accuracy || 0 };
    }
    /* centre a point in the uncovered strip between the header and the panel (not behind the panel) */
    function strip() {
      var size = map.getSize(), r = node.getBoundingClientRect();
      var top = Math.max(0, visible.top - r.top), bottom = visible.bottom > 0 ? Math.min(size.y, visible.bottom - r.top) : size.y;
      if (bottom - top < 80) { top = 0; bottom = size.y; }
      return { top: top, bottom: bottom, size: size };
    }
    function centreOn(ll, zoom) {
      if (!map) return;
      var z = zoom == null ? map.getZoom() : zoom, st = strip(), size = st.size, top = st.top, bottom = st.bottom;
      var dy = size.y / 2 - (top + bottom) / 2;
      var p = map.project(ll, z).add([0, dy]);
      map.setView(map.unproject(p, z), z, { animate: false });
    }
    /* fit the real points (driver if known + restaurants with coordinates) into the uncovered strip; no radius is applied */
    function fitView() {
      if (!map) return;
      var l = loc(), pts = stores().map(function (s) { return [+s.lat, +s.lng]; });
      if (l.ok) pts.push([l.lat, l.lng]);
      if (!pts.length) return;
      if (pts.length === 1) { centreOn(pts[0], 15); return; }
      var st = strip();
      map.fitBounds(pts, { paddingTopLeft: [32, st.top + 32], paddingBottomRight: [32, st.size.y - st.bottom + 32], maxZoom: 16, animate: false });
    }
    function placeView() { if (mode === 'fit') fitView(); else if (mode === 'me') { var l = loc(); if (l.ok) centreOn([l.lat, l.lng]); } }
    function drawStores() {
      var list = stores(), key = list.map(function (s) { return s.id + ':' + (+s.lat) + ',' + (+s.lng) + ':' + (s.is_open ? 1 : 0); }).join('|');
      if (key !== storesKey && layerStores) {
        storesKey = key; layerStores.clearLayers();
        list.forEach(function (s) {
          var open = s.is_open !== false;
          L.marker([+s.lat, +s.lng], {
            title: s.name || '', alt: s.name || '', keyboard: false,
            icon: L.divIcon({ className: '', html: '<div class="dmk" style="background:' + (open ? '#f1511b' : '#9aa0aa') + '">' + icon('store', 15) + '</div>', iconSize: [30, 30], iconAnchor: [15, 15] })
          }).bindTooltip(esc(s.name || ''), { direction: 'top', offset: [0, -14] }).addTo(layerStores);
        });
      }
      return list;
    }
    function drawMe() {
      var l = loc();
      if (!l.ok) { if (meMarker) { meMarker.remove(); meMarker = null; } if (accCircle) { accCircle.remove(); accCircle = null; } return l; }
      var ll = [l.lat, l.lng];
      if (!meMarker) meMarker = L.marker(ll, { interactive: false, keyboard: false, zIndexOffset: 1000, icon: L.divIcon({ className: '', html: '<div class="dmk me"></div>', iconSize: [20, 20], iconAnchor: [10, 10] }) }).addTo(map);
      else meMarker.setLatLng(ll);
      if (l.acc > 0) {
        if (!accCircle) accCircle = L.circle(ll, { className: 'w-acc', radius: l.acc, color: '#1d4ed8', weight: 1, opacity: .4, fillOpacity: .08, interactive: false }).addTo(map);
        else { accCircle.setLatLng(ll); accCircle.setRadius(l.acc); }
      } else if (accCircle) { accCircle.remove(); accCircle = null; }
      return l;
    }
    function refresh() {
      if (dead) return;
      /* nearby does not depend on the map library: «empty» only after a valid location AND the restaurant list was read */
      /* until D-W1 (what «nearby» means) the list has no radius, so it is never reported as «empty / none nearby» */
      var l0 = loc();
      setState('nearby', !l0.ok || !storesLoaded() ? 'loading' : 'ready');
      if (!map) return;
      drawStores(); var l = drawMe();
      if (l.ok && !placedWithDriver) { placedWithDriver = true; if (mode === 'fit') fitView(); }   /* first real reading: include the driver once */
    }

    /* H8: map failure message + retry, inside the map area only (offers, panel and shift are not touched).
       Two levels: TOTAL = nothing could be drawn (Leaflet failed, or no tile loaded and >=4 failed) -> message over the map
       strip; PARTIAL = some tiles failed while others loaded -> small notice at the top, the loaded part stays visible.
       Shown / hidden with style.display (the [hidden] attribute loses against an inline display without a reset sheet). */
    var fail = document.createElement('div'), part = document.createElement('div'), tiles = null, failOn = false, partOn = false, bad = {};
    fail.className = 'w-map-fail'; fail.setAttribute('role', 'status');
    fail.style.cssText = 'position:absolute;left:0;right:0;display:none;flex-direction:column;align-items:center;justify-content:center;gap:8px;padding:16px 24px;text-align:center;z-index:500;background:#E8EFEB;color:#5b6676;font-size:13px;line-height:18px';
    fail.innerHTML = '<span aria-hidden="true">' + icon('pin', 28) + '</span><b style="color:#17243c;font-size:15px;line-height:20px">' + esc(tx('wMapFail')) + '</b><span>' + esc(tx('wMapFailHint')) + '</span>' +
      '<button type="button" class="w-map-retry" style="min-height:44px;min-width:120px;margin-top:4px;padding:10px 20px;border:0;border-radius:999px;background:#f1511b;color:#fff;font-weight:700;font-size:14px;cursor:pointer">' + esc(tx('wMapRetry')) + '</button>';
    part.className = 'w-map-partial'; part.setAttribute('role', 'status');
    part.style.cssText = 'position:absolute;left:50%;transform:translateX(-50%);display:none;align-items:center;gap:6px;max-width:calc(100% - 24px);padding:0 4px 0 12px;z-index:500;background:#fff;border:1px solid #e3e7ee;border-radius:999px;box-shadow:0 2px 10px #17243c1f;color:#5b6676;font-size:12px;line-height:16px;white-space:nowrap';
    part.innerHTML = '<span style="overflow:hidden;text-overflow:ellipsis">' + esc(tx('wMapPartial')) + '</span><button type="button" class="w-map-partial-retry" style="min-height:44px;padding:0 10px;border:0;background:none;color:#f1511b;font-weight:700;font-size:12px;cursor:pointer">' + esc(tx('wMapPartialRetry')) + '</button>';
    node.appendChild(fail); node.appendChild(part);
    fail.querySelector('button').addEventListener('click', function () { retry(); });
    part.querySelector('button').addEventListener('click', function () { retry(); });
    function stripPx() {
      var r = node.getBoundingClientRect(), top = Math.max(0, visible.top - r.top), bottom = visible.bottom > 0 ? Math.min(r.height, visible.bottom - r.top) : r.height;
      if (bottom - top < 160) { top = 0; bottom = r.height; }
      return { top: top, bottom: bottom };
    }
    function placeFail() { var st = stripPx(); fail.style.top = st.top + 'px'; fail.style.height = (st.bottom - st.top) + 'px'; part.style.top = (st.top + 30) + 'px';   /* below the OSM attribution line */ }
    function showFail(on) { failOn = !!on; fail.style.display = on ? 'flex' : 'none'; if (on) { showPart(false); placeFail(); } }
    function showPart(on) { partOn = !!on && !failOn; part.style.display = partOn ? 'flex' : 'none'; if (partOn) placeFail(); }
    function badCount() { var n = 0; for (var k in bad) n++; return n; }
    function failed() { if (dead) return; setState('map', 'error'); showFail(true); refresh(); }
    function retry() {
      if (dead) return;
      showFail(false); showPart(false); bad = {};
      if (map && tiles) { if (S.map === 'error') setState('map', 'loading'); tilesOk = 0; tilesBad = 0; tiles.redraw(); }
      else { setState('map', 'loading'); start(); }
    }
    function onOnline() { if (S.map === 'error') retry(); }   /* the connection came back: try once by itself */
    window.addEventListener('online', onOnline);

    function start() { loadLeaflet().then(function () {
      if (dead) return;
      map = L.map(box, { zoomControl: false, attributionControl: false });
      L.control.attribution({ position: 'topright', prefix: false }).addTo(map);
      tiles = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '© OpenStreetMap', referrerPolicy: 'strict-origin-when-cross-origin' });
      var key = function (e) { return e && e.coords ? e.coords.z + '/' + e.coords.x + '/' + e.coords.y : ''; };
      tiles.on('tileload', function (e) {
        tilesOk++; delete bad[key(e)];
        if (S.map !== 'ready') setState('map', 'ready');
        if (failOn) showFail(false);                       /* recovered: the full message goes away */
        if (partOn && !badCount()) showPart(false);
      });
      tiles.on('tileerror', function (e) {
        tilesBad++; bad[key(e)] = 1;
        if (!tilesOk && tilesBad >= 4) { if (!failOn) failed(); }   /* nothing could be drawn: total failure */
      });
      tiles.on('tileunload', function (e) { delete bad[key(e)]; if (partOn && !badCount()) showPart(false); });
      /* all tiles of the view settled: some loaded + some failed = partial notice; none failed = clear */
      tiles.on('load', function () { if (!failOn) showPart(tilesOk > 0 && badCount() > 0); });
      tiles.addTo(map);
      layerStores = L.layerGroup().addTo(map);
      map.on('dragstart', function () { mode = 'free'; });   /* the user's own view is kept; «my location» brings the driver back */
      var l = loc();
      map.setView(l.ok ? [l.lat, l.lng] : CITY, l.ok ? 15 : 13);
      placedWithDriver = l.ok; fitView(); refresh();
    }, failed); }
    start();

    return {
      update: function () { refresh(); },
      resize: function (v) {
        if (v) { visible.top = +v.visibleTop || 0; visible.bottom = +v.visibleBottom || 0; }
        if (failOn || partOn) placeFail();
        if (!map || sizeFrame) return;
        sizeFrame = requestAnimationFrame(function () { sizeFrame = 0; if (map && !dead) map.invalidateSize({ pan: false }); });
        /* panel moved (snap, offer arrived, offline strip): re-place the view once it settles, never during a drag */
        clearTimeout(fitTimer); fitTimer = setTimeout(function () { if (map && !dead && !window.__drag) placeView(); }, 220);
      },
      recenter: function () {
        var l = loc(); if (!map || !l.ok) return;
        mode = 'me'; centreOn([l.lat, l.lng], Math.max(map.getZoom(), 16));   /* street level: the accuracy circle is readable around the marker */
      },
      destroy: function () {
        dead = true; if (sizeFrame) cancelAnimationFrame(sizeFrame); clearTimeout(fitTimer); window.removeEventListener('online', onOnline);
        if (map) { try { map.remove(); } catch (e) {} }
        map = null; meMarker = null; accCircle = null; layerStores = null;
        node.replaceChildren(); S.mounted = false; S.map = 'loading'; S.nearby = 'loading';
      }
    };
  }

  /* a provider already present (test harness / review export) is kept; in the app nothing defines one before this file */
  if (!window.TALABOT_WAITING_MAP_UI) window.TALABOT_WAITING_MAP_UI = { read: read, mount: mount };
})();
