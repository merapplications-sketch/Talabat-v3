/* TALABOT driver — street route on the mission map (batch B, prepared for review; loaded after map-view.js).
   Current leg only: before pickup driver -> restaurant, after pickup driver -> the order pin (the same lat/lng the customer
   chose, stored with the order). Route, distance and duration come from the server proxy (TLB.route -> Edge Function
   «route» -> OpenRouteService); the key never reaches the browser. Until that function is deployed, or when it fails,
   nothing changes: driver A keeps its straight line and its «не дорожный маршрут» label.
   Requests: on task / stage change, then at most every 120 s and only after the driver moved >= 250 m (quota: 2 000 / day).
   The duration is a road-speed estimate (no live traffic); shown as «~N мин», never as a countdown. */
(function () {
  'use strict';
  if (typeof mapUpd !== 'function' || !window.TLB || typeof TLB.route !== 'function') return;
  TLB.addDict({ rRoute: 'По дорогам: {km} км · ~{min} мин', rRouteAttr: 'Маршрут: openrouteservice.org' },
              { rRoute: 'By road: {km} km · ~{min} min', rRouteAttr: 'Route: openrouteservice.org' });
  var MIN_GAP = 120000, MIN_MOVE = 250;
  var cur = null, inflight = false, attr = false;   /* cur = {key, from, to, at, route} */
  function ready() { return !!(window.L && typeof DM !== 'undefined' && DM && DM !== 1 && DM.getContainer); }
  function stageOf(x) { return typeof aTaskStage === 'function' ? aTaskStage(x) : 0; }
  function target(x) {
    if (stageOf(x) >= 3) return x.lat != null && x.lng != null && isFinite(+x.lat) && isFinite(+x.lng) ? [+x.lat, +x.lng] : null;
    return typeof storePt === 'function' ? storePt(x.store) : null;
  }
  function meters(a, b) {
    var R = 6371000, r = function (v) { return v * Math.PI / 180; }, dl = r(b[0] - a[0]), dn = r(b[1] - a[1]);
    var h = Math.sin(dl / 2) * Math.sin(dl / 2) + Math.cos(r(a[0])) * Math.cos(r(b[0])) * Math.sin(dn / 2) * Math.sin(dn / 2);
    return 2 * R * Math.asin(Math.sqrt(h));
  }
  function draw(x) {
    if (!ready()) return;
    if (!DM.__route) DM.__route = L.layerGroup().addTo(DM);
    DM.__route.clearLayers();
    var key = String(x.id) + ':' + stageOf(x);
    if (!cur || cur.key !== key || !cur.route) return;
    /* the real route replaces the straight line that driver.html draws on every mapUpd */
    if (DM.__l) DM.__l.eachLayer(function (l) { if (l instanceof L.Polyline && !(l instanceof L.Polygon)) DM.__l.removeLayer(l); });
    L.polyline(cur.route.coords, { color: '#f1511b', weight: 5, opacity: 0.85, interactive: false, className: 'a-route' }).addTo(DM.__route);
    if (!attr && DM.attributionControl) { DM.attributionControl.addAttribution(t('rRouteAttr')); attr = true; }
    var label = document.getElementById('a-map-state');
    if (label) label.textContent = t('rRoute').replace('{km}', (cur.route.distanceM / 1000).toFixed(1).replace('.', ',')).replace('{min}', Math.max(1, Math.round(cur.route.durationS / 60)));
  }
  function want(x) {
    var to = target(x), from = GEO.lat != null && GEO.lng != null ? [GEO.lat, GEO.lng] : null;
    if (!to || !from || inflight) return;
    var key = String(x.id) + ':' + stageOf(x), now = Date.now();
    if (cur && cur.key === key && (now - cur.at < MIN_GAP || meters(cur.from, from) < MIN_MOVE)) return;
    if (!cur || cur.key !== key) cur = { key: key, from: from, to: to, at: now, route: null };
    inflight = true;
    var ask = { key: key, from: from };
    TLB.route(from, to).then(function (r) {
      inflight = false;
      if (!cur || cur.key !== ask.key) return;          /* the task / stage changed meanwhile: drop the late answer */
      cur.at = Date.now(); cur.from = ask.from;
      if (r) { cur.route = r; var x2 = typeof aTask === 'function' ? aTask() : null; if (x2 && String(x2.id) + ':' + stageOf(x2) === ask.key) draw(x2); }
    }, function () { inflight = false; });
  }
  var inner = mapUpd;
  mapUpd = function (x, force) {
    var res = inner.apply(this, arguments);
    if (x && ready()) { want(x); draw(x); }
    return res;
  };
  window.__routeLayer = { state: function () { return cur ? { key: cur.key, hasRoute: !!cur.route, at: cur.at } : null; } };   /* for checks */
})();
