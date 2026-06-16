import { useEffect, useRef, useCallback, useState } from 'react';
import { createPortal } from 'react-dom';
import './ChaosParticles.css';

// 🔧 НАСТРОЙКИ АТМОСФЕРЫ (крути под себя)
const CONFIG = {
  total: 50,
  mouse: { radius: 220, force: 0.4, friction: 0.92 },
    types: {
    dust: { ratio: 0.60, size: [1.5, 2.5], opacity: [0.08, 0.18], speed: 0.15, immortal: true },
    glow: { ratio: 0.30, size: [2.5, 4.0], opacity: [0.10, 0.20], speed: 0.12, immortal: true },
    spark: { ratio: 0.10, size: [3.0, 5.0], opacity: [0.15, 0.30], speed: 0.25, immortal: false, lifeMin: 3, lifeMax: 6 }
  },
  types: {
    dust: { ratio: 0.60, size: [1.5, 2.5], opacity: [0.08, 0.18], speed: 0.3, immortal: true },
    glow: { ratio: 0.30, size: [2.5, 4.0], opacity: [0.12, 0.22], speed: 0.2, immortal: true },
    spark: { ratio: 0.10, size: [3.0, 5.0], opacity: [0.30, 0.50], speed: 0.5, immortal: false, lifeMin: 2, lifeMax: 4 }
  },
  colors: {
    dust: ['rgba(255,255,255,0.2)', 'rgba(180,255,200,0.2)'],
    glow: ['rgba(255,230,150,0.25)', 'rgba(255,210,130,0.3)'],
    spark: ['rgba(255,255,255,0.5)', 'rgba(255,230,150,0.6)']
  }
};

