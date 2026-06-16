import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FloatingNav } from '../components/FloatingNav';
import { botApi } from '../adapters/botAdapter';
import './ShopScreen.css';

export function ShopScreen({ userId = "331113480", onBack }) {
  const navigate = useNavigate();
  const [balance, setBalance] = useState(0);
  const [upkeepActive, setUpkeepActive] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [profile, castle] = await Promise.all([
          botApi.getPlayerProfile(userId),
          botApi.getCastleInfo(userId)
        ]);
        setBalance(profile?.score_balance || 0);
        setUpkeepActive(castle?.bonuses_active || false);
      } catch (error) {
        console.error('❌ Error loading shop ', error);
      }
    };
    if (userId) loadData();
  }, [userId]);

  const handleBack = () => {
    if (onBack) onBack();
    else navigate('/game/menu/' + userId);
  };

  return (
    <div className="shop-screen">
      <div className="shop-screen__header">
        <button className="back-btn" onClick={handleBack}>← Назад</button>
        <h1>🛒 МАГАЗИН ЧИСЛЯНДИИ</h1>
      </div>

      <div className="balance-banner">
        <span>💰 Баланс:</span>
        <strong>{balance.toLocaleString('ru-RU')} 🪙</strong>
        {!upkeepActive && <span className="upkeep-warning">⚠️ Upkeep не оплачен!</span>}
      </div>

      <div className="shop-categories">
        <button className="category-card category-card--artifacts"
          onClick={() => navigate(`/game/shop/artifacts/${userId}`)}>
          <div className="category-icon">🔮</div>
          <div className="category-info">
            <h3>Артефакты</h3>
            <p>Долгосрочная прокачка: удача, сила, мудрость</p>
            <span className="category-hint">Требует оплаченный upkeep замка</span>
          </div>
          <div className="category-arrow">→</div>
        </button>

        <button className="category-card category-card--alchemy"
          onClick={() => navigate(`/game/shop/alchemy/${userId}`)}>
          <div className="category-icon">⚗️</div>
          <div className="category-info">
            <h3>Лавка Безумца</h3>
            <p>Рисковые зелья и хаотичные артефакты</p>
            <span className="category-hint">Разблокируется по прогрессу</span>
          </div>
          <div className="category-arrow">→</div>
        </button>
      </div>

      <div className="shop-tip">
        💡 <i>Выбери раздел: Артефакты для стабильного прогресса или Алхимия для риска и веселья!</i>
      </div>

      <FloatingNav userId={userId} showBack={true} showMenu={true} showSettings={false} onBack={handleBack} theme="game" />
    </div>
  );
}