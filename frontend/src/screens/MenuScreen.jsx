import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FloatingNav } from '../components/FloatingNav';
import { CoinsLabel } from '../components/CoinIcon';
import { botApi } from '../adapters/botAdapter';
import './MenuScreen.css';

export function MenuScreen({ userId = "331113480" }) {
  const navigate = useNavigate();
  const [playerStats, setPlayerStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadProfile = async () => {
      try {
        const profile = await botApi.getPlayerProfile(userId);
        setPlayerStats(profile);
      } catch (error) {
        console.error('❌ Error loading profile:', error);
      } finally {
        setLoading(false);
      }
    };

    if (userId) {
      loadProfile();
    }
  }, [userId]);

  const handleStartGame = () => navigate(`/game/worlds/${userId}`);
  const handleCastle = () => navigate(`/game/castle/${userId}`);
  const handleBank = () => navigate(`/game/bank/${userId}`);
  const handleShop = () => navigate(`/game/shop/${userId}`);
  const handleProfile = () => navigate(`/game/profile/${userId}`);

  if (loading) {
    return (
      <div className="menu-screen">
        <div className="menu-screen__loading">
          <div className="loading-spinner">✨</div>
          <p>Загрузка мира...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="menu-screen">
      <div className="menu-screen__header">
        <h1 className="menu-screen__title">🎮 ЧИСЛЯНДИЯ</h1>
        <p className="menu-screen__subtitle">Приключение начинается здесь!</p>
      </div>

      {playerStats && (
        <button type="button" className="menu-profile-teaser" onClick={handleProfile}>
          <div className="menu-profile-teaser__avatar">🧙‍♀️</div>
          <div className="menu-profile-teaser__body">
            <div className="menu-profile-teaser__name">{playerStats.first_name || 'Игрок'}</div>
            <div className="menu-profile-teaser__meta">
              👑 Ур. {playerStats.level} · {playerStats.rank_title}
            </div>
            <div className="menu-profile-teaser__stats">
              <CoinsLabel amount={playerStats.score_balance || 0} />
              <span>⭐ {playerStats.total_score?.toLocaleString('ru-RU') || 0}</span>
            </div>
          </div>
          <span className="menu-profile-teaser__cta">Профиль →</span>
        </button>
      )}

      <div className="menu-screen__actions">
        <button
          className="action-btn action-btn--primary"
          onClick={handleStartGame}
        >
          <span className="action-btn__icon">⚔️</span>
          <span className="action-btn__text">
            <strong>В БОЙ!</strong>
            <small>Карта миров</small>
          </span>
        </button>

        <div className="action-grid">
          <button
            className="action-card action-card--castle"
            onClick={handleCastle}
          >
            <span className="action-card__icon">🏰</span>
            <span className="action-card__title">Замок</span>
            <span className="action-card__desc">Улучшения</span>
          </button>

          <button
            className="action-card action-card--bank"
            onClick={handleBank}
          >
            <span className="action-card__icon">🏦</span>
            <span className="action-card__title">Банк</span>
            <span className="action-card__desc">Вклад</span>
          </button>

          <button
            className="action-card action-card--shop"
            onClick={handleShop}
          >
            <span className="action-card__icon">🛒</span>
            <span className="action-card__title">Магазин</span>
            <span className="action-card__desc">Артефакты</span>
          </button>
        </div>
      </div>

      <FloatingNav
        userId={userId}
        showBack={false}
        showMenu={false}
        showSettings={true}
        onSettings={handleProfile}
        theme="game"
      />
    </div>
  );
}
