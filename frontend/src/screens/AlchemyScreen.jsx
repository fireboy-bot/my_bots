import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FloatingNav } from '../components/FloatingNav';
import { CharacterCard } from '../components/CharacterCard';
import { botApi } from '../adapters/botAdapter';
import './AlchemyScreen.css';

// 🔹 Конфиг алхимии (синхронизируй с alchemy.py)
const ALCHEMY_CONFIG = {
  bravery_potion: {
    id: "bravery_potion", name: "💚 Зелье Смелости",
    description: "Следующая задача: +50 за успех, −30 за ошибку!",
    icon: "💚", cost: 150, type: "one_time_risk", unlocks_after: "subtraction"
  },
  chaos_cup: {
    id: "chaos_cup", name: "🔴 Кубок Хаоса",
    description: "Следующая задача: +100 за успех, −80 за ошибку!",
    icon: "🔴", cost: 250, type: "one_time_risk", unlocks_after: "multiplication"
  },
  dice_of_fate: {
    id: "dice_of_fate", name: "🎲 Кубик Судьбы",
    description: "Перед следующей задачей будет брошен кубик судьбы!",
    icon: "🎲", cost: 180, type: "one_time_risk", unlocks_after: "division"
  },
  madness_potion: {
    id: "madness_potion", name: "🌀 Зелье Безумия",
    description: "На уровне: ошибки = +20, правильные = −10",
    icon: "🌀", cost: 200, type: "level_wide_risk", unlocks_after: "completed_normal_game"
  }
};

