import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FloatingNav } from '../components/FloatingNav';
import { botApi } from '../adapters/botAdapter';
import './CastleScreen.css';

// 🔹 Декорации из твоего items.py (синхронизируй с ботом!)
const CASTLE_DECORATIONS = [
  { id: "carrot_wall", name: "🥕 Морковки на стене", emoji: "🥕", description: "Уют и мотивация", base_price: 300, cost_multiplier: 1.4, bonus_per_level: 0.02, max_bonus: 0.10 },
  { id: "candles", name: "🕯️ Серебряные подсвечники", emoji: "🕯️", description: "Атмосфера и свет", base_price: 400, cost_multiplier: 1.5, bonus_per_level: 0.03, max_bonus: 0.15 },
  { id: "pythagoras", name: "🖼️ Портрет Пифагора", emoji: "🖼️", description: "Мудрость великих", base_price: 500, cost_multiplier: 1.6, bonus_per_level: 0.04, max_bonus: 0.20 },
  { id: "formula_wallpaper", name: "📐 Обои «Сад формул»", emoji: "📐", description: "Красота математики", base_price: 600, cost_multiplier: 1.7, bonus_per_level: 0.05, max_bonus: 0.25 },
  { id: "crystal_chandelier", name: "💡 Хрустальная люстра", emoji: "💡", description: "Роскошь и вдохновение", base_price: 800, cost_multiplier: 1.8, bonus_per_level: 0.06, max_bonus: 0.30 },
  { id: "textbook_throne", name: "🪑 Трон из учебников", emoji: "🪑", description: "Власть знаний", base_price: 1000, cost_multiplier: 2.0, bonus_per_level: 0.08, max_bonus: 0.40 },
  { id: "star_dome", name: "🌟 Звёздный купол", emoji: "🌟", description: "Бесконечность возможностей", base_price: 1500, cost_multiplier: 2.2, bonus_per_level: 0.10, max_bonus: 0.50 },
  { id: "vladimir_monocle", name: "🎩 Монокль Владимира", emoji: "🎩", description: "Элегантность дворецкого", base_price: 2000, cost_multiplier: 2.5, bonus_per_level: 0.12, max_bonus: 0.60 },
];

