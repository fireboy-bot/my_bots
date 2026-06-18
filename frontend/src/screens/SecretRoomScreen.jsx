import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { FloatingNav } from '../components/FloatingNav';
import { botApi } from '../adapters/botAdapter';
import './SecretRoomScreen.css';

export function SecretRoomScreen({ userId = '331113480' }) {
  const navigate = useNavigate();
  const [state, setState] = useState(null);
  const [event, setEvent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [message, setMessage] = useState(null);

  const loadState = useCallback(async () => {
    setLoading(true);
    try {
      const data = await botApi.getSecretRoom(userId);
      if (data?.error) {
        setMessage({ type: 'error', text: data.error });
      } else {
        setState(data);
      }
    } catch (err) {
      console.error('Secret room load error:', err);
      setMessage({ type: 'error', text: 'Не удалось загрузить комнату' });
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    if (userId) loadState();
  }, [userId, loadState]);

  const handleBack = () => navigate(`/game/castle/${userId}`);

  const handleExplore = async () => {
    if (processing || !state?.available) return;
    setProcessing(true);
    setMessage(null);
    setEvent(null);
    try {
      const result = await botApi.exploreSecretRoom(userId);
      if (result.state) setState(result.state);
      if (!result.success && result.message) {
        setMessage({ type: 'error', text: result.message });
        return;
      }
      setEvent(result);
      if (result.message && result.event_type !== 'puzzle') {
        setMessage({ type: 'success', text: result.message });
      }
    } catch (err) {
      setMessage({ type: 'error', text: '⚠️ Ошибка исследования' });
    } finally {
      setProcessing(false);
    }
  };

  const handlePuzzleAnswer = async (puzzleId, optionIndex) => {
    if (processing) return;
    setProcessing(true);
    try {
      const result = await botApi.answerSecretPuzzle(userId, puzzleId, optionIndex);
      if (result.state) setState(result.state);
      setEvent(null);
      setMessage({
        type: result.correct ? 'success' : 'error',
        text: result.message || (result.correct ? '✅ Верно!' : '❌ Неверно'),
      });
    } catch (err) {
      setMessage({ type: 'error', text: '⚠️ Ошибка ответа' });
    } finally {
      setProcessing(false);
    }
  };

  if (loading) {
    return (
      <div className="secret-room">
        <div className="secret-room__loading">
          <div className="loading-spinner">🗝️</div>
          <p>Тайная комната...</p>
        </div>
      </div>
    );
  }

  if (!state?.unlocked) {
    return (
      <div className="secret-room">
        <header className="secret-room__header">
          <h1>🗝️ Тайная комната</h1>
        </header>
        <div className="secret-room__locked">
          <span className="secret-room__locked-icon">🔒</span>
          <p>Комната откроется после победы над <strong>Финальным Владыкой</strong> (не Истинным — он ещё дальше).</p>
          <button type="button" className="secret-room__btn" onClick={handleBack}>← В замок</button>
        </div>
        <FloatingNav userId={userId} showBack onBack={handleBack} showMenu theme="game" />
      </div>
    );
  }

  return (
    <div className="secret-room">
      <header className="secret-room__header">
        <h1>🗝️ Тайная комната</h1>
        <p className="secret-room__subtitle">Загадки, лор и редкие находки</p>
      </header>

      <div className="secret-room__stats">
        <div><span>Уровень</span><strong>{state.level}</strong></div>
        <div><span>Опыт</span><strong>{state.exp}/{state.exp_needed}</strong></div>
        <div><span>Попытки</span><strong>{state.attempts_left}/{state.attempts_max}</strong></div>
        <div><span>Серия</span><strong>🔥 {state.streak} дн.</strong></div>
      </div>

      {!state.available && (
        <div className="secret-room__notice">
          🔒 Попытки на сегодня закончились. Откроется через: <strong>{state.resets_at}</strong>
        </div>
      )}

      {state.lore_completion && (
        <div className="secret-room__lore-bar">
          <span>📜 Коллекция лора</span>
          <strong>{state.lore_completion.seen}/{state.lore_completion.total} ({state.lore_completion.percent}%)</strong>
        </div>
      )}

      <button
        type="button"
        className="secret-room__explore-btn"
        onClick={handleExplore}
        disabled={processing || !state.available}
      >
        {processing ? '⏳ ...' : '🔍 Исследовать'}
      </button>

      {event?.event_type === 'puzzle' && event.puzzle && (
        <div className="secret-room__event secret-room__event--puzzle">
          <h3>{event.title}</h3>
          <p>{event.puzzle.question}</p>
          <div className="secret-room__options">
            {event.puzzle.options.map((option, idx) => (
              <button
                key={idx}
                type="button"
                className="secret-room__option-btn"
                onClick={() => handlePuzzleAnswer(event.puzzle.id, idx)}
                disabled={processing}
              >
                {option}
              </button>
            ))}
          </div>
        </div>
      )}

      {event && event.event_type !== 'puzzle' && event.title && (
        <div className={`secret-room__event secret-room__event--${event.event_type}`}>
          <h3>{event.title}</h3>
          {event.message && <p className="secret-room__event-text">{event.message}</p>}
        </div>
      )}

      {state.items?.length > 0 && (
        <section className="secret-room__section">
          <h3>💎 Коллекция ({state.items.length})</h3>
          <ul className="secret-room__items">
            {state.items.map((item) => (
              <li key={item.id}>{item.name}</li>
            ))}
          </ul>
        </section>
      )}

      {state.logs_preview?.length > 0 && (
        <section className="secret-room__section">
          <h3>📜 Дневник</h3>
          {state.logs_preview.map((entry, idx) => (
            <p key={idx} className="secret-room__log-entry">{entry}</p>
          ))}
        </section>
      )}

      {message && (
        <div className={`secret-room__message secret-room__message--${message.type}`}>
          {message.text}
        </div>
      )}

      <button type="button" className="secret-room__back" onClick={handleBack}>← В замок</button>
      <FloatingNav userId={userId} showBack onBack={handleBack} showMenu theme="game" />
    </div>
  );
}
