import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FloatingNav } from '../components/FloatingNav';
import { CoinsLabel } from '../components/CoinIcon';
import { botApi } from '../adapters/botAdapter';
import './ProfileScreen.css';

const CHAOS_LABELS = {
  dormant: 'Спит',
  awakened: 'Пробуждён',
  unstable: 'Нестабилен',
  critical: 'Критический',
};

export function ProfileScreen({ userId = '331113480' }) {
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await botApi.getPlayerProfile(userId);
        if (data?.error) {
          setError(data.error);
        } else {
          setProfile(data);
        }
      } catch (err) {
        console.error('Profile load error:', err);
        setError('Не удалось загрузить профиль');
      } finally {
        setLoading(false);
      }
    };
    if (userId) load();
  }, [userId]);

  const handleBack = () => navigate(`/game/menu/${userId}`);

  if (loading) {
    return (
      <div className="profile-screen">
        <div className="profile-screen__loading">
          <div className="loading-spinner">👤</div>
          <p>Зал славы...</p>
        </div>
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="profile-screen">
        <div className="profile-screen__error">⚠️ {error || 'Профиль не найден'}</div>
        <button type="button" className="profile-screen__back" onClick={handleBack}>← В меню</button>
        <FloatingNav userId={userId} showBack onBack={handleBack} showMenu theme="game" />
      </div>
    );
  }

  const xpPercent = profile.xp_to_next
    ? Math.min(100, Math.round((profile.xp / profile.xp_to_next) * 100))
    : 0;

  return (
    <div className="profile-screen">
      <header className="profile-hero">
        <div className="profile-hero__avatar">🧙‍♀️</div>
        <div className="profile-hero__info">
          <h1 className="profile-hero__name">{profile.first_name}</h1>
          <p className="profile-hero__id">Игрок #{profile.user_id}</p>
          <p className="profile-hero__rank">
            👑 Ур. {profile.level} · {profile.rank_title}
          </p>
        </div>
      </header>

      <div className="profile-xp">
        <div className="profile-xp__labels">
          <span>Опыт</span>
          <span>{profile.xp} / {profile.xp_to_next} XP</span>
        </div>
        <div className="profile-xp__bar">
          <div className="profile-xp__fill" style={{ width: `${xpPercent}%` }} />
        </div>
      </div>

      <div className="profile-stats-grid">
        <div className="profile-stat-card profile-stat-card--gold">
          <span className="profile-stat-card__label">На руках</span>
          <CoinsLabel amount={profile.score_balance} />
        </div>
        <div className="profile-stat-card">
          <span className="profile-stat-card__label">Рейтинг</span>
          <strong>{profile.total_score?.toLocaleString('ru-RU')}</strong>
        </div>
        <div className="profile-stat-card">
          <span className="profile-stat-card__label">Задач решено</span>
          <strong>{profile.tasks_solved}</strong>
        </div>
        <div className="profile-stat-card">
          <span className="profile-stat-card__label">Точность</span>
          <strong>
            {profile.accuracy?.emoji} {profile.accuracy?.percent}%
          </strong>
          <small>{profile.accuracy?.label}</small>
        </div>
      </div>

      <section className="profile-section">
        <h2 className="profile-section__title">🗺️ Прогресс</h2>
        <div className="profile-progress-list">
          <div className="profile-progress-row">
            <span>Острова</span>
            <strong>{profile.islands_completed} / {profile.islands_total}</strong>
          </div>
          <div className="profile-progress-row">
            <span>Пост-гейм миры</span>
            <strong>{profile.postgame_worlds_completed} / {profile.postgame_worlds_total}</strong>
          </div>
          <div className="profile-progress-row">
            <span>Боссы побеждены</span>
            <strong>{profile.bosses_defeated_count}</strong>
          </div>
          <div className="profile-progress-row">
            <span>Замок открыт</span>
            <strong>{profile.completed_normal_game ? '✅ Да' : '🔒 Нет'}</strong>
          </div>
        </div>
      </section>

      {profile.defeated_bosses?.length > 0 && (
        <section className="profile-section">
          <h2 className="profile-section__title">⚔️ Побеждённые боссы</h2>
          <div className="profile-chips">
            {profile.defeated_bosses.map((id) => (
              <span key={id} className="profile-chip">{id.replace(/_/g, ' ')}</span>
            ))}
          </div>
        </section>
      )}

      <section className="profile-section">
        <h2 className="profile-section__title">🌀 Хаос</h2>
        <div className="profile-chaos">
          <span>Энергия: <strong>{profile.chaos_energy}</strong></span>
          <span>Разлом: <strong>{profile.rift_stage}</strong></span>
          <span>Артефакт: <strong>{CHAOS_LABELS[profile.artifact_chaos_state] || profile.artifact_chaos_state}</strong></span>
        </div>
      </section>

      <section className="profile-section">
        <h2 className="profile-section__title">🎒 Инвентарь</h2>
        {profile.inventory_count > 0 ? (
          <button type="button" className="profile-inventory-btn" onClick={() => navigate(`/game/inventory/${userId}`)}>
            Открыть инвентарь ({profile.inventory_count} предметов) →
          </button>
        ) : (
          <>
            <p className="profile-inventory-note profile-inventory-note--empty">
              Пусто — пора исследовать Числяндию!
            </p>
            <button type="button" className="profile-inventory-btn profile-inventory-btn--ghost" onClick={() => navigate(`/game/inventory/${userId}`)}>
              Открыть инвентарь →
            </button>
          </>
        )}
      </section>

      <button type="button" className="profile-screen__back" onClick={handleBack}>
        ← В меню
      </button>

      <FloatingNav userId={userId} showBack onBack={handleBack} showMenu theme="game" />
    </div>
  );
}
