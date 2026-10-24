/* TALABOT driver — mission map view policy (technical, loaded after assets/driver-a/driver-a.js).
   Driver A re-framed the mission map (fitBounds) after EVERY mapUpd and EVERY non-drag panel paint, i.e. on each render
   (GPS reading, offer countdown, Safari toolbar / innerHeight change) -> the map jumped and changed zoom by itself.
   Policy here, same markers and the same fit function of driver A (aFitVisible), only WHEN it runs changes:
   - auto-frame once per task + stage (first display, task change, stage change);
   - plus once when the driver's position first becomes known for that task (the first frame had no driver point);
   - after a user pan / pinch / wheel / double-tap the user's view is kept (no auto-frame) until the task or stage changes
     or window.aMapRecenter() is called;
   - otherwise (GPS update, re-render, panel or viewport size change) only invalidateSize, which keeps centre and zoom.
   Markers keep moving with GPS through the unchanged mapUpd of driver.html. */
(function () {
  'use strict';
  if (typeof aFitVisible !== 'function' || typeof mapUpd !== 'function') return;
  var frameOnce = aFitVisible, key = '', withMe = false, user = false, bound = null;
  function ready() { return !!(window.L && typeof DM !== 'undefined' && DM && DM !== 1 && DM.getContainer); }
  function bindUser() {
    var c = DM.getContainer(); if (bound === c) return; bound = c;
    ['pointerdown', 'touchstart', 'wheel', 'dblclick'].forEach(function (ev) {
      c.addEventListener(ev, function (e) { if (e.isTrusted !== false) user = true; }, { passive: true });
    });
  }
  function keep() { try { DM.invalidateSize({ animate: false }); } catch (e) {} }   /* pan:true (default) keeps the centre */
  aFitVisible = function (x) {
    if (!x || !ready() || !document.getElementById('a-sheet')) return;
    bindUser();
    var k = String(x.id) + ':' + (typeof aTaskStage === 'function' ? aTaskStage(x) : ''), hasMe = GEO.lat != null && GEO.lng != null;
    if (k !== key) { key = k; user = false; withMe = hasMe; frameOnce(x); return; }
    if (!user && hasMe && !withMe) { withMe = true; frameOnce(x); return; }
    keep();
  };
  /* for a «my location» control on the mission screen (none in driver A today): back to the automatic frame */
  window.aMapRecenter = function () { var x = typeof aTask === 'function' ? aTask() : null; user = false; if (x && ready()) { withMe = GEO.lat != null; frameOnce(x); } };
})();