export function ChaosParticles({ chaosEnergy = 0, riftStage = 0, enabled = true }) {
  const canvasRef = useRef(null);
  const rafRef = useRef(null);
  const particlesRef = useRef([]);
  const mouseRef = useRef({ x: 0, y: 0 });
  const [portalRoot, setPortalRoot] = useState(null);

  // 1. Создаём изолированный контейнер в <body>
  useEffect(() => {
    const root = document.createElement('div');
    root.style.position = 'fixed';
    root.style.inset = '0';
    root.style.zIndex = '1';
    root.style.pointerEvents = 'none';
    root.style.overflow = 'hidden';
    document.body.appendChild(root);
    setPortalRoot(root);

    return () => {
      if (document.body.contains(root)) document.body.removeChild(root);
    };
  }, []);

  // 2. Отслеживание мыши
  useEffect(() => {
    const handleMove = (e) => {
      mouseRef.current.x = e.clientX;
      mouseRef.current.y = e.clientY;
    };
    document.addEventListener('mousemove', handleMove, { passive: true });
    return () => document.removeEventListener('mousemove', handleMove);
  }, []);

  // 3. Создание частицы
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
      color: CONFIG.colors[type][Math.floor(Math.random() * 2)],
      phase: Math.random() * Math.PI * 2,
      life: cfg.immortal ? 1 : cfg.lifeMin + Math.random() * (cfg.lifeMax - cfg.lifeMin),
      isRespawning: !cfg.immortal,
      jitter: 0.01
    };
  }, []);

  // 4. Инициализация массива частиц
  const initParticles = useCallback((w, h) => {
    const arr = [];
    const total = Math.min(CONFIG.total, Math.floor((w * h) / 40000));
    for (let i = 0; i < total; i++) {
      const r = Math.random();
      let type = r < CONFIG.types.dust.ratio ? 'dust' 
               : r < CONFIG.types.dust.ratio + CONFIG.types.glow.ratio ? 'glow' 
               : 'spark';
      arr.push(createParticle(w, h, type));
    }
    return arr;
  }, [createParticle]);

  // 5. Анимационный цикл
  const animate = useCallback(() => {
    try {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      const w = canvas.width;
      const h = canvas.height;
      const { x: mx, y: my } = mouseRef.current;
      const { radius: mr, force: mf, friction } = CONFIG.mouse;
      const chaosMult = 1 + (chaosEnergy / 100) * 0.3;

      ctx.clearRect(0, 0, w, h);

      particlesRef.current.forEach(p => {
        const cfg = CONFIG.types[p.type];
        const dx = p.x - mx;
        const dy = p.y - my;
        const dist = Math.hypot(dx, dy);

        if (dist < mr && dist > 1) {
          const push = mf * (1 - dist / mr);
          p.vx += (dx / dist) * push;
          p.vy += (dy / dist) * push;
        }

        p.vx *= friction;
        p.vy *= friction;

        p.x += p.vx * chaosMult;
        p.y += p.vy * chaosMult;

        p.phase += 0.008;
        p.x += Math.sin(p.phase) * 0.2;
        p.y += Math.cos(p.phase * 0.6) * 0.2;
        p.x += (Math.random() - 0.5) * p.jitter;
        p.y += (Math.random() - 0.5) * p.jitter;

        const m = 5;
        if (p.x < m) { p.vx += 0.05; p.x = m; }
        if (p.x > w - m) { p.vx -= 0.05; p.x = w - m; }
        if (p.y < m) { p.vy += 0.05; p.y = m; }
        if (p.y > h - m) { p.vy -= 0.05; p.y = h - m; }

        if (cfg.immortal) {
          p.currentOpacity = cfg.opacity[0] + Math.sin(Date.now() * 0.001 + p.phase) * 0.02;
        } else {
          if (p.isRespawning) {
            p.currentOpacity += 0.012;
            if (p.currentOpacity >= p.targetOpacity) {
              p.currentOpacity = p.targetOpacity;
              p.isRespawning = false;
            }
          } else {
            p.life -= 0.002;
            if (p.life <= 0.2) p.currentOpacity -= 0.008;
            if (p.currentOpacity <= 0.01) {
              p.x = Math.random() * w; p.y = Math.random() * h;
              p.life = cfg.lifeMin + Math.random() * (cfg.lifeMax - cfg.lifeMin);
              p.currentOpacity = 0; p.isRespawning = true;
              p.vx = (Math.random() - 0.5) * cfg.speed;
              p.vy = (Math.random() - 0.5) * cfg.speed;
            }
          }
        }
        p.currentOpacity = Math.max(0.02, Math.min(1, p.currentOpacity));

        if (p.type === 'spark' && !p.isRespawning && p.currentOpacity > 0.1) {
          if (riftStage >= 3) p.currentOpacity += Math.sin(Date.now() * 0.005 + p.phase) * 0.03;
          if (Math.random() < 0.002) { p.vx += (Math.random()-0.5)*0.3; p.vy += (Math.random()-0.5)*0.3; }
          ctx.beginPath();
          ctx.strokeStyle = p.color.replace(/[\d.]+\)$/, `${p.currentOpacity * 0.3})`);
          ctx.lineWidth = 1;
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(p.x - p.vx * 4, p.y - p.vy * 4);
          ctx.stroke();
        }

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        if (p.type !== 'dust') {
          const g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.size * 2);
          g.addColorStop(0, p.color.replace(/[\d.]+\)$/, `${p.currentOpacity})`));
          g.addColorStop(1, 'transparent');
          ctx.fillStyle = g;
        } else {
          ctx.fillStyle = p.color.replace(/[\d.]+\)$/, `${p.currentOpacity})`);
        }
        ctx.fill();
      });

      rafRef.current = requestAnimationFrame(animate);
    } catch (e) {
      console.error('❌ Particles error:', e);
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    }
  }, [chaosEnergy, riftStage]);

  // 6. Resize + управление циклом
  useEffect(() => {
    if (!enabled || !portalRoot) return;
    const canvas = canvasRef.current;
    if (!canvas) return;

    const resize = () => { 
      canvas.width = window.innerWidth; 
      canvas.height = window.innerHeight; 
      particlesRef.current = initParticles(canvas.width, canvas.height); 
    };
    
    resize();
    window.addEventListener('resize', resize);
    rafRef.current = requestAnimationFrame(animate);
    return () => { 
      window.removeEventListener('resize', resize); 
      if (rafRef.current) cancelAnimationFrame(rafRef.current); 
    };
  }, [animate, initParticles, enabled, portalRoot]);

  if (!enabled || !portalRoot) return null;

  return createPortal(
    <canvas ref={canvasRef} className="chaos-particles-canvas" />,
    portalRoot
  );
}