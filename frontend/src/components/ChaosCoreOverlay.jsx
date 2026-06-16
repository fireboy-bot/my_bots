import { useEffect, useRef, useCallback } from 'react';
import './ChaosCoreOverlay.css';

// 🔹 Маппер: старая система → новая (по промпту креативщика)
const STATE_MAP = {
  dormant: 'idle',
  awakened: 'awakening',
  active: 'unstable',
  overload: 'critical'
};

export function ChaosCoreOverlay({ chaosEnergy = 0, riftStage = 0 }) {
  const canvasRef = useRef(null);
  const rafRef = useRef(null);
  const cracksRef = useRef([]);
  const lastFrameRef = useRef(0);

  // 🔹 Преобразуем стадию в визуальное состояние
  const getVisualState = useCallback(() => {
    const legacyState = riftStage >= 3 ? 'overload' : riftStage === 2 ? 'active' : riftStage === 1 ? 'awakened' : 'dormant';
    return STATE_MAP[legacyState];
  }, [riftStage]);

  // 🔹 Генерация трещин (заготовка под креативщика)
  const generateCracks = useCallback(() => {
    const cracks = [];
    const count = riftStage === 3 ? 12 : riftStage === 2 ? 7 : riftStage === 1 ? 3 : 0;
    for (let i = 0; i < count; i++) {
      cracks.push({
        angle: (Math.PI * 2 * i) / count + (Math.random() - 0.5) * 0.5,
        length: 0,
        maxLength: 0.3 + Math.random() * 0.7,
        width: 1 + Math.random() * 2,
        progress: 0,
        speed: 0.005 + Math.random() * 0.01
      });
    }
    return cracks;
  }, [riftStage]);

  // 🔹 Цикл анимации (requestAnimationFrame)
  const animate = useCallback((timestamp) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;
    const cx = w / 2;
    const cy = h / 2;

    ctx.clearRect(0, 0, w, h);

    // Инициализация трещин при первой отрисовке или смене стадии
    if (cracksRef.current.length === 0) {
      cracksRef.current = generateCracks();
    }

    // Отрисовка трещин
    ctx.strokeStyle = 'rgba(123, 92, 255, 0.8)';
    ctx.lineCap = 'round';
    ctx.shadowBlur = 8;
    ctx.shadowColor = 'rgba(255, 255, 255, 0.4)';

    cracksRef.current.forEach(crack => {
      if (crack.progress < 1) {
        crack.progress += crack.speed;
        crack.length = crack.maxLength * crack.progress;
      }

      const x2 = cx + Math.cos(crack.angle) * crack.length * Math.max(w, h);
      const y2 = cy + Math.sin(crack.angle) * crack.length * Math.max(w, h);

      ctx.lineWidth = crack.width * (0.5 + 0.5 * Math.sin(timestamp * 0.005));
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(x2, y2);
      ctx.stroke();
    });

    // Эффекты в зависимости от стадии
    const state = getVisualState();
    if (state === 'unstable' || state === 'critical') {
      ctx.fillStyle = `rgba(92, 225, 255, ${0.05 * chaosEnergy / 100})`;
      ctx.fillRect(0, 0, w, h);
    }

    rafRef.current = requestAnimationFrame(animate);
  }, [chaosEnergy, riftStage, getVisualState, generateCracks]);

  // 🔹 Ресайз и запуск/остановка цикла
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener('resize', resize);

    rafRef.current = requestAnimationFrame(animate);

    return () => {
      window.removeEventListener('resize', resize);
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      cracksRef.current = [];
    };
  }, [animate]);

  // 🔹 CSS-переменные для shake и overlay
  useEffect(() => {
    const root = document.documentElement;
    const state = getVisualState();
    const intensity = state === 'idle' ? 0 : state === 'awakening' ? 0.1 : state === 'unstable' ? 0.3 : 0.6;
    const darkness = state === 'idle' ? 0 : Math.min(chaosEnergy / 100, 0.4);
    
    root.style.setProperty('--chaos-shake', `${intensity}px`);
    root.style.setProperty('--chaos-overlay', `rgba(10, 12, 20, ${darkness})`);
    root.style.setProperty('--chaos-core-pulse', state === 'critical' ? '0.8s' : '1.5s');
  }, [chaosEnergy, riftStage, getVisualState]);

  return (
    <div className="chaos-overlay" aria-hidden="true">
      <canvas ref={canvasRef} className="chaos-canvas" />
      <div className="chaos-darken" />
    </div>
  );
}