/* Grip drag DIAGNOSTICS only (31 Oct) — loaded by talabat-core.js when the page address contains ?debug=grip.
   Observes, never changes: passive capture listeners, an overlay with pointer-events:none. No drag, map, order or account
   logic is touched. Purpose: an iPhone screenshot that shows which events Safari delivers to the grip during a drag. */
(function () {
  'use strict';
  if (window.__gripDebug) return; window.__gripDebug = true;
  var box = document.createElement('div'), log = [], n = { ts: 0, tm: 0, te: 0, tc: 0, pd: 0, pm: 0, pu: 0, pc: 0, cl: 0, prevented: 0 };
  box.setAttribute('aria-hidden', 'true');
  box.style.cssText = 'position:fixed;left:6px;right:6px;top:calc(env(safe-area-inset-top,0px) + 56px);z-index:2147483647;pointer-events:none;' +
    'background:rgba(23,36,60,.88);color:#fff;font:11px/1.35 ui-monospace,Menlo,monospace;padding:6px 8px;border-radius:8px;white-space:pre-wrap;max-height:42vh;overflow:hidden';
  function grip() { return document.getElementById('a-grip'); }
  function onGrip(e) { var g = grip(); return !!(g && e.target && (e.target === g || g.contains(e.target))); }
  function state() {
    var g = grip(), sheet = document.getElementById('a-sheet'), cs = g ? getComputedStyle(g) : null, vv = window.visualViewport;
    return 'grip:' + (g ? 'yes ta=' + cs.touchAction : 'none') + ' snap=' + (typeof ASnap !== 'undefined' ? ASnap : '?') + ' drag=' + (window.__drag || 0) +
      '\nsheetTop=' + (sheet ? Math.round(sheet.getBoundingClientRect().top) : '?') + ' scrollY=' + Math.round(window.scrollY) +
      ' vv=' + (vv ? Math.round(vv.height) + '@' + Math.round(vv.offsetTop) : '?') + ' lock=' + document.documentElement.classList.contains('a-mission-lock');
  }
  function paint() {
    box.textContent = 'GRIP DEBUG  ts ' + n.ts + ' tm ' + n.tm + ' te ' + n.te + ' tc ' + n.tc + ' | pd ' + n.pd + ' pm ' + n.pm + ' pu ' + n.pu + ' pc ' + n.pc +
      ' | click ' + n.cl + ' | prevented ' + n.prevented + '\n' + state() + '\n' + log.slice(-8).join('\n');
    if (!box.isConnected && document.body) document.body.appendChild(box);
  }
  function rec(kind, e, extra) {
    var t = e.touches && e.touches[0] || e.changedTouches && e.changedTouches[0] || e;
    log.push(kind + (onGrip(e) ? '@grip' : '@' + ((e.target && (e.target.id || e.target.className || e.target.tagName)) + '').slice(0, 18)) +
      ' y=' + Math.round(t.clientY || 0) + (extra || '') + (e.cancelable === false ? ' noCancel' : ''));
    if (log.length > 40) log.splice(0, 20);
  }
  var map = { touchstart: 'ts', touchmove: 'tm', touchend: 'te', touchcancel: 'tc', pointerdown: 'pd', pointermove: 'pm', pointerup: 'pu', pointercancel: 'pc', click: 'cl' };
  Object.keys(map).forEach(function (type) {
    document.addEventListener(type, function (e) {
      if (!onGrip(e) && !window.__drag) return;
      n[map[type]]++;
      if (type === 'touchmove' || type === 'pointermove') { if (n[map[type]] % 4 !== 1) { paint(); return; } }
      rec(map[type], e, e.pointerType ? ' ' + e.pointerType : '');
      // check after the app's own handlers whether the move was prevented (page must not scroll / pull)
      if (type === 'touchmove') setTimeout(function () { if (e.defaultPrevented) { n.prevented++; } paint(); }, 0);
      paint();
    }, { capture: true, passive: true });
  });
  setInterval(paint, 500);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', paint); else paint();
})();