export function AlchemyScreen({ userId = "331113480", onBack }) {
  const navigate = useNavigate();
  const [inventory, setInventory] = useState([]);
  const [playerStats, setPlayerStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [message, setMessage] = useState(null);
  const [alchemistPhrase, setAlchemistPhrase] = useState('');

  useEffect(() => {
    const loadData = async () => {
      try {
        const profile = await botApi.getPlayerProfile(userId);
        setPlayerStats(profile);
        setInventory(profile?.inventory || []);
        
        const phrases = [
          "💀 «ХА-ХА-ХА! Что будем варить сегодня, а?»",
          "💀 «Риск — благородное дело... если ты не боишься потерять всё!»",
          "💀 «Мои зелья не для слабых духом, сударыня...»"
        ];
        setAlchemistPhrase(phrases[Math.floor(Math.random() * phrases.length)]);
      } catch (error) {
        console.error('❌ Error loading alchemy:', error);
      } finally {
        setLoading(false);
      }
    };
    if (userId) loadData();
  }, [userId]);

  const handleCraft = async (itemId) => {
    if (processing) return;
    const item = ALCHEMY_CONFIG[itemId];
    
    // 🔹 Проверка разблокировки ТОЛЬКО по прогрессу (БЕЗ upkeep!)
    const zones = playerStats?.unlocked_zones || [];
    const completed = playerStats?.completed_normal_game || false;
    const isUnlocked = !item.unlocks_after || 
      (item.unlocks_after === 'subtraction' && zones.includes('subtraction')) ||
      (item.unlocks_after === 'multiplication' && zones.includes('multiplication')) ||
      (item.unlocks_after === 'division' && zones.includes('division')) ||
      (item.unlocks_after === 'completed_normal_game' && completed);
    
    if (!isUnlocked) {
      setMessage({ type: 'error', text: '❌ Рецепт ещё не открыт! Исследуй Числяндию.' });
      setTimeout(() => setMessage(null), 4000);
      return;
    }
    
    const balance = playerStats?.score_balance || 0;
    if (balance < item.cost) {
      setMessage({ type: 'error', text: `❌ Недостаточно золота! Нужно ${item.cost} 🪙` });
      setTimeout(() => setMessage(null), 3000);
      return;
    }
    
    if (item.type === 'one_time_risk' && inventory.includes(itemId)) {
      setMessage({ type: 'error', text: `❌ ${item.name} уже создан!` });
      setTimeout(() => setMessage(null), 3000);
      return;
    }
    
    setProcessing(true);
    try {
      const result = await botApi.craftAlchemy?.(userId, itemId) || { success: true, message: `✨ Создано: ${item.name}!` };
      if (result.success) {
        setMessage({ type: 'success', text: result.message + (result.activation ? `\n\n${result.activation}` : '') });
        const profile = await botApi.getPlayerProfile(userId);
        setInventory(profile?.inventory || []);
        setPlayerStats(profile);
      } else {
        setMessage({ type: 'error', text: result.message });
      }
    } catch (e) {
      console.error('❌ Error:', e);
      setMessage({ type: 'error', text: '⚠️ Ошибка' });
    }
    setProcessing(false);
    setTimeout(() => setMessage(null), 5000);
  };

  const handleBack = () => { if (onBack) onBack(); else navigate('/game/shop/' + userId); };

  if (loading) return <div className="alchemy-screen"><div className="loading">💀 Лавка Безумца открывается...</div></div>;

  return (
    <div className="alchemy-screen">
      <div className="alchemy-screen__header">
        <button className="back-btn" onClick={handleBack}>← Назад</button>
        <h1>⚗️ ЛАВКА БЕЗУМЦА</h1>
      </div>

      {/* 🔹 АВАТАР АЛХИМИКА */}
      <CharacterCard name="Алхимик" image="/alchemist_calm.jpg" mood="calm" />
      
      {/* 🔹 СООБЩЕНИЕ АЛХИМИКА */}
      <div className="alchemist-message">
        <p dangerouslySetInnerHTML={{ __html: alchemistPhrase }} />
      </div>

      {/* 🔹 ПОДСКАЗКА: алхимия НЕ зависит от upkeep */}
      <div className="alchemy-tip">
        💀 <i>«ХА-ХА-ХА! Мои зелья работают всегда — даже если замок спит! Но рискни... если осмелишься!»</i>
      </div>

      {/* 🔹 СПИСОК РЕЦЕПТОВ */}
      <div className="alchemy-list">
        {Object.values(ALCHEMY_CONFIG).map(item => {
          const zones = playerStats?.unlocked_zones || [];
          const completed = playerStats?.completed_normal_game || false;
          const isUnlocked = !item.unlocks_after || 
            (item.unlocks_after === 'subtraction' && zones.includes('subtraction')) ||
            (item.unlocks_after === 'multiplication' && zones.includes('multiplication')) ||
            (item.unlocks_after === 'division' && zones.includes('division')) ||
            (item.unlocks_after === 'completed_normal_game' && completed);
          
          const inInventory = inventory.includes(item.id);
          const balance = playerStats?.score_balance || 0;
          const canAfford = balance >= item.cost;
          const canCraft = isUnlocked && canAfford && (item.type !== 'one_time_risk' || !inInventory);

          return (
            <div key={item.id} className={`alchemy-card ${!isUnlocked ? 'locked' : ''}`}>
              <div className="alchemy-header">
                <span className="alchemy-icon">{item.icon}</span>
                <div>
                  <strong>{item.name}</strong>
                  <p className="alchemy-desc">{item.description}</p>
                </div>
              </div>
              <div className="alchemy-stats">
                <div><span>Цена:</span> <strong>{item.cost} 🪙</strong></div>
                <div><span>Тип:</span> <strong>{item.type === 'one_time_risk' ? '⚡ Одноразовый' : '🌀 На уровень'}</strong></div>
                <div><span>Статус:</span> <strong className={isUnlocked ? 'ok' : 'locked'}>
                  {isUnlocked ? (inInventory ? '✅ В инвентаре' : '🔓 Открыт') : '🔒 Закрыт'}
                </strong></div>
              </div>
              {isUnlocked && (
                <button className={`craft-btn ${canCraft ? '' : 'disabled'}`}
                  onClick={() => handleCraft(item.id)} disabled={processing || !canCraft}>
                  {inInventory ? '✅ Уже создан' : `⚗️ Создать за ${item.cost} 🪙`}
                </button>
              )}
            </div>
          );
        })}
      </div>

      {message && <div className={`message message--${message.type} alchemy-message`}>{message.text}</div>}
      
      <FloatingNav userId={userId} showBack={true} showMenu={true} onBack={handleBack} theme="game" />
    </div>
  );
}