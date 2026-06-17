import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FloatingNav } from '../components/FloatingNav';
import { botApi } from '../adapters/botAdapter';
import './WorldsScreen.css';

export function WorldsScreen({ userId = '331113480' }) {
  const navigate = useNavigate();
  const [worlds, setWorlds] = useState([]);
  const [bosses, setBosses] = useState([]);
  const [castleUnlocked, setCastleUnlocked] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError(null);
      try {
        const [worldsData, bossesData] = await Promise.all([
          botApi.getWorlds(userId),
          botApi.getBosses(userId),
        ]);
        if (worldsData?.error) {
          setError(worldsData.error);
          setWorlds([]);
        } else {
          setWorlds(worldsData.worlds || []);
        }
        if (!bossesData?.error) {
          setBosses(bossesData.bosses || []);
          setCastleUnlocked(!!bossesData.castle_unlocked);
        }
      } catch (err) {
        console.error('❌ Error loading worlds:', err);
        setError('Не удалось загрузить карту');
      } finally {
        setLoading(false);
      }
    };

    if (userId) {
      loadData();
    }
  }, [userId]);

  const handleSelectWorld = (world) => {
    if (!world.unlocked) return;
    navigate(`/game/task/${userId}/${world.id}`);
  };

  const handleSelectBoss = (boss) => {
    if (!boss.unlocked || boss.defeated) return;
    navigate(`/game/boss/${userId}/${boss.id}`);
  };

  const handleBack = () => navigate(`/game/menu/${userId}`);

  const islandBosses = bosses.filter((b) => b.tier !== 'final');
  const finalBoss = bosses.find((b) => b.tier === 'final');

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

      {bosses.length > 0 && (
        <section className="worlds-bosses">
          <h2 className="worlds-bosses__title">⚔️ Боссы</h2>
          <div className="worlds-bosses__grid">
            {islandBosses.map((boss) => (
              <button
                key={boss.id}
                type="button"
                className={`boss-card ${boss.defeated ? 'boss-card--defeated' : ''} ${boss.unlocked ? '' : 'boss-card--locked'}`}
                onClick={() => handleSelectBoss(boss)}
                disabled={!boss.unlocked || boss.defeated}
                title={boss.lock_reason || boss.description}
              >
                <span className="boss-card__emoji">{boss.emoji}</span>
                <span className="boss-card__name">{boss.name}</span>
                <span className="boss-card__status">
                  {boss.defeated ? '✅ Побеждён' : boss.unlocked ? '⚔️ Бой' : '🔒 Закрыт'}
                </span>
              </button>
            ))}
          </div>

          {finalBoss && (
            <button
              type="button"
              className={`boss-card boss-card--final ${finalBoss.defeated ? 'boss-card--defeated' : ''} ${finalBoss.unlocked ? '' : 'boss-card--locked'}`}
              onClick={() => handleSelectBoss(finalBoss)}
              disabled={!finalBoss.unlocked || finalBoss.defeated}
            >
              <span className="boss-card__emoji">{finalBoss.emoji}</span>
              <span className="boss-card__name">{finalBoss.name}</span>
              <p className="boss-card__desc">
                {finalBoss.defeated
                  ? 'Замок и артефакты открыты!'
                  : finalBoss.unlocked
                    ? 'Финальный бой — откроет замок и артефакты'
                    : finalBoss.lock_reason || 'Победи боссов трёх островов'}
              </p>
              <span className="boss-card__status">
                {finalBoss.defeated ? '👑 Побеждён' : finalBoss.unlocked ? '👑 В БОЙ!' : '🔒 Закрыт'}
              </span>
            </button>
          )}
        </section>
      )}

      {castleUnlocked && (
        <div className="worlds-castle-cta">
          <button type="button" className="worlds-castle-cta__btn" onClick={() => navigate(`/game/castle/${userId}`)}>
            🏰 Замок и артефакты
          </button>
        </div>
      )}

      <button type="button" className="worlds-screen__back" onClick={handleBack}>
        ← В меню
      </button>

      <FloatingNav userId={userId} showBack onBack={handleBack} showMenu theme="game" />
    </div>
  );
}
