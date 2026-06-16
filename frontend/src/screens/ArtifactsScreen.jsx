import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FloatingNav } from '../components/FloatingNav';
import { CharacterCard } from '../components/CharacterCard';
import { botApi } from '../adapters/botAdapter';
import './ArtifactsScreen.css';

// 🔹 Конфиг артефактов (синхронизируй с items.py)
const ARTIFACTS_CONFIG = {
  artifact_luck: {
    id: "artifact_luck", name: "🍀 Артефакт Удачи",
    description: "Постоянный бонус к очкам за правильные ответы",
    icon: "🍀", base_price: 500, max_level: 10,
    effect: "score_bonus", base_value: 0.05, per_level: 0.05, max_value: 0.40,
    cost_multiplier: 1.4, requires_upkeep: true
  },
  artifact_power: {
    id: "artifact_power", name: "⚡ Артефакт Силы",
    description: "Снижение потери очков при ошибке",
    icon: "⚡", base_price: 500, max_level: 10,
    effect: "penalty_reduction", base_value: 0.10, per_level: 0.10, max_value: 0.75,
    cost_multiplier: 1.4, requires_upkeep: true
  },
  artifact_wisdom: {
    id: "artifact_wisdom", name: "🧠 Артефакт Мудрости",
    description: "Дополнительные подсказки в бою с боссом",
    icon: "🧠", base_price: 750, max_level: 10,
    effect: "boss_hints", base_value: 1, per_level: 1, max_value: 10,
    cost_multiplier: 1.45, requires_upkeep: true
  }
};

