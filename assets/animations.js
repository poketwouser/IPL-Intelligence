/**
 * IPL Intelligence — Animation Engine v5.0
 * GSAP + Lenis smooth scroll. Cinema-grade interactions.
 * Page transitions, scroll storytelling, enhanced reveals.
 */

(function () {
  "use strict";

  let lenis = null;

  /* ── Wait for GSAP + Lenis ── */
  function waitForLibs(cb, attempts) {
    attempts = attempts || 0;
    if (typeof gsap !== "undefined" && typeof ScrollTrigger !== "undefined" &&
        typeof Lenis !== "undefined") {
      cb();
    } else if (attempts < 80) {
      setTimeout(() => waitForLibs(cb, attempts + 1), 100);
    } else {
      bootCSSFallback();
    }
  }

  /* ════════════════════════════════════════════════════════
     LOADER — Cinematic intro sequence
  ════════════════════════════════════════════════════════ */
  function initLoader() {
    const loader = document.getElementById("page-loader");
    if (!loader) return;

    // Dismiss the loader - guaranteed to work
    const dismiss = () => {
      if (loader.classList.contains("done")) return;
      if (typeof gsap !== "undefined") {
        gsap.to(loader, {
          opacity: 0, scale: 1.02, duration: 0.6, ease: "power2.inOut",
          onComplete: () => {
            loader.classList.add("done");
            loader.style.display = "none";
            document.body.classList.add("page-entered");
          },
        });
      } else {
        loader.style.transition = "opacity 0.5s ease";
        loader.style.opacity = "0";
        setTimeout(() => {
          loader.classList.add("done");
          loader.style.display = "none";
          document.body.classList.add("page-entered");
        }, 500);
      }
    };

    // Auto dismiss
    setTimeout(dismiss, 1000); // reduced timeout for snappier entry
  }

  /* ════════════════════════════════════════════════════════
     LENIS SMOOTH SCROLL
  ════════════════════════════════════════════════════════ */
  function initLenis() {
    if (typeof Lenis === "undefined") return;

    lenis = new Lenis({
      duration: 1.25,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      orientation: "vertical",
      smoothWheel: true,
      wheelMultiplier: 1.0,
      touchMultiplier: 2,
    });

    if (typeof gsap !== "undefined") {
      gsap.ticker.add((time) => lenis.raf(time * 1000));
      gsap.ticker.lagSmoothing(0);
      if (typeof ScrollTrigger !== "undefined") {
        lenis.on("scroll", ScrollTrigger.update);
      }
    } else {
      (function raf(t) { lenis.raf(t); requestAnimationFrame(raf); })(performance.now());
    }
  }

  /* ════════════════════════════════════════════════════════
     SCROLL PROGRESS
  ════════════════════════════════════════════════════════ */
  function initScrollProgress() {
    const line = document.getElementById("scroll-line");
    if (!line) return;

    if (lenis) {
      lenis.on("scroll", ({ progress }) => {
        line.style.width = (progress * 100).toFixed(2) + "%";
      });
    } else {
      window.addEventListener("scroll", () => {
        const d = document.documentElement;
        const pct = d.scrollTop / (d.scrollHeight - d.clientHeight) || 0;
        line.style.width = (pct * 100).toFixed(2) + "%";
      }, { passive: true });
    }
  }

  /* ════════════════════════════════════════════════════════
     NAVBAR
  ════════════════════════════════════════════════════════ */
  function initNavbar() {
    const navbar = document.getElementById("navbar");
    if (!navbar) return;

    function onScroll(y) {
      navbar.classList.toggle("scrolled", y > 60);
    }

    if (lenis) {
      lenis.on("scroll", ({ scroll }) => onScroll(scroll));
    } else {
      window.addEventListener("scroll", () => onScroll(window.scrollY), { passive: true });
    }

    updateActiveNavLinks();
  }

  function updateActiveNavLinks() {
    const path = window.location.pathname;
    document.querySelectorAll(".nav-link, .drawer-link").forEach(link => {
      const href = link.getAttribute("href") || "";
      const active = href === "/" ? path === "/" : (href.length > 1 && path.startsWith(href));
      link.classList.toggle("active", active);
    });
  }

  /* ════════════════════════════════════════════════════════
     MOBILE DRAWER
  ════════════════════════════════════════════════════════ */
  function initDrawer() {
    const hamburger = document.getElementById("hamburger-btn");
    const drawer    = document.getElementById("drawer");
    const backdrop  = document.getElementById("drawer-backdrop");
    const closeBtn  = document.getElementById("drawer-close");
    if (!hamburger || !drawer) return;

    function open()  {
      drawer.classList.add("open");
      backdrop && backdrop.classList.add("open");
      document.body.style.overflow = "hidden";
      if (lenis) lenis.stop();
    }
    function close() {
      drawer.classList.remove("open");
      backdrop && backdrop.classList.remove("open");
      document.body.style.overflow = "";
      if (lenis) lenis.start();
    }

    hamburger.addEventListener("click", open);
    closeBtn  && closeBtn.addEventListener("click", close);
    backdrop  && backdrop.addEventListener("click", close);
    drawer.querySelectorAll(".drawer-link").forEach(l => l.addEventListener("click", close));
    document.addEventListener("keydown", e => { if (e.key === "Escape") close(); });
  }

  /* ════════════════════════════════════════════════════════
     SCROLL REVEALS — GSAP (Enhanced v5)
  ════════════════════════════════════════════════════════ */
  function initScrollReveal() {
    if (typeof gsap === "undefined" || typeof ScrollTrigger === "undefined") {
      initScrollRevealCSS();
      return;
    }

    gsap.registerPlugin(ScrollTrigger);

    // Standard reveal
    gsap.utils.toArray(".reveal:not([data-gsap-done])").forEach(el => {
      el.dataset.gsapDone = "1";
      gsap.fromTo(el,
        { opacity: 0, y: 36 },
        {
          opacity: 1, y: 0,
          duration: 0.8, ease: "power3.out",
          scrollTrigger: { trigger: el, start: "top 92%", toggleActions: "play none none reverse" }
        }
      );
    });

    // Directional reveals
    gsap.utils.toArray(".reveal-left:not([data-gsap-done])").forEach(el => {
      el.dataset.gsapDone = "1";
      gsap.fromTo(el,
        { opacity: 0, x: -40 },
        {
          opacity: 1, x: 0,
          duration: 0.8, ease: "power3.out",
          scrollTrigger: { trigger: el, start: "top 92%" }
        }
      );
    });

    gsap.utils.toArray(".reveal-right:not([data-gsap-done])").forEach(el => {
      el.dataset.gsapDone = "1";
      gsap.fromTo(el,
        { opacity: 0, x: 40 },
        {
          opacity: 1, x: 0,
          duration: 0.8, ease: "power3.out",
          scrollTrigger: { trigger: el, start: "top 92%" }
        }
      );
    });

    gsap.utils.toArray(".reveal-scale:not([data-gsap-done])").forEach(el => {
      el.dataset.gsapDone = "1";
      gsap.fromTo(el,
        { opacity: 0, scale: 0.9 },
        {
          opacity: 1, scale: 1,
          duration: 0.7, ease: "power2.out",
          scrollTrigger: { trigger: el, start: "top 92%" }
        }
      );
    });

    // Stagger grids
    gsap.utils.toArray(".stagger-in:not([data-gsap-done])").forEach(container => {
      container.dataset.gsapDone = "1";
      gsap.fromTo(Array.from(container.children),
        { opacity: 0, y: 24 },
        {
          opacity: 1, y: 0,
          stagger: 0.08,
          duration: 0.6, ease: "power2.out",
          scrollTrigger: { trigger: container, start: "top 92%" }
        }
      );
    });

    // Timeline items
    gsap.utils.toArray(".timeline-item:not([data-gsap-done])").forEach((el, i) => {
      el.dataset.gsapDone = "1";
      gsap.fromTo(el,
        { opacity: 0, x: -30 },
        {
          opacity: 1, x: 0,
          duration: 0.6, ease: "power2.out",
          delay: i * 0.05,
          scrollTrigger: { trigger: el, start: "top 94%" }
        }
      );
    });
  }

  function initScrollRevealCSS() {
    const io = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (e.isIntersecting) { e.target.classList.add("visible"); io.unobserve(e.target); }
      });
    }, { threshold: 0.1 });
    document.querySelectorAll(".reveal, .reveal-left, .reveal-right, .reveal-scale, .stagger-in, .timeline-item").forEach(el => io.observe(el));
  }

  /* ════════════════════════════════════════════════════════
     ANIMATED COUNTERS
  ════════════════════════════════════════════════════════ */
  function initCounters() {
    const counters = document.querySelectorAll("[data-counter]:not([data-counter-init])");
    if (!counters.length) return;

    function animateCounter(el) {
      if (el.dataset.animated) return;
      el.dataset.animated = "1";

      const target   = parseFloat(el.dataset.counter) || 0;
      const duration = parseInt(el.dataset.duration)  || 1800;
      const suffix   = el.dataset.suffix || "";
      const decimals = parseInt(el.dataset.decimals)  || 0;
      const prefix   = el.dataset.prefix || "";

      if (typeof gsap !== "undefined") {
        const obj = { val: 0 };
        gsap.to(obj, {
          val: target, duration: duration / 1000, ease: "power2.out",
          onUpdate() { el.textContent = prefix + obj.val.toFixed(decimals) + suffix; },
        });
      } else {
        const start = performance.now();
        (function step(now) {
          const p = Math.min(1, (now - start) / duration);
          const e = 1 - Math.pow(1 - p, 3);
          el.textContent = prefix + (target * e).toFixed(decimals) + suffix;
          if (p < 1) requestAnimationFrame(step);
        })(start);
      }
    }

    if (typeof ScrollTrigger !== "undefined") {
      counters.forEach(el => {
        el.dataset.counterInit = "1";
        ScrollTrigger.create({ trigger: el, start: "top 92%", onEnter: () => animateCounter(el) });
      });
    } else {
      const io = new IntersectionObserver((entries) => {
        entries.forEach(e => { if (e.isIntersecting) { animateCounter(e.target); io.unobserve(e.target); } });
      }, { threshold: 0.3 });
      counters.forEach(el => {
        el.dataset.counterInit = "1";
        io.observe(el);
      });
    }
  }

  /* ════════════════════════════════════════════════════════
     PLAYER CARD 3D TILT
  ════════════════════════════════════════════════════════ */
  function initTilt() {
    document.querySelectorAll(".player-card:not([data-tilt])").forEach(card => {
      card.dataset.tilt = "1";

      card.addEventListener("mousemove", e => {
        const r  = card.getBoundingClientRect();
        const rx = ((e.clientY - r.top  - r.height / 2) / (r.height / 2)) * -12;
        const ry = ((e.clientX - r.left - r.width  / 2) / (r.width  / 2)) *  12;
        if (typeof gsap !== "undefined") {
          gsap.to(card, { rotateX: rx, rotateY: ry, scale: 1.06, duration: 0.4, ease: "power2.out", transformPerspective: 800 });
        } else {
          card.style.transform = `perspective(800px) rotateX(${rx}deg) rotateY(${ry}deg) scale(1.06)`;
        }
      });

      card.addEventListener("mouseleave", () => {
        if (typeof gsap !== "undefined") {
          gsap.to(card, { rotateX: 0, rotateY: 0, scale: 1, duration: 0.6, ease: "elastic.out(1, 0.5)" });
        } else {
          card.style.transform = "";
        }
      });
    });
  }

  /* ════════════════════════════════════════════════════════
     MAGNETIC BUTTONS
  ════════════════════════════════════════════════════════ */
  function initMagnetic() {
    if (typeof gsap === "undefined") return;
    document.querySelectorAll(".btn-primary:not([data-mag]), .btn-ghost:not([data-mag]), .featured-card:not([data-mag])").forEach(btn => {
      btn.dataset.mag = "1";
      btn.addEventListener("mousemove", e => {
        const r  = btn.getBoundingClientRect();
        const dx = (e.clientX - r.left - r.width  / 2) * 0.15;
        const dy = (e.clientY - r.top  - r.height / 2) * 0.15;
        gsap.to(btn, { x: dx, y: dy, duration: 0.4, ease: "power2.out" });
      });
      btn.addEventListener("mouseleave", () => {
        gsap.to(btn, { x: 0, y: 0, duration: 0.5, ease: "back.out(2)" });
      });
    });
  }

  /* ════════════════════════════════════════════════════════
     CUSTOM CURSOR
  ════════════════════════════════════════════════════════ */
  function initCursor() {
    if ("ontouchstart" in window || navigator.maxTouchPoints > 0) return;

    const dot   = document.getElementById("cursor");
    const trail = document.getElementById("cursor-trail");
    if (!dot) return;

    let mx = -200, my = -200, tx = -200, ty = -200;

    window.addEventListener("mousemove", e => { mx = e.clientX; my = e.clientY; }, { passive: true });

    const SELECTORS = "a, button, .player-card, .featured-card, .stat-card, .timeline-content, label, [role='button']";

    (function tick() {
      if (typeof gsap !== "undefined") {
        gsap.set(dot, { x: mx, y: my });
        if (trail) {
          tx += (mx - tx) * 0.1;
          ty += (my - ty) * 0.1;
          gsap.set(trail, { x: tx, y: ty });
        }
      } else {
        dot.style.left = mx + "px"; dot.style.top = my + "px";
        if (trail) {
          tx += (mx - tx) * 0.1; ty += (my - ty) * 0.1;
          trail.style.left = tx + "px"; trail.style.top = ty + "px";
        }
      }

      const el = document.elementFromPoint(mx, my);
      document.body.classList.toggle("cursor-hover", !!(el && el.closest(SELECTORS)));

      requestAnimationFrame(tick);
    })();
  }

  /* ════════════════════════════════════════════════════════
     HERO PARALLAX
  ════════════════════════════════════════════════════════ */
  function initHeroParallax() {
    if (typeof gsap === "undefined" || typeof ScrollTrigger === "undefined") return;

    const hero    = document.querySelector(".home-hero");
    const content = document.querySelector(".home-hero-content");
    const orbs    = document.querySelectorAll(".home-hero-orb");

    if (!hero) return;

    if (content) {
      gsap.to(content, {
        y: -120, opacity: 0.3, ease: "none",
        scrollTrigger: { trigger: hero, start: "top top", end: "bottom top", scrub: 1.2 }
      });
    }

    orbs.forEach((orb, i) => {
      gsap.to(orb, {
        y: -80 - i * 40, ease: "none",
        scrollTrigger: { trigger: hero, start: "top top", end: "bottom top", scrub: true }
      });
    });
  }

  /* ════════════════════════════════════════════════════════
     PERFORMANCE METER ANIMATION
  ════════════════════════════════════════════════════════ */
  function initPerfMeters() {
    const perfSel = ".perf-meter-fill:not([data-animated]), .legend-bar-fill:not([data-animated]), .dynasty-bar:not([data-animated])";
    document.querySelectorAll(perfSel).forEach(fill => {
      const target = fill.dataset.width || "0%";
      fill.dataset.animated = "1";

      if (typeof ScrollTrigger !== "undefined") {
        ScrollTrigger.create({
          trigger: fill,
          start: "top 92%",
          onEnter: () => { fill.style.width = target; }
        });
      } else {
        const io = new IntersectionObserver(entries => {
          entries.forEach(e => {
            if (e.isIntersecting) {
              fill.style.width = target;
              io.unobserve(e.target);
            }
          });
        }, { threshold: 0.3 });
        io.observe(fill);
      }
    });
  }

  /* ════════════════════════════════════════════════════════
     PAGE TRANSITION SYSTEM
  ════════════════════════════════════════════════════════ */
  let _path = window.location.pathname;

  function initPageTransitions() {
    setInterval(() => {
      if (window.location.pathname !== _path) {
        const oldPath = _path;
        _path = window.location.pathname;

        // Transition effect
        document.body.classList.remove("page-entered");
        document.body.classList.add("page-transitioning");

        setTimeout(() => {
          document.body.classList.remove("page-transitioning");
          document.body.classList.add("page-entered");

          updateActiveNavLinks();

          // Re-init dynamic elements
          setTimeout(() => {
            initScrollReveal();
            initCounters();
            initTilt();
            initMagnetic();
            initHeroParallax();
            initPerfMeters();
            if (typeof ScrollTrigger !== "undefined") ScrollTrigger.refresh();
          }, 100);
        }, 300);

        // Scroll to top
        if (lenis) {
          lenis.scrollTo(0, { immediate: true });
        } else {
          window.scrollTo(0, 0);
        }
      }
    }, 200);
  }

  /* ════════════════════════════════════════════════════════
     MUTATION OBSERVER (Dash dynamic content)
  ════════════════════════════════════════════════════════ */
  function initMutationObserver() {
    const target = document.querySelector(".main") || document.body;
    let debounceTimer;

    new MutationObserver(() => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        initLoader();
        initScrollReveal();
        initCounters();
        initTilt();
        initMagnetic();
        initPerfMeters();
        if (typeof ScrollTrigger !== "undefined") ScrollTrigger.refresh();
      }, 150);
    }).observe(target, { childList: true, subtree: true });
  }

  /* ════════════════════════════════════════════════════════
     CSS FALLBACK BOOT (no GSAP/Lenis)
  ════════════════════════════════════════════════════════ */
  function bootCSSFallback() {
    initCursor();
    initDrawer();
    initScrollRevealCSS();
    initCounters();
    initNavbar();
    initScrollProgress();
    initPageTransitions();
    initMutationObserver();
    initPerfMeters();
  }

  /* ════════════════════════════════════════════════════════
     MAIN BOOT
  ════════════════════════════════════════════════════════ */
  function boot() {
    initLenis();
    initCursor();
    initDrawer();
    initScrollProgress();
    initNavbar();
    initScrollReveal();
    initCounters();
    initTilt();
    initMagnetic();
    initHeroParallax();
    initPerfMeters();
    initPageTransitions();
    initMutationObserver();
  }

  function start() {
    initLoader(); // Run immediately when DOM is ready
    waitForLibs(boot);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }

})();
