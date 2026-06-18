import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { FloatingNav } from '../components/FloatingNav';
import { GameEventOverlay } from '../components/GameEventOverlay';
import { botApi } from '../adapters/botAdapter';
import './TrueLordScreen.css';

const SPEAKER_LABELS = {
  true_lord: '👑 Истинный Владыка',
  manunya: '💛 Манюня',
  georgy: '🐌 Георгий',
};

function PhaseBadge({ phase, phaseName }) {
  return (
    <span className={`true-lord-phase true-lord-phase--${phase}`}>
      {phaseName || phase}
    </span>
  );
}

function HpBar({ current, max }) {
  const pct = max > 0 ? Math.round((current / max) * 100) : 0;
  return (
    <div className="true-lord-hp">
      <div className="true-lord-hp__label">
        <span>❤️ {current} / {max}</span>
      </div>
      <div className="true-lord-hp__track">
        <div className="true-lord-hp__fill" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function DialogueFeed({ messages }) {
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (!messages.length) return null;

  return (
    <div className="true-lord-dialogues">
      {messages.map((msg, i) => (
        <div
          key={`${msg.speaker}-${i}`}
          className={`true-lord-dialogue true-lord-dialogue--${msg.speaker}${msg.style === 'title' ? ' true-lord-dialogue--title' : ''}`}
        >
          <span className="true-lord-dialogue__speaker">
            {SPEAKER_LABELS[msg.speaker] || msg.speaker}
          </span>
          <p>{msg.text}</p>
        </div>
      ))}
      <div ref={endRef} />
    </div>
  );
}

export function TrueLordScreen({ userId = '331113480' }) {
  const navigate = useNavigate();
  const [boss, setBoss] = useState(null);
  const [task, setTask] = useState(null);
  const [answerInput, setAnswerInput] = useState('');
  const [feedback, setFeedback] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [dialogues, setDialogues] = useState([]);
  const [hintText, setHintText] = useState(null);
  const [gameEvent, setGameEvent] = useState(null);
  const inputRef = useRef(null);

  const appendDialogues = useCallback((newOnes) => {
    if (!newOnes?.length) return;
    setDialogues((prev) => [...prev, ...newOnes]);
  }, []);

  useEffect(() => {
    if (task && inputRef.current && !processing) {
      inputRef.current.focus();
    }
  }, [task, processing]);

  const loadBattle = useCallback(async () => {
    setLoading(true);
    setFeedback(null);
    setHintText(null);
    try {
      const data = await botApi.startBoss(userId, 'true_lord');
      if (data?.error) {
        setFeedback({ type: 'error', text: data.error });
        return;
      }
      setBoss(data);
      setTask(data.task);
      setDialogues(data.dialogues || []);
    } catch (error) {
      console.error('True Lord load error:', error);
      setFeedback({ type: 'error', text: '⚠️ Не удалось начать битву' });
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    if (userId) loadBattle();
  }, [userId, loadBattle]);

  const handleSubmit = async () => {
    const raw = answerInput.trim().replace(',', '.');
    if (!raw || processing || !task?.id) return;

    setProcessing(true);
    setFeedback(null);
    setHintText(null);

    try {
      const result = await botApi.checkAnswer({
        user_id: userId,
        answer: raw,
        task_id: task.id,
        expected_answer: task.correct_answer,
        island_id: 'true_lord',
        operation_type: 'boss',
      });

      appendDialogues(result.dialogues);

      if (result.boss_defeated && result.absolute_victory) {
        setBoss((prev) => ({ ...prev, boss_health: 0 }));
        setGameEvent({
          type: 'absolute_victory',
          message: result.message,
          rewardItem: result.reward_item,
          finaleText: result.finale_text,
          secretText: result.secret_text,
        });
        return;
      }

      if (result.level_up) {
        appendDialogues([{ speaker: 'manunya', text: `🎉 Новый уровень! Ты стала сильнее!` }]);
      }

      setFeedback({
        type: result.correct ? 'success' : 'error',
        text: result.message,
      });

      if (result.boss_health !== undefined) {
        setBoss((prev) => ({
          ...prev,
          boss_health: result.boss_health,
          phase: result.phase || prev?.phase,
          phase_name: result.phase_name || prev?.phase_name,
          avatar_url: result.avatar_url || prev?.avatar_url,
        }));
      }

      if (result.next_task) {
        setTimeout(() => {
          setTask(result.next_task);
          setAnswerInput('');
          if (!result.correct) {
            setFeedback(null);
          }
        }, result.correct ? 1400 : 2200);
      }
    } catch (error) {
      console.error('True Lord answer error:', error);
      setFeedback({ type: 'error', text: '⚠️ Ошибка отправки' });
    } finally {
      setProcessing(false);
    }
  };

  const handleHint = async () => {
    if (processing) return;
    setProcessing(true);
    try {
      const result = await botApi.trueLordHint(userId);
      if (result.error) {
        setFeedback({ type: 'error', text: result.error });
        return;
      }
      setHintText(result.hint);
      setFeedback({ type: 'hint', text: result.message });
    } catch (error) {
      setFeedback({ type: 'error', text: '⚠️ Не удалось получить подсказку' });
    } finally {
      setProcessing(false);
    }
  };

  const handleExit = async () => {
    try {
      await botApi.exitBoss(userId);
    } catch (_) {
      /* ignore */
    }
    navigate(`/game/worlds/${userId}`);
  };

  if (loading) {
    return (
      <div className="true-lord-screen true-lord-screen--loading">
        <div className="loading-spinner">👁️</div>
        <p>Истинный Владыка пробуждается...</p>
      </div>
    );
  }

  if (feedback?.type === 'error' && !boss?.task) {
    return (
      <div className="true-lord-screen true-lord-screen--loading">
        <p className="true-lord-error">{feedback.text}</p>
        <button type="button" className="true-lord-btn true-lord-btn--ghost" onClick={handleExit}>
          ← На карту
        </button>
      </div>
    );
  }

  return (
    <div className="true-lord-screen">
      <header className="true-lord-header">
        {boss?.avatar_url && (
          <img
            src={boss.avatar_url}
            alt="Истинный Владыка"
            className="true-lord-avatar"
          />
        )}
        <h1>{boss?.boss_name || 'Истинный Владыка'}</h1>
        <PhaseBadge phase={boss?.phase || 'calm'} phaseName={boss?.phase_name} />
      </header>

      <HpBar current={boss?.boss_health ?? 0} max={boss?.boss_max_health ?? 20} />

      <DialogueFeed messages={dialogues} />

      <div className="true-lord-card">
        <p className="true-lord-question">{task?.question}</p>
        {hintText && (
          <p className="true-lord-hint">💡 {hintText}</p>
        )}
        <input
          ref={inputRef}
          className="true-lord-input"
          type="text"
          autoFocus
          inputMode="numeric"
          value={answerInput}
          onChange={(e) => setAnswerInput(e.target.value.replace(/[^0-9.,-]/g, ''))}
          onKeyDown={(e) => e.key === 'Enter' && !processing && handleSubmit()}
          disabled={processing}
          placeholder="Твой ответ..."
        />
        <div className="true-lord-actions">
          <button
            type="button"
            className="true-lord-btn true-lord-btn--hint"
            onClick={handleHint}
            disabled={processing}
          >
            💡 Подсказка
          </button>
          <button
            type="button"
            className="true-lord-btn true-lord-btn--attack"
            onClick={handleSubmit}
            disabled={processing || !answerInput.trim()}
          >
            ⚔️ Атаковать
          </button>
        </div>
      </div>

      {feedback && feedback.type !== 'error' && (
        <div className={`true-lord-feedback true-lord-feedback--${feedback.type}`}>
          {feedback.text}
        </div>
      )}

      <button type="button" className="true-lord-exit" onClick={handleExit}>
        ← Отступить
      </button>

      <FloatingNav userId={userId} showBack onBack={handleExit} showMenu theme="game" />

      <GameEventOverlay
        event={gameEvent}
        onContinue={() => {
          setGameEvent(null);
          navigate(`/game/worlds/${userId}`);
        }}
      />
    </div>
  );
}