export function ArtifactsScreen({ userId = "331113480", onBack }) {
  const navigate = useNavigate();
  const [artifacts, setArtifacts] = useState({});
  const [playerStats, setPlayerStats] = useState(null);
  const [castleInfo, setCastleInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [message, setMessage] = useState(null);
  const [vladimirPhrase, setVladimirPhrase] = useState('');

  useEffect(() => {
    const loadData = async () => {
      try {
        const [profile, castle] = await Promise.all([
          botApi.getPlayerProfile(userId),
          botApi.getCastleInfo(userId)
        ]);
        setPlayerStats(profile);
        setCastleInfo(castle);
        setArtifacts(profile?.artifact_upgrades || {});
        
        // 🔹 Правильная проверка: замок открыт?
        const isCastleUnlocked = profile?.defeated_bosses?.includes('final_boss') || 
                                 profile?.completed_normal_game || false;
        
        if (!isCastleUnlocked) {
          setVladimirPhrase("🎩 «Артефакты ждут своего часа, сударыня. Победите Финального Владыку, чтобы открыть их силу.»");
        } else if (!castle?.bonuses_active) {
          setVladimirPhrase("🎩 «Артефакты дремлют, сударыня. Оплатите upkeep замка, и они обретут силу.»");
        } else {
          setVladimirPhrase("🎩 «Ваши артефакты сияют, сударыня. Инвестиции в мудрость всегда окупаются.»");
        }
      } catch (error) {
        console.error('❌ Error loading artifacts:', error);
      } finally {
        setLoading(false);
      }
    };
    if (userId) loadData();
  }, [userId]);

  const handleUpgrade = async (artifactId) => {
    if (processing) return;
    const artifact = ARTIFACTS_CONFIG[artifactId];
    const level = artifacts[artifactId]?.level || 0;
    
    // 🔹 Правильная проверка: замок открыт И upkeep оплачен
    const isCastleUnlocked = playerStats?.defeated_bosses?.includes('final_boss') || 
                             playerStats?.completed_normal_game || false;
    const artifactsWork = isCastleUnlocked && castleInfo?.bonuses_active;
    
    if (!isCastleUnlocked) {
      setMessage({ type: 'error', text: '❌ Артефакты откроются после победы над Финальным Владыкой!' });
      setTimeout(() => setMessage(null), 4000);
      return;
    }
    
    if (artifact.requires_upkeep && !artifactsWork) {
      setMessage({ type: 'error', text: '❌ Upkeep замка не оплачен! Артефакты не активны.' });
      setTimeout(() => setMessage(null), 4000);
      return;
    }
    
    const price = level === 0 ? artifact.base_price : Math.floor(artifact.base_price * Math.pow(artifact.cost_multiplier, level));
    if ((playerStats?.score_balance || 0) < price) {
      setMessage({ type: 'error', text: `❌ Недостаточно золота! Нужно ${price.toLocaleString()} 🪙` });
      setTimeout(() => setMessage(null), 3000);
      return;
    }
    
    setProcessing(true);
    try {
      const result = await botApi.upgradeArtifact?.(userId, artifactId) || { success: true, message: `✅ ${artifact.name} улучшен!` };
      if (result.success) {
        setMessage({ type: 'success', text: result.message });
        const profile = await botApi.getPlayerProfile(userId);
        setPlayerStats(profile);
        setArtifacts(profile?.artifact_upgrades || {});
      } else {
        setMessage({ type: 'error', text: result.message });
      }
    } catch (e) {
      console.error('❌ Error:', e);
      setMessage({ type: 'error', text: '⚠️ Ошибка' });
    }
    setProcessing(false);
    setTimeout(() => setMessage(null), 4000);
  };

  const handleBack = () => { if (onBack) onBack(); else navigate('/game/shop/' + userId); };

  if (loading) return <div className="artifacts-screen"><div className="loading">✨ Загрузка артефактов...</div></div>;

  const balance = playerStats?.score_balance || 0;
  const isCastleUnlocked = playerStats?.defeated_bosses?.includes('final_boss') || 
                           playerStats?.completed_normal_game || false;
  const artifactsWork = isCastleUnlocked && castleInfo?.bonuses_active;

  return (
    <div className="artifacts-screen">
      <div className="artifacts-screen__header">
        <button className="back-btn" onClick={handleBack}>← Назад</button>
        <h1>🔮 АРТЕФАКТЫ</h1>
      </div>

      {/* 🔹 АВАТАР ВЛАДИМИРА */}
      <CharacterCard name="Владимир" image="/vladimir_calm.jpg" mood="calm" />
      
      {/* 🔹 СООБЩЕНИЕ ВЛАДИМИРА */}
      <div className="vladimir-message">
        <p dangerouslySetInnerHTML={{ __html: vladimirPhrase }} />
      </div>

      {/* 🔹 ПРЕДУПРЕЖДЕНИЯ */}
      {!isCastleUnlocked && (
        <div className="castle-locked-banner">
          🔒 Артефакты станут доступны после победы над Финальным Владыкой
        </div>
      )}
      {isCastleUnlocked && !artifactsWork && (
        <div className="upkeep-warning-banner">
          ⚠️ <strong>Upkeep замка не оплачен!</strong> Артефакты не активны.
        </div>
      )}

      {/* 🔹 ПОДСКАЗКА ПРО ТИП БОНУСА */}
      <div className="bonus-type-hint">
        💡 <i>Бонусы артефактов применяются к <strong>очкам за задачи</strong>, а не к золоту. Золото тратится на покупки!</i>
      </div>

      {/* 🔹 СПИСОК АРТЕФАКТОВ */}
      <div className="artifacts-list">
        {Object.values(ARTIFACTS_CONFIG).map(artifact => {
          const level = artifacts[artifact.id]?.level || 0;
          const price = level === 0 ? artifact.base_price : Math.floor(artifact.base_price * Math.pow(artifact.cost_multiplier, level));
          const bonus = Math.min(artifact.base_value + (artifact.per_level * level), artifact.max_value);
          const canAfford = balance >= price;
          const isMaxed = level >= artifact.max_level;
          const isActive = !artifact.requires_upkeep || artifactsWork;

          return (
            <div key={artifact.id} className="artifact-card">
              <div className="artifact-header">
                <span className="artifact-icon">{artifact.icon}</span>
                <div>
                  <strong>{artifact.name}</strong>
                  <p className="artifact-desc">{artifact.description}</p>
                </div>
              </div>
              <div className="artifact-stats">
                <div><span>Уровень:</span> <strong>{level}/{artifact.max_level}</strong></div>
                <div><span>Бонус:</span> <strong>+{Math.round(bonus * 100)}%</strong></div>
                <div><span>Статус:</span> <strong className={isActive && level > 0 ? 'ok' : 'warn'}>
                  {isActive ? (level > 0 ? '✅ АКТИВЕН' : '⬜ НЕ КУПЛЕН') : '❌ НЕ АКТИВЕН'}
                </strong></div>
              </div>
              {!isMaxed ? (
                <button className={`upgrade-btn ${canAfford && isActive ? '' : 'disabled'}`}
                  onClick={() => handleUpgrade(artifact.id)} disabled={processing || !canAfford || !isActive}>
                  {level === 0 ? `🛒 Купить за ${price.toLocaleString()} 🪙` : `⬆️ Улучшить за ${price.toLocaleString()} 🪙`}
                </button>
              ) : (
                <div className="maxed">⚡ МАКСИМАЛЬНЫЙ УРОВЕНЬ!</div>
              )}
            </div>
          );
        })}
      </div>

      {message && <div className={`message message--${message.type}`}>{message.text}</div>}
      
      <FloatingNav userId={userId} showBack={true} showMenu={true} onBack={handleBack} theme="game" />
    </div>
  );
}