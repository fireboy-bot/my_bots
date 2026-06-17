import { useEffect } from 'react';
import { createPortal } from 'react-dom';
import './GameEventOverlay.css';

const ZONE_NAMES = {
  addition: 'Сложение',
  subtraction: 'Вычитание',
  multiplication: 'Умножение',
  division: 'Деление',
  time_world: 'Время',
  measure_world: 'Меры',
  logic_world: 'Логика',
};

function zoneLabel(id) {
  return ZONE_NAMES[id] || id;
}

export function GameEventOverlay({ event, onContinue }) {
  useEffect(() => {
    if (!event) return undefined;
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = prev;
    };
  }, [event]);

  if (!event) return null;

  const overlay = (() => {
  if (event.type === 'level_up') {
    return (
      <div className="game-event-overlay" role="dialog" aria-modal="true" aria-live="polite">
        <div className="game-event-card game-event-card--level">
          <div className="game-event-card__icon">⭐</div>
          <h2>Новый уровень!</h2>
          <p className="game-event-card__highlight">Уровень {event.level}</p>
          <p className="game-event-card__sub">Так держать, герой!</p>
          <button type="button" className="game-event-card__btn" onClick={onContinue}>
            Продолжить
          </button>
        </div>
      </div>
    );
  }

  if (event.type === 'island_complete') {
    return (
      <div className="game-event-overlay" role="dialog" aria-modal="true" aria-live="polite">
        <div className="game-event-card game-event-card--victory">
          <div className="game-event-card__icon">🏆</div>
          <h2>Остров пройден!</h2>
          <p>{event.message}</p>
          {event.completionBonus > 0 && (
            <p className="game-event-card__reward">+{event.completionBonus} монет</p>
          )}
          {event.unlockedZone && (
            <p className="game-event-card__unlock">
              🔓 Открыт: {zoneLabel(event.unlockedZone)}
            </p>
          )}
          {event.bossPending && (
            <p className="game-event-card__boss">
              ⚔️ Босс ждёт: {event.bossPending.name}
            </p>
          )}
          {event.levelUp && (
            <p className="game-event-card__level">⭐ Уровень {event.levelUp}</p>
          )}
          <button type="button" className="game-event-card__btn" onClick={onContinue}>
            {event.bossPending ? 'К боссу!' : 'На карту'}
          </button>
        </div>
      </div>
    );
  }

  if (event.type === 'boss_victory') {
    return (
      <div className="game-event-overlay" role="dialog" aria-modal="true" aria-live="polite">
        <div className="game-event-card game-event-card--boss">
          <div className="game-event-card__icon">🎉</div>
          <h2>Победа!</h2>
          <p>{event.message}</p>
          {event.rewardItem && (
            <p className="game-event-card__reward">Награда: {event.rewardItem.replace(/_/g, ' ')}</p>
          )}
          <button type="button" className="game-event-card__btn" onClick={onContinue}>
            На карту миров
          </button>
        </div>
      </div>
    );
  }

  if (event.type === 'final_boss_victory') {
    return (
      <div className="game-event-overlay" role="dialog" aria-modal="true" aria-live="polite">
        <div className="game-event-card game-event-card--final">
          <div className="game-event-card__icon">👑</div>
          <h2>Владыка повержен!</h2>
          <p>{event.message}</p>
          <p className="game-event-card__unlock">🏰 Замок открыт · 🔮 Артефакты доступны</p>
          {event.rewardItem && (
            <p className="game-event-card__reward">Награда: {event.rewardItem.replace(/_/g, ' ')}</p>
          )}
          <div className="game-event-card__actions">
            <button type="button" className="game-event-card__btn" onClick={event.onCastle}>
              В замок
            </button>
            <button type="button" className="game-event-card__btn game-event-card__btn--ghost" onClick={onContinue}>
              На карту
            </button>
          </div>
        </div>
      </div>
    );
  }

  return null;
  })();

  return createPortal(overlay, document.body);
}
