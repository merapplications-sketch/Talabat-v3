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
  /* Panel jump (iPhone 24 Oct): every render (about once a second while an offer counts down, and on each GPS reading)
     rebuilds the waiting / mission panel with innerHTML. The new panel starts at its CSS top (460 / 240 px); driver A then
     measures the layout and sets the real top, and the `transition: top .18s` animated that move -> the panel slid up from
     the default position on every render. During a re-render only, transitions of the two panels are switched off, so the
     panel appears directly at its kept position; snaps, drags and taps keep their animation. Layout and design unchanged. */
  if (typeof render0 === 'function') {
    var css = document.createElement('style');
    css.textContent = 'html.a-rerender .w-sheet,html.a-rerender .a-sheet{transition:none!important}';
    document.head.appendChild(css);
    var renderPanels = render0, clearFrame = 0;
    render0 = function () {
      var root = document.documentElement;
      root.classList.add('a-rerender');
      try { return renderPanels.apply(this, arguments); }
      finally {
        void root.offsetHeight;   /* settle the new panel at its final top before the class goes away */
        if (clearFrame) cancelAnimationFrame(clearFrame);
        clearFrame = requestAnimationFrame(function () { clearFrame = 0; root.classList.remove('a-rerender'); });
      }
    };
  }
  /* for a «my location» control on the mission screen (none in driver A today): back to the automatic frame */
  window.aMapRecenter = function () { var x = typeof aTask === 'function' ? aTask() : null; user = false; if (x && ready()) { withMe = GEO.lat != null; frameOnce(x); } };
})();
