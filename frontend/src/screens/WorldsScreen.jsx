import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FloatingNav } from '../components/FloatingNav';
import { botApi } from '../adapters/botAdapter';
import './WorldsScreen.css';

export function WorldsScreen({ userId = '331113480' }) {
  const navigate = useNavigate();
  const [worlds, setWorlds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadWorlds = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await botApi.getWorlds(userId);
        if (data?.error) {
          setError(data.error);
          setWorlds([]);
          return;
        }
        setWorlds(data.worlds || []);
      } catch (err) {
        console.error('❌ Error loading worlds:', err);
        setError('Не удалось загрузить острова');
      } finally {
        setLoading(false);
      }
    };

    if (userId) {
      loadWorlds();
    }
  }, [userId]);

  const handleSelectWorld = (world) => {
    if (!world.unlocked) return;
    navigate(`/game/task/${userId}/${world.id}`);
  };

  const handleBack = () => navigate(`/game/menu/${userId}`);

  if (loading) {
    return (
      <div className="worlds-screen">
        <div className="worlds-screen__loading">
          <div className="loading-spinner">🗺️</div>
          <p>Карта миров...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="worlds-screen">
      <header className="worlds-screen__header">
        <h1 className="worlds-screen__title">🏝️ Острова</h1>
        <p className="worlds-screen__subtitle">Выбери приключение</p>
      </header>

      {error && (
        <div className="worlds-screen__error">⚠️ {error}</div>
      )}

      <div className="worlds-grid">
        {worlds.map((world) => (
          <button
            key={world.id}
            type="button"
            className={`world-card world-card--${world.tier} ${world.unlocked ? '' : 'world-card--locked'}`}
            onClick={() => handleSelectWorld(world)}
            disabled={!world.unlocked}
          >
            <span className="world-card__emoji">{world.emoji}</span>
            <span className="world-card__name">{world.name}</span>
            <span className="world-card__status">
              {world.unlocked ? '▶ Играть' : '🔒 Закрыто'}
            </span>
          </button>
        ))}
      </div>

      <button type="button" className="worlds-screen__back" onClick={handleBack}>
        ← В меню
      </button>

      <FloatingNav userId={userId} showBack onBack={handleBack} showMenu theme="game" />
    </div>
  );
}
