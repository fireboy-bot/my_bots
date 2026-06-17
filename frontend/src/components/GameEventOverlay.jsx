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
  if (!event) return null;

  if (event.type === 'level_up') {
    return (
      <div className="game-event-overlay" role="dialog" aria-live="polite">
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
      <div className="game-event-overlay" role="dialog" aria-live="polite">
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
      <div className="game-event-overlay" role="dialog" aria-live="polite">
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

  return null;
}
