import './ChaosArtifact.css';

export function ChaosArtifact({ state = 'dormant', energy = 0, onStateChange }) {
  // 🔹 Конфигурация состояний (обновлённые цвета по фидбеку)
  const config = {
    dormant:   { icon: '💤', label: 'Спящий',   color: '#22c55e', glow: 'rgba(34, 197, 94, 0.4)' },
    awakened:  { icon: '✨', label: 'Пробуждён', color: '#22d3ee', glow: 'rgba(34, 211, 238, 0.5)' }, // 🔹 cyan вместо лайма
    active:    { icon: '⚡', label: 'Активен',   color: '#eab308', glow: 'rgba(234, 179, 8, 0.6)' },
    overload:  { icon: '🌋', label: 'Перегрузка!', color: '#ef4444', glow: 'rgba(168, 85, 247, 0.7)' } // 🔹 фиолет+красный
  };
  
  const { icon, label, color, glow } = config[state] || config.dormant;
  const energyClamped = Math.max(0, Math.min(100, energy));
  
  // 🔹 Динамические классы
  const stateClass = `chaos-artifact--${state}`;
  const energyClass = energyClamped > 75 ? 'energy-high' : energyClamped > 40 ? 'energy-mid' : 'energy-low';
  
  // 🔹 Задержка реакции (0.2 сек "думает")
  const transitionDelay = '0.2s';
  
  return (
    <div 
      className={`chaos-artifact ${stateClass} ${energyClass}`}
      style={{ '--transition-delay': transitionDelay }}
    >
      {/* 🔹 Внешнее свечение */}
      <div className="chaos-glow-outer" style={{ '--glow-color': glow }} />
      
      {/* 🔹 Ядро артефакта */}
      <div className="chaos-core">
        {/* 🔹 Базовый градиент */}
        <div className="chaos-gradient" style={{ '--core-color': color }} />
        
        {/* 🔹 ВНУТРЕННЕЕ ДВИЖЕНИЕ (энергия внутри) */}
        <div className="chaos-inner-flow" />
        
        {/* 🔹 Иконка состояния */}
        <span className="chaos-icon">{icon}</span>
        
        {/* 🔹 Микротрещины (active/overload) */}
        {(state === 'active' || state === 'overload') && (
          <div className="chaos-cracks">
            <div className="crack crack-1" />
            <div className="crack crack-2" />
            <div className="crack crack-3" />
            {/* 🔹 Импульс по трещинам */}
            <div className="crack-impulse" />
          </div>
        )}
        
        {/* 🔹 Микро-частицы вокруг ядра (3-6 шт) */}
        <div className="chaos-particles">
          {[...Array(5)].map((_, i) => (
            <span 
              key={i} 
              className="particle" 
              style={{ 
                '--delay': `${i * 0.4}s`,
                '--size': `${2 + Math.random() * 3}px`,
                '--color': state === 'overload' ? '#ef4444' : color
              }} 
            />
          ))}
        </div>
        
        {/* 🔹 Вибрация + глитч для overload */}
        {state === 'overload' && (
          <>
            <div className="chaos-vibrate" />
            <div className="chaos-glitch" />
          </>
        )}
      </div>
      
      {/* 🔹 Энергия: полоса + текст */}
      <div className="chaos-energy">
        <div className="energy-bar">
          <div 
            className="energy-fill" 
            style={{ 
              width: `${energyClamped}%`,
              backgroundColor: color,
              boxShadow: `0 0 12px ${color}`,
              transition: `width ${transitionDelay} ease, background-color ${transitionDelay} ease`
            }} 
          />
        </div>
        <span className="energy-text">{energyClamped}%</span>
      </div>
      
      {/* 🔹 Подпись состояния */}
      <span className="chaos-label">{label}</span>
    </div>
  );
}