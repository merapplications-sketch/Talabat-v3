// One server-owned policy; no navigation provider key or editable policy in browser storage.
export const EXTERNAL_IDS = ['yandex', '2gis', 'google'];
export function navigationConfig(env) {
  let x = {}; try { x = JSON.parse(env.NAVIGATION_CONFIG || '{}'); } catch { return { invalid: true, internal: false, external: false, providers: [], provider: 'none', revision: 'invalid' }; }
  const bounded = (v, def, lo, hi) => Number.isFinite(v) ? Math.max(lo, Math.min(hi, v)) : def;
  const providers = EXTERNAL_IDS.filter(id => !Array.isArray(x.externalProviders) || x.externalProviders.includes(id));
  return {
    revision: String(x.revision || 'navigation-v1'), provider: String(x.provider || 'geoapify'),
    internal: x.internal === true, external: x.external !== false, providers,
    defaultExternal: providers.includes(x.defaultExternal) ? x.defaultExternal : providers[0],
    dailyCredits: bounded(x.dailyCredits, 2400, 0, 3000), accountCredits: 3000,
    // Credits per request are computed (routeCredits), not a fixed reservation. detailsCredits = conservative surcharge for
    // `details=instruction_details`, whose cost Geoapify does not publish (0..10, default 1). Old `reservationCredits` is ignored.
    detailsCredits: bounded(x.detailsCredits, 1, 0, 10), rps: bounded(x.rps, 4, 1, 4),
    maxStraightKm: bounded(x.maxStraightKm, 60, 1, 60), cacheMs: 60000, timeoutMs: 7000,
    configTtlMs: 30000, refreshMs: 120000, deviationM: 60, deviationHoldMs: 5000, gpsMaxAgeMs: 30000,
  };
}
export function publicConfig(c, reason = null) {
  return { revision: c.revision, provider: c.provider, internal: c.internal && !c.invalid,
    external: c.external, providers: c.providers, defaultExternal: c.defaultExternal,
    configTtlMs: c.configTtlMs || 30000, refreshMs: c.refreshMs || 120000,
    deviationM: c.deviationM || 60, deviationHoldMs: c.deviationHoldMs || 5000, gpsMaxAgeMs: c.gpsMaxAgeMs || 30000,
    mode: c.internal && !reason ? 'internal' : 'tracking', reason };
}
export function validPoint(p) {
  return Array.isArray(p) && p.length === 2 && p.every(v => typeof v === 'number' && Number.isFinite(v)) &&
    Math.abs(p[0]) <= 90 && Math.abs(p[1]) <= 180 && !(p[0] === 0 && p[1] === 0);
}
export function externalLinks(c, to) {
  if (!c.external || !validPoint(to)) return [];
  const ll = to.join(','), xy = [to[1], to[0]].join(',');
  // Provider-documented coordinates: Yandex/Google lat,lng; 2GIS lng,lat. Never text search.
  const urls = {
    yandex: { name: 'Yandex Maps', app: 'yandexmaps://maps.yandex.ru/?rtext=' + encodeURIComponent('~' + ll) + '&rtt=auto', web: 'https://yandex.ru/maps/?rtext=' + encodeURIComponent('~' + ll) + '&rtt=auto' },
    '2gis': { name: '2GIS', app: 'https://2gis.ru/directions/tab/car/points/|' + xy, web: 'https://2gis.ru/directions/tab/car/points/|' + xy },
    google: { name: 'Google Maps', app: 'https://www.google.com/maps/dir/?api=1&destination=' + encodeURIComponent(ll) + '&travelmode=driving&dir_action=navigate', web: 'https://www.google.com/maps/dir/?api=1&destination=' + encodeURIComponent(ll) + '&travelmode=driving&dir_action=navigate' },
  };
  return c.providers.map(id => ({ id, ...urls[id] }));
}

// Geoapify Routing credits (pricing-details): credits = waypoints − 1, plus 1 credit for each 500 km of result route length
// when the route is longer than 500 km (counted conservatively as ceil(km / 500)), plus the conservative details surcharge.
// Before the request the length is unknown: the straight-line cap (maxStraightKm <= 60) makes the length surcharge 0 for the
// reservation; after the response the real length is checked and any excess is settled in the ledger (never refunded).
export function routeCredits({ waypoints = 2, distanceM = 0, detailsCredits = 1 } = {}) {
  const km = Math.max(0, +distanceM || 0) / 1000;
  return Math.max(1, (waypoints | 0) - 1) + (km > 500 ? Math.ceil(km / 500) : 0) + Math.max(0, detailsCredits | 0);
}
