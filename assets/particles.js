/* ================================================================
   IPL INTELLIGENCE PLATFORM — Particle System
   Canvas-based floating particles with mouse repulsion
   ================================================================ */

(function () {
  'use strict';

  var canvas, ctx, particles = [], raf;
  var W = 0, H = 0;
  var mouseX = -9999, mouseY = -9999;

  var CFG = {
    count:       55,
    minR:        0.5,
    maxR:        1.8,
    speed:       0.28,
    colors:     ['rgba(245,166,35,', 'rgba(0,212,255,', 'rgba(168,85,247,', 'rgba(255,107,53,'],
    linkDist:    110,
    mouseDist:   90,
  };

  function rand(a, b) { return a + Math.random() * (b - a); }

  /* ── Particle ──────────────────────────────────────────────────── */
  function Particle() { this.spawn(); }

  Particle.prototype.spawn = function () {
    this.x  = rand(0, W);
    this.y  = rand(0, H);
    this.vx = rand(-CFG.speed, CFG.speed);
    this.vy = rand(-CFG.speed, CFG.speed);
    this.r  = rand(CFG.minR, CFG.maxR);
    this.color = CFG.colors[Math.floor(Math.random() * CFG.colors.length)];
    this.alpha  = rand(0.08, 0.45);
    this.life   = rand(120, 280);
    this.maxLife = this.life;
  };

  Particle.prototype.update = function () {
    this.life--;
    if (this.life <= 0) { this.spawn(); return; }

    var dx = this.x - mouseX;
    var dy = this.y - mouseY;
    var dist = Math.sqrt(dx * dx + dy * dy);

    if (dist < CFG.mouseDist && dist > 0) {
      var force = (CFG.mouseDist - dist) / CFG.mouseDist;
      this.vx += (dx / dist) * force * 0.55;
      this.vy += (dy / dist) * force * 0.55;
      this.vx *= 0.94;
      this.vy *= 0.94;
    }

    this.x += this.vx;
    this.y += this.vy;

    if (this.x < 0)  this.x = W;
    if (this.x > W)  this.x = 0;
    if (this.y < 0)  this.y = H;
    if (this.y > H)  this.y = 0;
  };

  Particle.prototype.draw = function () {
    var life = this.life / this.maxLife;
    var a    = this.alpha * life;
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
    ctx.fillStyle = this.color + a + ')';
    ctx.fill();
  };

  /* ── connections ───────────────────────────────────────────────── */
  function drawLinks() {
    for (var i = 0; i < particles.length; i++) {
      for (var j = i + 1; j < particles.length; j++) {
        var dx   = particles[i].x - particles[j].x;
        var dy   = particles[i].y - particles[j].y;
        var dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < CFG.linkDist) {
          var a = (1 - dist / CFG.linkDist) * 0.07;
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = 'rgba(245,166,35,' + a + ')';
          ctx.lineWidth   = 0.6;
          ctx.stroke();
        }
      }
    }
  }

  /* ── animation loop ────────────────────────────────────────────── */
  function loop() {
    ctx.clearRect(0, 0, W, H);
    for (var i = 0; i < particles.length; i++) {
      particles[i].update();
      particles[i].draw();
    }
    drawLinks();
    raf = requestAnimationFrame(loop);
  }

  /* ── resize ─────────────────────────────────────────────────────── */
  function resize() {
    if (!canvas) return;
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }

  /* ── init ────────────────────────────────────────────────────────── */
  function init() {
    canvas = document.getElementById('particle-canvas');
    if (!canvas) { setTimeout(init, 500); return; }

    ctx = canvas.getContext('2d');
    resize();

    for (var i = 0; i < CFG.count; i++) {
      particles.push(new Particle());
    }

    window.addEventListener('resize', resize, { passive: true });
    window.addEventListener('mousemove', function (e) {
      mouseX = e.clientX;
      mouseY = e.clientY;
    }, { passive: true });
    window.addEventListener('mouseleave', function () {
      mouseX = -9999;
      mouseY = -9999;
    });

    loop();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
