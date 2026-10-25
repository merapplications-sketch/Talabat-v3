// Only the selected upstream is implemented. Future adapters implement calculate(ctx) -> normalized route.
// No secondary provider / paid fallback. Existing ORS integration is retained in Git history, not called implicitly.
import { validPoint } from './config.js';
export const geoapify = {
  configured: env => !!env.GEOAPIFY_KEY,
  async calculate({ from, to, env, fetch, signal, now }) {
    const url = new URL('https://api.geoapify.com/v1/routing');
    url.search = new URLSearchParams({ waypoints: from.join(',') + '|' + to.join(','), mode: 'drive', lang: 'ru', details: 'instruction_details', apiKey: env.GEOAPIFY_KEY }).toString();
    const r = await fetch(url.toString(), { signal, headers: { Accept: 'application/geo+json' } });
    if (r.status === 429) throw new Error('quota');
    if (r.status === 401 || r.status === 403) throw new Error('provider_denied');
    if (!r.ok) throw new Error('upstream');
    const g = await r.json(), f = g?.features?.[0], p = f?.properties, geom = f?.geometry;
    const lines = geom?.type === 'MultiLineString' ? geom.coordinates : geom?.type === 'LineString' ? [geom.coordinates] : [];
    if (!p || !Number.isFinite(p.distance) || p.distance < 0 || !Number.isFinite(p.time) || p.time < 0 || !lines.length) throw new Error('no_route');
    const coords = [], steps = [];
    lines.forEach((line, leg) => {
      if (!Array.isArray(line) || line.length < 2 || line.some(v => !Array.isArray(v) || !validPoint([v[1], v[0]]))) throw new Error('no_route');
      if(coords.length + line.length > 30000) throw new Error('no_route');
      const offset = coords.length;
      coords.push(...line.map(v => [v[1], v[0]]));
      (p.legs?.[leg]?.steps || []).forEach(s => {
        if (!Number.isInteger(s.from_index) || !Number.isInteger(s.to_index) || s.from_index < 0 || s.to_index < s.from_index || s.to_index >= line.length) throw new Error('no_route');
        if(!Number.isFinite(s.time)||s.time<0||!Number.isFinite(s.distance)||s.distance<0)throw new Error('no_route');
        steps.push({ from: offset + s.from_index, to: offset + s.to_index, distanceM: +s.distance || 0,
          durationS: +s.time || 0, instruction: String(s.instruction?.text || ''), maneuver: String(s.instruction?.type || '') });
      });
    });
    // Do not thin original geometry: maneuver indices must continue to address the same points.
    if (coords.length > 30000 || steps.length > 5000) throw new Error('no_route');
    return { coords, distance_m: Math.round(p.distance), duration_s: Math.round(p.time), steps,
      source: 'geoapify', attribution: 'Powered by Geoapify | © OpenStreetMap contributors', calculated_at: now() };
  },
};
export const providers = Object.freeze({ geoapify });
