import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FloatingNav } from '../components/FloatingNav';
import { botApi } from '../adapters/botAdapter';
import './MenuScreen.css';

export function MenuScreen({ userId = "331113480" }) {
  const navigate = useNavigate();
  const [playerStats, setPlayerStats] = useState(null);
  const [loading, setLoading] = useState(true);

  // 🔹 Загрузка профиля игрока
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

  // 🔹 Переходы
  const handleStartGame = () => navigate(`/game/task/${userId}`);
  const handleCastle = () => navigate(`/game/castle/${userId}`);
  const handleBank = () => navigate(`/game/bank/${userId}`);
  const handleShop = () => navigate(`/game/shop/${userId}`);

  // 🔹 Скелетон загрузки
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
      
      {/* 🔹 HEADER */}
      <div className="menu-screen__header">
        <h1 className="menu-screen__title">🎮 ЧИСЛЯНДИЯ</h1>
        <p className="menu-screen__subtitle">Приключение начинается здесь!</p>
      </div>

      {/* 🔹 ПРОФИЛЬ ИГРОКА — ОБНОВЛЁННЫЙ */}
      {playerStats && (
        <div className="menu-screen__profile">
          <div className="profile-card">
            <div className="profile-avatar">🧙‍♀️</div>
            <div className="profile-info">
              <div className="profile-name">Игрок #{playerStats.user_id}</div>
              <div className="profile-stats">
                <span className="stat">🏆 Ур: {playerStats.level || 1}</span>
                <span className="stat stat--score">⭐ {playerStats.total_score?.toLocaleString('ru-RU') || 0}</span>
                <span className="stat stat--gold">💰 {playerStats.score_balance?.toLocaleString('ru-RU') || 0}</span>
                <span className="stat">✅ {playerStats.tasks_solved || 0}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 🔹 ГЛАВНЫЕ КНОПКИ */}
      <div className="menu-screen__actions">
        <button 
          className="action-btn action-btn--primary"
          onClick={handleStartGame}
        >
          <span className="action-btn__icon">⚔️</span>
          <span className="action-btn__text">
            <strong>В БОЙ!</strong>
            <small>Решать задачи</small>
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

      {/* 🔹 FLOATING NAV */}
      <FloatingNav 
        userId={userId}
        showBack={false}
        showMenu={false}
        showSettings={true}
        theme="game"
      />
      
    </div>
  );
}