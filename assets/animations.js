/* ================================================================
   IPL INTELLIGENCE PLATFORM — Animation Engine
   Scroll reveals · Counters · Navbar · Mobile menu · Hover tilt
   ================================================================ */

(function () {
  'use strict';

  var _obs = new WeakMap();
  var _initiated = false;

  /* ── helpers ─────────────────────────────────────────────────── */
  function debounce(fn, ms) {
    var t;
    return function () {
      clearTimeout(t);
      t = setTimeout(fn, ms);
    };
  }

  function easeOutExpo(x) {
    return x >= 1 ? 1 : 1 - Math.pow(2, -10 * x);
  }

  function formatNum(n, dec) {
    dec = dec || 0;
    if (n >= 1e6) return (n / 1e6).toFixed(dec || 1) + 'M';
    if (n >= 1e3) return (n / 1e3).toFixed(dec || 0) + 'K';
    return n.toFixed(dec);
  }

  /* ── page loader ──────────────────────────────────────────────── */
  function initLoader() {
    var loader = document.getElementById('page-loader');
    if (!loader) return;
    setTimeout(function () {
      loader.classList.add('done');
    }, 1900);
  }

  /* ── scroll progress bar ──────────────────────────────────────── */
  function initScrollProgress() {
    var bar = document.querySelector('.scroll-progress');
    if (!bar) return;
    function update() {
      var scrollable = document.documentElement.scrollHeight - window.innerHeight;
      var pct = scrollable > 0 ? (window.scrollY / scrollable) * 100 : 0;
      bar.style.width = pct + '%';
    }
    window.addEventListener('scroll', update, { passive: true });
    update();
  }

  /* ── floating navbar ──────────────────────────────────────────── */
  function initNavbar() {
    var nav = document.querySelector('.floating-navbar');
    if (!nav) return;
    function onScroll() {
      nav.classList.toggle('scrolled', window.scrollY > 24);
    }
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
    updateActiveNavLinks();
  }

  function updateActiveNavLinks() {
    var path = window.location.pathname;
    document.querySelectorAll('.nav-link[href], .drawer-nav-link[href]').forEach(function (a) {
      var href = a.getAttribute('href');
      var isActive = href === path || (href === '/' && (path === '/' || path === ''));
      a.classList.toggle('active', isActive);
    });
  }

  /* ── mobile drawer ────────────────────────────────────────────── */
  function initMobileMenu() {
    var btn      = document.querySelector('.hamburger');
    var drawer   = document.querySelector('.mobile-drawer');
    var overlay  = document.querySelector('.drawer-overlay');
    if (!btn || !drawer) return;

    function open()  { drawer.classList.add('open'); btn.classList.add('open'); if (overlay) overlay.classList.add('open'); document.body.style.overflow = 'hidden'; }
    function close() { drawer.classList.remove('open'); btn.classList.remove('open'); if (overlay) overlay.classList.remove('open'); document.body.style.overflow = ''; }

    btn.addEventListener('click', function () {
      drawer.classList.contains('open') ? close() : open();
    });

    if (overlay) overlay.addEventListener('click', close);

    drawer.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', close);
    });
  }

  /* ── scroll reveal ────────────────────────────────────────────── */
  function initScrollReveal() {
    var items = document.querySelectorAll('.reveal:not([data-obs]), .stagger-in:not([data-obs])');
    if (!items.length) return;

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.classList.add('in');
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

    items.forEach(function (el) {
      el.setAttribute('data-obs', '1');
      io.observe(el);
    });
  }

  /* ── animated counters ────────────────────────────────────────── */
  function initCounters() {
    var items = document.querySelectorAll('[data-counter]:not([data-counted])');
    if (!items.length) return;

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          animateCounter(e.target);
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.5 });

    items.forEach(function (el) {
      el.setAttribute('data-counted', '1');
      io.observe(el);
    });
  }

  function animateCounter(el) {
    var target   = parseFloat(el.getAttribute('data-counter') || '0');
    var duration = parseInt(el.getAttribute('data-duration') || '2200');
    var suffix   = el.getAttribute('data-suffix') || '';
    var dec      = parseInt(el.getAttribute('data-decimals') || '0');
    var start    = performance.now();

    function tick(now) {
      var elapsed  = now - start;
      var progress = Math.min(elapsed / duration, 1);
      var value    = target * easeOutExpo(progress);
      el.textContent = formatNum(value, dec) + suffix;
      if (progress < 1) requestAnimationFrame(tick);
      else el.textContent = formatNum(target, dec) + suffix;
    }

    requestAnimationFrame(tick);
  }

  /* ── card tilt ────────────────────────────────────────────────── */
  function initTilt() {
    document.querySelectorAll('.player-card:not([data-tilt])').forEach(function (card) {
      card.setAttribute('data-tilt', '1');
      card.addEventListener('mousemove', function (e) {
        var r  = card.getBoundingClientRect();
        var cx = r.width  / 2;
        var cy = r.height / 2;
        var rx = ((e.clientY - r.top)  - cy) / cy * -9;
        var ry = ((e.clientX - r.left) - cx) / cx *  9;
        card.style.transform = 'perspective(900px) rotateX(' + rx + 'deg) rotateY(' + ry + 'deg) scale(1.03) translateY(-8px)';
      });
      card.addEventListener('mouseleave', function () {
        card.style.transform = '';
      });
    });
  }

  /* ── magnetic buttons ─────────────────────────────────────────── */
  function initMagnetic() {
    document.querySelectorAll('.btn-glow:not([data-mag])').forEach(function (btn) {
      btn.setAttribute('data-mag', '1');
      btn.addEventListener('mousemove', function (e) {
        var r  = btn.getBoundingClientRect();
        var x  = e.clientX - r.left - r.width  / 2;
        var y  = e.clientY - r.top  - r.height / 2;
        btn.style.transform = 'translate(' + (x * 0.14) + 'px,' + (y * 0.14) + 'px)';
      });
      btn.addEventListener('mouseleave', function () {
        btn.style.transform = '';
      });
    });
  }

  /* ── featured card subtle hover glow ─────────────────────────── */
  function initFeaturedCards() {
    document.querySelectorAll('.featured-card:not([data-fc])').forEach(function (card) {
      card.setAttribute('data-fc', '1');
    });
  }

  /* ── location listener (re-init on Dash page changes) ─────────── */
  var _lastPath = window.location.pathname;
  function watchLocation() {
    setInterval(function () {
      if (window.location.pathname !== _lastPath) {
        _lastPath = window.location.pathname;
        onContentUpdated();
        updateActiveNavLinks();
      }
    }, 300);
  }

  /* ── content mutation observer ────────────────────────────────── */
  var contentObserver = new MutationObserver(debounce(onContentUpdated, 250));

  function onContentUpdated() {
    initScrollReveal();
    initCounters();
    initTilt();
    initMagnetic();
    initFeaturedCards();
  }

  /* ── main init ────────────────────────────────────────────────── */
  function init() {
    if (_initiated) return;
    _initiated = true;

    initLoader();
    initScrollProgress();
    initNavbar();
    initMobileMenu();
    initScrollReveal();
    initCounters();
    initTilt();
    initMagnetic();
    initFeaturedCards();
    watchLocation();

    contentObserver.observe(document.body, { childList: true, subtree: true });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
