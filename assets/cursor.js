/* ================================================================
   IPL INTELLIGENCE PLATFORM — Custom Cursor
   Smooth-following ring with hover expand
   ================================================================ */

(function () {
  'use strict';

  var dot, ring;
  var mx = 0, my = 0;
  var rx = 0, ry = 0;

  var INTERACTABLES = 'a, button, .btn-glow, .player-card, .featured-card, .stat-card, .kpi-card, .chart-card, .glass-card, input, select, .nav-link, .hamburger, [role="button"]';

  function init() {
    if ('ontouchstart' in window || navigator.maxTouchPoints > 0) return;

    dot  = document.getElementById('cursor');
    ring = document.getElementById('cursor-ring');
    if (!dot || !ring) return;

    document.addEventListener('mousemove', function (e) {
      mx = e.clientX;
      my = e.clientY;
      dot.style.left = mx + 'px';
      dot.style.top  = my + 'px';
    }, { passive: true });

    document.addEventListener('mouseover', function (e) {
      var target = e.target.closest(INTERACTABLES);
      if (target) ring.classList.add('hovering');
      else ring.classList.remove('hovering');
    });

    document.addEventListener('mousedown', function () {
      dot.style.transform  = 'translate(-50%,-50%) scale(0.7)';
      ring.style.transform = 'translate(-50%,-50%) scale(0.85)';
    });

    document.addEventListener('mouseup', function () {
      dot.style.transform  = '';
      ring.style.transform = '';
    });

    followRing();
  }

  function followRing() {
    rx += (mx - rx) * 0.11;
    ry += (my - ry) * 0.11;
    if (ring) {
      ring.style.left = rx + 'px';
      ring.style.top  = ry + 'px';
    }
    requestAnimationFrame(followRing);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
