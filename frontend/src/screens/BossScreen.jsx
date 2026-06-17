import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { FloatingNav } from '../components/FloatingNav';
import { GameEventOverlay } from '../components/GameEventOverlay';
import { botApi } from '../adapters/botAdapter';
import './BossScreen.css';

function BossHealthBar({ current, max }) {
  const hearts = [];
  for (let i = 0; i < max; i += 1) {
    hearts.push(
      <span key={i} className="boss-hp__heart">
        {i < current ? '❤️' : '💔'}
      </span>
    );
  }
  return <div className="boss-hp">{hearts}</div>;
}

export function BossScreen({ userId = '331113480', bossId }) {
  const navigate = useNavigate();
  const [boss, setBoss] = useState(null);
  const [task, setTask] = useState(null);
  const [answerInput, setAnswerInput] = useState('');
  const [feedback, setFeedback] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [taskProgress, setTaskProgress] = useState(null);
  const [gameEvent, setGameEvent] = useState(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (task && inputRef.current && !processing && feedback?.type !== 'success') {
      inputRef.current.focus();
    }
  }, [task, processing, feedback]);

  const loadBoss = useCallback(async () => {
    setLoading(true);
    setFeedback(null);
    try {
      const data = await botApi.startBoss(userId, bossId);
      if (data?.error) {
        setFeedback({ type: 'error', text: data.error });
        return;
      }
      setBoss(data);
      setTask(data.task);
      setTaskProgress({ current: data.task_index || 1, total: data.total_tasks || 0 });
    } catch (error) {
      console.error('Boss load error:', error);
      setFeedback({ type: 'error', text: '⚠️ Не удалось начать бой' });
    } finally {
      setLoading(false);
    }
  }, [userId, bossId]);

  useEffect(() => {
    if (userId && bossId) {
      loadBoss();
    }
  }, [userId, bossId, loadBoss]);

  const handleSubmit = async () => {
    const raw = answerInput.trim().replace(',', '.');
    if (!raw || processing || !task?.id) return;

    setProcessing(true);
    setFeedback(null);

    try {
      const result = await botApi.checkAnswer({
        user_id: userId,
        answer: raw,
        task_id: task.id,
        expected_answer: task.correct_answer,
        island_id: bossId,
        operation_type: 'boss',
      });

      if (result.boss_defeated) {
        setFeedback({ type: 'success', text: result.message });
        setBoss((prev) => ({ ...prev, boss_health: 0 }));
        setGameEvent({
          type: 'boss_victory',
          message: result.message,
          rewardItem: result.reward_item,
        });
        return;
      }

      if (result.boss_failed) {
        setFeedback({ type: 'error', text: result.message });
        setTimeout(() => navigate(`/game/worlds/${userId}`), 2500);
        return;
      }

      setFeedback({
        type: result.correct ? 'success' : 'error',
        text: result.ability_triggered
          ? `${result.message} (${result.ability_triggered.name})`
          : result.message,
      });

      if (result.boss_health !== undefined) {
        setBoss((prev) => ({ ...prev, boss_health: result.boss_health }));
      }

      if (result.next_task) {
        setTimeout(() => {
          setTask(result.next_task);
          setTaskProgress({
            current: result.task_index || 1,
            total: result.total_tasks || taskProgress?.total,
          });
          setAnswerInput('');
          setFeedback(null);
        }, 1200);
      } else {
        setTimeout(() => {
          setAnswerInput('');
          setFeedback(null);
        }, 1200);
      }
    } catch (error) {
      console.error('Boss answer error:', error);
      setFeedback({ type: 'error', text: '⚠️ Ошибка отправки' });
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
      <div className="boss-screen boss-screen--loading">
        <div className="loading-spinner">⚔️</div>
        <p>Босс появляется...</p>
      </div>
    );
  }

  return (
    <div className="boss-screen">
      <header className="boss-screen__header">
        <span className="boss-screen__emoji">{boss?.boss_emoji || '👹'}</span>
        <h1>{boss?.boss_name || 'Босс'}</h1>
        <p>{boss?.intro || boss?.boss_description}</p>
      </header>

      <BossHealthBar
        current={boss?.boss_health ?? 0}
        max={boss?.boss_max_health ?? 5}
      />

      {taskProgress && (
        <div className="boss-screen__progress">
          Задача {taskProgress.current} из {taskProgress.total}
        </div>
      )}

      <div className="boss-screen__card">
        <p className="boss-screen__question">{task?.question}</p>
        <input
          ref={inputRef}
          className="boss-screen__input"
          type="text"
          autoFocus
          inputMode="numeric"
          value={answerInput}
          onChange={(e) => setAnswerInput(e.target.value.replace(/[^0-9.,-]/g, ''))}
          onKeyDown={(e) => e.key === 'Enter' && !processing && handleSubmit()}
          disabled={processing || feedback?.type === 'success'}
          placeholder="Твой ответ..."
        />
        <button
          type="button"
          className="boss-screen__submit"
          onClick={handleSubmit}
          disabled={processing || !answerInput.trim()}
        >
          ⚔️ Атаковать
        </button>
      </div>

      {feedback && (
        <div className={`boss-screen__feedback boss-screen__feedback--${feedback.type}`}>
          {feedback.text}
        </div>
      )}

      <button type="button" className="boss-screen__exit" onClick={handleExit}>
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
