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

  const islandWorlds = worlds.filter((w) => w.tier === 'island');
  const postGameWorlds = worlds.filter((w) => w.tier === 'world');
  const islandBosses = bosses.filter((b) => b.tier === 'island');
  const finalBoss = bosses.find((b) => b.tier === 'final');
  const keeperBosses = bosses.filter((b) => b.tier === 'keeper');
  const endgameBoss = bosses.find((b) => b.tier === 'endgame');
  const postGameUnlocked = postGameWorlds.some((w) => w.unlocked);

  const renderWorldCard = (world) => (
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
        {world.unlocked ? (world.tier === 'world' ? '▶ 20 задач' : '▶ Играть') : '🔒 Закрыто'}
      </span>
    </button>
  );

  const renderBossCard = (boss, options = {}) => (
    <button
      key={boss.id}
      type="button"
      className={`boss-card ${options.final ? 'boss-card--final' : ''} ${options.endgame ? 'boss-card--endgame' : ''} ${boss.defeated ? 'boss-card--defeated' : ''} ${boss.unlocked ? '' : 'boss-card--locked'}`}
      onClick={() => handleSelectBoss(boss)}
      disabled={!boss.unlocked || boss.defeated}
      title={boss.lock_reason || boss.description}
    >
      <span className="boss-card__emoji">{boss.emoji}</span>
      <span className="boss-card__name">{boss.name}</span>
      {options.desc && (
        <p className="boss-card__desc">{options.desc}</p>
      )}
      <span className="boss-card__status">
        {boss.defeated ? '✅ Побеждён' : boss.unlocked ? '⚔️ Бой' : '🔒 Закрыт'}
      </span>
    </button>
  );

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
        <h1 className="worlds-screen__title">🗺️ Карта приключений</h1>
        <p className="worlds-screen__subtitle">Острова, миры и боссы</p>
      </header>

      {error && (
        <div className="worlds-screen__error">⚠️ {error}</div>
      )}

      <section className="worlds-section">
        <h2 className="worlds-section__title">🏝️ Острова</h2>
        <div className="worlds-grid">
          {islandWorlds.map(renderWorldCard)}
        </div>
      </section>

      {postGameWorlds.length > 0 && (
        <section className={`worlds-section worlds-section--postgame ${postGameUnlocked ? '' : 'worlds-section--locked-hint'}`}>
          <h2 className="worlds-section__title">🌌 Пост-гейм</h2>
          {!postGameUnlocked && (
            <p className="worlds-section__hint">Откроется после победы над Финальным Владыкой</p>
          )}
          <div className="worlds-grid">
            {postGameWorlds.map(renderWorldCard)}
          </div>
        </section>
      )}

      {bosses.length > 0 && (
        <section className="worlds-bosses">
          <h2 className="worlds-bosses__title">⚔️ Боссы островов</h2>
          <div className="worlds-bosses__grid">
            {islandBosses.map((boss) => renderBossCard(boss))}
          </div>

          {finalBoss && renderBossCard(finalBoss, {
            final: true,
            desc: finalBoss.defeated
              ? 'Замок и артефакты открыты!'
              : finalBoss.unlocked
                ? 'Финальный бой — откроет пост-гейм миры'
                : finalBoss.lock_reason || 'Победи боссов трёх островов',
          })}

          {keeperBosses.length > 0 && (
            <>
              <h3 className="worlds-bosses__subtitle">🛡️ Хранители миров</h3>
              <div className="worlds-bosses__grid">
                {keeperBosses.map((boss) => renderBossCard(boss))}
              </div>
            </>
          )}

          {endgameBoss && renderBossCard(endgameBoss, {
            endgame: true,
            desc: endgameBoss.defeated
              ? 'Абсолютная победа!'
              : endgameBoss.unlocked
                ? 'Финал всей Числяндии'
                : endgameBoss.lock_reason || 'Победи всех Хранителей',
          })}
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