export function CastleScreen({ userId = "331113480", onBack }) {
  const navigate = useNavigate();
  
  // 🔹 Состояния
  const [castleInfo, setCastleInfo] = useState(null);
  const [playerStats, setPlayerStats] = useState(null);
  const [accessLevel, setAccessLevel] = useState('locked'); // 'locked' | 'preview' | 'full'
  const [upkeepDays, setUpkeepDays] = useState(1);
  const [selectedDecoration, setSelectedDecoration] = useState(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [message, setMessage] = useState(null);
  const [vladimirPhrase, setVladimirPhrase] = useState('');

  // 🔹 Загрузка данных
  useEffect(() => {
    const loadData = async () => {
      try {
        const [castle, profile] = await Promise.all([
          botApi.getCastleInfo(userId),
          botApi.getPlayerProfile(userId)
        ]);
        
        setCastleInfo(castle);
        setPlayerStats(profile);
        
        // 🔹 Определяем уровень доступа (как в Python)
        const defeatedBosses = profile?.defeated_bosses || [];
        const completedNormal = profile?.completed_normal_game || false;
        const playerLevel = profile?.level || 1;
        
        if (defeatedBosses.includes('final_boss') || completedNormal) {
          setAccessLevel('full');
        } else if (playerLevel >= 5) {
          setAccessLevel('preview');
        } else {
          setAccessLevel('locked');
        }
        
        // 🔹 Фраза Владимира в зависимости от доступа
        setVladimirPhrase(getVladimirPhrase(accessLevel, castle));
        
      } catch (error) {
        console.error('❌ Error loading castle data:', error);
        setMessage({ type: 'error', text: '⚠️ Ошибка загрузки данных' });
      } finally {
        setLoading(false);
      }
    };
    
    if (userId) {
      loadData();
    }
  }, [userId]);

  // 🔹 Фразы Владимира (синхронизируй с phrase_manager в боте!)
  const getVladimirPhrase = (level, castle) => {
    const phrases = {
      locked: "🎩 «Замок закрыт, сударыня. Вернитесь, когда достигнете 5 уровня. Знания — ключ к дверям.»",
      preview: "🎩 «Замок открыт, сударыня. Но настоящие сокровища ждут после победы над Финальным Владыкой. Пока — лишь тизер величия.»",
      full: "🎩 «Добро пожаловать домой, сударыня. Замок живёт, пока вы заботитесь о нём. Упкейп — это не расход, это инвестиция в ваше величие.»"
    };
    
    // 🔹 Если upkeep не оплачен — добавляем напоминание
    if (level === 'full' && !castle?.bonuses_active) {
      return phrases.full + "\n\n⚠️ <i>Upkeep не оплачен! Бонусы не активны.</i>";
    }
    
    return phrases[level] || phrases.locked;
  };

  // 🔹 Оплата upkeep
  const handlePayUpkeep = async () => {
    if (processing || accessLevel !== 'full') return;
    
    setProcessing(true);
    setMessage(null);
    
    try {
      const result = await botApi.payCastleUpkeep(userId, upkeepDays);
      
      if (result.success) {
        setMessage({ type: 'success', text: result.message });
        // Обновляем данные
        const [castle, profile] = await Promise.all([
          botApi.getCastleInfo(userId),
          botApi.getPlayerProfile(userId)
        ]);
        setCastleInfo(castle);
        setPlayerStats(profile);
        setVladimirPhrase(getVladimirPhrase('full', castle));
      } else {
        setMessage({ type: 'error', text: result.message });
      }
    } catch (error) {
      console.error('❌ Error paying upkeep:', error);
      setMessage({ type: 'error', text: '⚠️ Ошибка соединения' });
    }
    
    setProcessing(false);
    setTimeout(() => setMessage(null), 4000);
  };

  // 🔹 Покупка/улучшение декорации
  const handleBuyDecoration = async (decoration) => {
    if (processing || accessLevel !== 'full') return;
    
    const currentLevel = castleInfo?.decoration_upgrades?.[decoration.id] || 0;
    const price = currentLevel === 0 
      ? decoration.base_price 
      : Math.floor(decoration.base_price * Math.pow(decoration.cost_multiplier, currentLevel));
    
    if ((playerStats?.score_balance || 0) < price) {
      setMessage({ type: 'error', text: `❌ Недостаточно золота! Нужно ${price.toLocaleString()} 🪙` });
      setTimeout(() => setMessage(null), 3000);
      return;
    }
    
    setProcessing(true);
    
    try {
      // 🔹 В реальном боте: engine.castle.upgrade_decoration()
      // Здесь — имитация через botApi (добавь эндпоинт в Flask если нужно)
      const result = await botApi.upgradeDecoration(userId, decoration.id);
      
      if (result.success) {
        setMessage({ type: 'success', text: result.message });
        // Обновляем данные
        const [castle, profile] = await Promise.all([
          botApi.getCastleInfo(userId),
          botApi.getPlayerProfile(userId)
        ]);
        setCastleInfo(castle);
        setPlayerStats(profile);
      } else {
        setMessage({ type: 'error', text: result.message });
      }
    } catch (error) {
      console.error('❌ Error upgrading decoration:', error);
      setMessage({ type: 'error', text: '⚠️ Ошибка улучшения' });
    }
    
    setProcessing(false);
    setSelectedDecoration(null);
    setTimeout(() => setMessage(null), 4000);
  };

  // 🔹 Навигация
  const handleBack = () => {
    if (onBack) {
      onBack();
    } else {
      navigate('/game/menu/' + userId);
    }
  };

  const handleChatWithVladimir = () => {
    // 🔹 Имитация "поболтать" — случайная фраза
    const idlePhrases = [
      "🎩 «Чай, сударыня? Или, может, кофе для ясности ума?»",
      "🎩 «Замок хранит секреты. Но не все готовы их услышать.»",
      "🎩 «Вы прогрессируете. Это... приятно.»",
      "🎩 «Математика — это язык вселенной. Вы уже начали его понимать.»"
    ];
    setMessage({ type: 'system', text: idlePhrases[Math.floor(Math.random() * idlePhrases.length)] });
    setTimeout(() => setMessage(null), 4000);
  };

  const handleSecretRoom = () => {
    // 🔹 Заглушка — в реальном боте: переход к secret_room.py
    setMessage({ type: 'system', text: "🗝️ <i>«Тайная комната... пока закрыта. Но вы на правильном пути.»</i>" });
    setTimeout(() => setMessage(null), 4000);
  };

  // 🔹 Хелпер: цена следующего уровня декорации
  const getDecorationPrice = (decoration, currentLevel) => {
    if (currentLevel === 0) return decoration.base_price;
    return Math.floor(decoration.base_price * Math.pow(decoration.cost_multiplier, currentLevel));
  };

  // 🔹 Хелпер: бонус декорации на текущем уровне
  const getDecorationBonus = (decoration, currentLevel) => {
    if (currentLevel === 0) return decoration.bonus_per_level;
    const bonus = decoration.bonus_per_level + (decoration.bonus_per_level * currentLevel);
    return Math.min(bonus, decoration.max_bonus);
  };

  // 🔹 Скелетон загрузки
  if (loading) {
    return (
      <div className="castle-screen">
        <div className="castle-screen__loading">
          <div className="loading-spinner">🏰</div>
          <p>Замок просыпается...</p>
        </div>
        <FloatingNav 
          userId={userId}
          showBack={true}
          showMenu={true}
          showSettings={false}
          onBack={handleBack}
          theme="game"
        />
      </div>
    );
  }

  // 🔹 ЗАМОК ЗАКРЫТ (до 5 уровня)
  if (accessLevel === 'locked') {
    return (
      <div className="castle-screen">
        <div className="castle-screen__header">
          <button className="back-btn" onClick={handleBack}>← Назад</button>
          <h1>🔒 ЗАМОК</h1>
        </div>
        
        <div className="vladimir-message vladimir-message--locked">
          <div className="vladimir-avatar">🎩</div>
          <p dangerouslySetInnerHTML={{ __html: vladimirPhrase }} />
        </div>
        
        <div className="castle-locked-visual">
          <span className="lock-emoji">🔐</span>
          <p className="lock-text">Доступен с 5 уровня</p>
          <p className="lock-subtext">Продолжай решать задачи!</p>
        </div>
        
        <FloatingNav 
          userId={userId}
          showBack={true}
          showMenu={true}
          showSettings={false}
          onBack={handleBack}
          theme="game"
        />
      </div>
    );
  }

  // 🔹 ПРЕВЬЮ (5+ уровень, но нет победы)
  if (accessLevel === 'preview') {
    return (
      <div className="castle-screen">
        <div className="castle-screen__header">
          <button className="back-btn" onClick={handleBack}>← Назад</button>
          <h1>🏰 ЗАМОК (тизер)</h1>
        </div>
        
        <div className="vladimir-message">
          <div className="vladimir-avatar">🎩</div>
          <p dangerouslySetInnerHTML={{ __html: vladimirPhrase }} />
        </div>
        
        <div className="castle-preview-card">
          <div className="castle-art">
            <span className="castle-emoji">🏰</span>
            <div className="castle-level">Уровень доступа: <strong>Тизер</strong></div>
          </div>
          <p className="preview-desc">
            «Вы видите лишь часть величия. Полная версия откроется после победы над Финальным Владыкой.»
          </p>
        </div>
        
        <div className="preview-actions">
          <button className="action-btn" onClick={() => navigate('/game/task/' + userId)}>
            ⚔️ Вернуться к задачам
          </button>
          <button className="action-btn action-btn--secondary" onClick={handleChatWithVladimir}>
            🍵 Поболтать с Владимиром
          </button>
        </div>
        
        <FloatingNav 
          userId={userId}
          showBack={true}
          showMenu={true}
          showSettings={false}
          onBack={handleBack}
          theme="game"
        />
      </div>
    );
  }

  // 🔹 ПОЛНЫЙ ДОСТУП (победа над Владыкой)
  return (
    <div className="castle-screen">
      
      {/* 🔹 HEADER */}
      <div className="castle-screen__header">
        <button className="back-btn" onClick={handleBack}>← Назад</button>
        <h1>🏰 ЗАМОК ЧИСЛЯНДИИ</h1>
      </div>

      {/* 🔹 ВЛАДИМИР — СООБЩЕНИЕ */}
      <div className="vladimir-message">
        <div className="vladimir-avatar">🎩</div>
        <p dangerouslySetInnerHTML={{ __html: vladimirPhrase }} />
      </div>

      {/* 🔹 СТАТУС UPKEEP */}
      <div className={`upkeep-status ${castleInfo?.bonuses_active ? 'active' : 'inactive'}`}>
        <div className="upkeep-icon">{castleInfo?.bonuses_active ? '✅' : '❌'}</div>
        <div className="upkeep-info">
          <strong>Upkeep:</strong> {castleInfo?.bonuses_active 
            ? `Оплачен на ${castleInfo.days_remaining} дн.` 
            : 'Не оплачен'}
          {castleInfo?.bonuses_active && (
            <span className="bonus-badge">🎁 {castleInfo.total_bonus_display}</span>
          )}
        </div>
      </div>

      {/* 🔹 БАЛАНС */}
      <div className="balance-card">
        <span>💰 На руках:</span>
        <strong>{playerStats?.score_balance?.toLocaleString() || 0} 🪙</strong>
      </div>

      {/* 🔹 ОПЛАТА UPKEEP */}
      <div className="upkeep-section">
        <h3>⚙️ Оплатить содержание</h3>
        <p className="upkeep-desc">
          Цена: <strong>{(upkeepDays * 100).toLocaleString()} 🪙</strong> за {upkeepDays} день(ей)
        </p>
        
        <div className="days-selector">
          {[1, 7, 30].map(days => (
            <button
              key={days}
              className={`days-btn ${upkeepDays === days ? 'active' : ''}`}
              onClick={() => setUpkeepDays(days)}
              disabled={processing}
            >
              {days} д.
            </button>
          ))}
        </div>

        <button 
          className="pay-btn"
          onClick={handlePayUpkeep}
          disabled={processing || (playerStats?.score_balance || 0) < upkeepDays * 100}
        >
          {processing ? '⏳ Обработка...' : `💰 Оплатить ${(upkeepDays * 100).toLocaleString()} 🪙`}
        </button>
      </div>

      {/* 🔹 ДЕКОРАЦИИ */}
      <div className="decorations-section">
        <h3>🎨 Декорации</h3>
        <p className="section-desc">Нажми на декорацию для покупки или улучшения</p>
        
        <div className="decorations-grid">
          {CASTLE_DECORATIONS.map(dec => {
            const currentLevel = castleInfo?.decoration_upgrades?.[dec.id] || 0;
            const price = getDecorationPrice(dec, currentLevel);
            const bonus = getDecorationBonus(dec, currentLevel);
            const canAfford = (playerStats?.score_balance || 0) >= price;
            
            return (
              <button
                key={dec.id}
                className={`decoration-card ${selectedDecoration?.id === dec.id ? 'selected' : ''} ${currentLevel === 0 ? 'locked' : ''}`}
                onClick={() => setSelectedDecoration(selectedDecoration?.id === dec.id ? null : dec)}
                disabled={processing}
              >
                <span className="dec-emoji">{dec.emoji}</span>
                <span className="dec-name">{dec.name}</span>
                
                {currentLevel > 0 ? (
                  <>
                    <span className="dec-level">Ур. {currentLevel}</span>
                    <span className="dec-bonus">+{Math.round(bonus * 100)}%</span>
                  </>
                ) : (
                  <span className="dec-price">{price.toLocaleString()} 🪙</span>
                )}
                
                {selectedDecoration?.id === dec.id && (
                  <div className="dec-actions">
                    <button
                      className={`buy-btn ${canAfford ? '' : 'disabled'}`}
                      onClick={(e) => { e.stopPropagation(); handleBuyDecoration(dec); }}
                      disabled={!canAfford || processing}
                    >
                      {currentLevel === 0 ? '🛒 Купить' : '⬆️ Улучшить'}
                    </button>
                    <button 
                      className="cancel-btn"
                      onClick={(e) => { e.stopPropagation(); setSelectedDecoration(null); }}
                    >
                      ✕
                    </button>
                  </div>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* 🔹 ДОПОЛНИТЕЛЬНЫЕ ДЕЙСТВИЯ */}
      <div className="extra-actions">
        <button className="action-btn action-btn--secondary" onClick={handleChatWithVladimir}>
          🍵 Поболтать с Владимиром
        </button>
        <button className="action-btn action-btn--secondary" onClick={handleSecretRoom}>
          🗝️ Тайная Комната
        </button>
      </div>

      {/* 🔹 СООБЩЕНИЯ */}
      {message && (
        <div className={`message message--${message.type}`} dangerouslySetInnerHTML={{ __html: message.text }} />
      )}

      {/* 🔹 FLOATING NAV */}
      <FloatingNav 
        userId={userId}
        showBack={true}
        showMenu={true}
        showSettings={false}
        onBack={handleBack}
        theme="game"
      />
      
    </div>
  );
}