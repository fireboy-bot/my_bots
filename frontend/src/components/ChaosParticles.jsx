import { useEffect, useRef, useCallback } from 'react';
import './ChaosParticles.css';

const CONFIG = {
  total: 40,
  types: {
    dust: { ratio: 0.70, size: [1, 2], opacity: [0.04, 0.10], speed: 0.2, immortal: true },
    glow: { ratio: 0.25, size: [1.5, 2.5], opacity: [0.06, 0.12], speed: 0.15, immortal: true },
    spark: { ratio: 0.05, size: [2, 3], opacity: [0.10, 0.18], speed: 0.25, immortal: false, lifeMin: 2, lifeMax: 4 },
  },
  colors: {
    dust: ['rgba(255,255,255,0.15)', 'rgba(180,255,200,0.12)'],
    glow: ['rgba(255,230,150,0.18)', 'rgba(200,180,255,0.15)'],
    spark: ['rgba(255,255,255,0.25)', 'rgba(255,230,150,0.22)'],
  },
};

export function ChaosParticles({ chaosEnergy = 0, riftStage = 0, enabled = true }) {
  const canvasRef = useRef(null);
  const rafRef = useRef(null);
  const particlesRef = useRef([]);

  const createParticle = useCallback((w, h, type) => {
    const cfg = CONFIG.types[type];
    return {
      x: Math.random() * w,
      y: Math.random() * h,
      vx: (Math.random() - 0.5) * cfg.speed,
      vy: (Math.random() - 0.5) * cfg.speed,
      size: cfg.size[0] + Math.random() * (cfg.size[1] - cfg.size[0]),
      targetOpacity: cfg.opacity[0] + Math.random() * (cfg.opacity[1] - cfg.opacity[0]),
      currentOpacity: cfg.immortal ? cfg.opacity[1] : 0,
      type,
      color: CONFIG.colors[type][Math.floor(Math.random() * CONFIG.colors[type].length)],
      phase: Math.random() * Math.PI * 2,
      life: cfg.immortal ? 1 : cfg.lifeMin + Math.random() * (cfg.lifeMax - cfg.lifeMin),
      isRespawning: !cfg.immortal,
    };
  }, []);

  const initParticles = useCallback((w, h) => {
    const arr = [];
    const total = Math.min(CONFIG.total, Math.floor((w * h) / 50000));
    for (let i = 0; i < total; i++) {
      const r = Math.random();
      const type =
        r < CONFIG.types.dust.ratio
          ? 'dust'
          : r < CONFIG.types.dust.ratio + CONFIG.types.glow.ratio
            ? 'glow'
            : 'spark';
      arr.push(createParticle(w, h, type));
    }
    return arr;
  }, [createParticle]);

  const animate = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const w = canvas.width;
    const h = canvas.height;
    const chaosMult = 1 + (chaosEnergy / 100) * 0.15;

    ctx.clearRect(0, 0, w, h);

    particlesRef.current.forEach((p) => {
      const cfg = CONFIG.types[p.type];

      p.vx *= 0.99;
      p.vy *= 0.99;
      p.x += p.vx * chaosMult;
      p.y += p.vy * chaosMult;
      p.phase += 0.006;
      p.x += Math.sin(p.phase) * 0.15;
      p.y += Math.cos(p.phase * 0.6) * 0.15;

      const m = 8;
      if (p.x < m) p.x = m;
      if (p.x > w - m) p.x = w - m;
      if (p.y < m) p.y = m;
      if (p.y > h - m) p.y = h - m;

      if (cfg.immortal) {
        p.currentOpacity = cfg.opacity[0] + Math.sin(Date.now() * 0.001 + p.phase) * 0.015;
      } else {
        if (p.isRespawning) {
          p.currentOpacity += 0.01;
          if (p.currentOpacity >= p.targetOpacity) {
            p.currentOpacity = p.targetOpacity;
            p.isRespawning = false;
          }
        } else {
          p.life -= 0.002;
          if (p.life <= 0.2) p.currentOpacity -= 0.008;
          if (p.currentOpacity <= 0.01) {
            p.x = Math.random() * w;
            p.y = Math.random() * h;
            p.life = cfg.lifeMin + Math.random() * (cfg.lifeMax - cfg.lifeMin);
            p.currentOpacity = 0;
            p.isRespawning = true;
            p.vx = (Math.random() - 0.5) * cfg.speed;
            p.vy = (Math.random() - 0.5) * cfg.speed;
          }
        }
      }

      p.currentOpacity = Math.max(0.02, Math.min(0.22, p.currentOpacity));

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      ctx.fillStyle = p.color.replace(/[\d.]+\)$/, `${p.currentOpacity})`);
      ctx.fill();
    });

    // rAF управляется снаружи (с паузой при hidden tab)
  }, [chaosEnergy]);

  useEffect(() => {
    if (!enabled) return;
    const canvas = canvasRef.current;
    if (!canvas) return;

    let running = true;

    const resize = () => {
      const parent = canvas.parentElement;
      if (!parent) return;
      canvas.width = parent.clientWidth;
      canvas.height = parent.clientHeight;
      particlesRef.current = initParticles(canvas.width, canvas.height);
    };

    const tick = () => {
      if (!running || document.hidden) {
        rafRef.current = requestAnimationFrame(tick);
        return;
      }
      animate();
      rafRef.current = requestAnimationFrame(tick);
    };

    resize();
    window.addEventListener('resize', resize);
    rafRef.current = requestAnimationFrame(tick);

    return () => {
      running = false;
      window.removeEventListener('resize', resize);
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [animate, initParticles, enabled]);

  if (!enabled) return null;

  return <canvas ref={canvasRef} className="chaos-particles-canvas" aria-hidden="true" />;
}
