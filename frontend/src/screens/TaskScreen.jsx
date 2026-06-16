import { useState, useEffect, useRef, useCallback, memo } from 'react';
import { useNavigate } from 'react-router-dom';
import { FloatingNav } from '../components/FloatingNav';
import { ChaosArtifact } from '../components/ChaosArtifact';
import { ChaosCoreOverlay } from '../components/ChaosCoreOverlay';
import { ChaosParticles } from '../components/ChaosParticles';
import { TaskArea } from '../components/TaskArea';
import { botApi } from '../adapters/Adapter';
import './TaskScreen.css';

// 🔹 Боковые панели — обернуты в memo, не перерисовываются без смены пропсов
const StatsPanel = memo(function StatsPanel({ playerStats }) {
  return (
    <aside className="game-panel game-stats">
      <div className="stat-item">
        <span className="stat-icon" data-type="level">⭐</span>
        <div>
          <div className="stat-value">{playerStats.level}</div>
          <div className="stat-label">Уровень</div>
        </div>
      </div>
      <div className="stat-item">
        <span className="stat-icon" data-type="coins">🪙</span>
        <div>
          <div className="stat-value">{playerStats.coins}</div>
          <div className="stat-label">Монеты</div>
        </div>
      </div>
      <div className="stat-item">
        <span className="stat-icon" data-type="hearts">❤️</span>
        <div>
          <div className="stat-value">{playerStats.hearts}</div>
          <div className="stat-label">Жизни</div>
        </div>
      </div>
      <div className="stat-item">
        <span className="stat-icon" data-type="xp">📈</span>
        <div>
          <div className="stat-value">{playerStats.xp} XP</div>
          <div className="stat-label">Опыт</div>
        </div>
      </div>
    </aside>
  );
});

const SettingsPanel = memo(function SettingsPanel() {
  return (
    <aside className="game-panel game-settings">
      <button className="game-button">⚙️ Настройки</button>
      <button className="game-button">🔇 Звук: Вкл</button>
      <button className="game-button">🎵 Музыка: Вкл</button>
    </aside>
  );
});

const ChaosPanel = memo(function ChaosPanel({ chaosState }) {
  return (
    <aside className="game-panel game-chaos">
      <ChaosArtifact state={chaosState.artifact_state} energy={chaosState.chaos_energy} />
    </aside>
  );
});

const NavPanel = memo(function NavPanel({ onBack, userId, navigate }) {
  return (
    <footer className="game-panel game-nav">
      <button className="game-button" onClick={onBack}>← Назад</button>
      <button className="game-button">💡 Подсказка</button>
      <button className="game-button" onClick={() => navigate('/game/menu/' + userId)}>🏠 Меню</button>
    </footer>
  );
});

// 🔹 ОСНОВНОЙ КОМПОНЕНТ
export function TaskScreen({ userId = "331113480", onBack }) {
  const navigate = useNavigate();
  
  // 🔹 Состояния ТОЛЬКО для центральной зоны
  const [task, setTask] = useState(null);
  const [answerInput, setAnswerInput] = useState('');
  const [feedback, setFeedback] = useState(null);
  const [transferTask, setTransferTask] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [loading, setLoading] = useState(true);
  
  // 🔹 Состояния для боковых панелей
  const [chaosState, setChaosState] = useState({
    rift_stage: 0, chaos_energy: 0, artifact_state: 'dormant', consecutive_errors: 0
  });
  const [playerStats, setPlayerStats] = useState({
    level: 5, coins: 1250, hearts: 3, xp: 2450
  });
  
  const autoNextTimerRef = useRef(null);
  
  useEffect(() => {
    return () => {
      if (autoNextTimerRef.current) clearTimeout(autoNextTimerRef.current);
    };
  }, []);

  // 🔹 Загрузка задачи
  const loadTask = useCallback(async () => {
    if (autoNextTimerRef.current) clearTimeout(autoNextTimerRef.current);
    setAnswerInput('');
    setFeedback(null);
    setTransferTask(null);
    setProcessing(false);
    setLoading(true);

    try {
      const taskData = await botApi.getTask(userId, 'addition');
      setTask(taskData);
      if (taskData.chaos_state) {
        setChaosState(prev => ({ ...prev, ...taskData.chaos_state }));
      }
    } catch (error) {
      console.error('❌ Error loading task:', error);
      setFeedback({ type: 'error', text: '⚠️ Ошибка загрузки задачи' });
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => { loadTask(); }, [loadTask]);

  // 🔹 Обработка ввода
  const handleInputChange = (e) => {
    setAnswerInput(e.target.value.replace(/[^0-9.,]/g, ''));
  };

  // 🔹 Отправка ответа
  const handleSubmit = async () => {
    const raw = answerInput.trim().replace(',', '.');
    if (!raw || processing || !task) return;
    
    setProcessing(true);
    setFeedback(null);
    if (autoNextTimerRef.current) clearTimeout(autoNextTimerRef.current);
    
    try {
      const result = await botApi.checkAnswer({
        user_id: userId,
        answer: raw,
        task_id: task?.id || null,
        expected_answer: task?.correct_answer ?? task?.answer,
        island_id: task?.island || 'addition',
        operation_type: task?.operation_type || 'addition',
        is_transfer: !!transferTask,
        currentBalance: playerStats.coins
      });
      
      if (result.chaos_state) {
        setChaosState(result.chaos_state);
      }
      
      if (result.new_balance !== undefined) {
        setPlayerStats(prev => ({ ...prev, coins: result.new_balance }));
      }
      if (result.new_total_score !== undefined) {
        setPlayerStats(prev => ({ ...prev, xp: result.new_total_score }));
      }
      
      if (result.transfer_task && !transferTask) {
        setTransferTask(result.transfer_task);
        setFeedback({ type: 'transfer', text: result.message, hint: result.transfer_task.hint });
      } else {
        setFeedback({
          type: result.correct ? 'success' : 'error',
          text: result.message,
          reward: result.reward
        });
        
        if (result.correct) {
          autoNextTimerRef.current = setTimeout(() => {
            loadTask();
          }, 1500);
        } else {
          setTimeout(() => {
            setFeedback(null);
            setAnswerInput('');
          }, 1500);
        }
      }
      
      if (transferTask && result.correct) {
        setTimeout(() => {
          setTransferTask(null);
          loadTask();
        }, 1500);
      }
      
    } catch (error) {
      console.error('❌ Error submitting answer:', error);
      setFeedback({ type: 'error', text: '⚠️ Ошибка отправки ответа' });
    } finally {
      setProcessing(false);
    }
  };

  const handleBack = () => {
    if (onBack) onBack();
    else navigate('/game/menu/' + userId);
  };

  // 🔹 Скелетон загрузки
  if (loading && !task) {
    return (
      <div className="task-screen loading">
        <div className="loading-spinner">✨</div>
      </div>
    );
  }

  const isChaosActive = chaosState.rift_stage >= 2;

  return (
    <div className={`task-screen ${isChaosActive ? 'chaos-active' : ''}`}>
      {/* 🔹 СЛОЙ ЭФФЕКТОВ */}
      <ChaosParticles chaosEnergy={chaosState.chaos_energy} riftStage={chaosState.rift_stage} enabled={!loading} />
      <ChaosCoreOverlay chaosEnergy={chaosState.chaos_energy} riftStage={chaosState.rift_stage} />

      {/* 🔹 ПАНЕЛИ */}
      <StatsPanel playerStats={playerStats} />
      <TaskArea
        task={task}
        transferTask={transferTask}
        feedback={feedback}
        processing={processing}
        chaosState={chaosState}
        answerInput={answerInput}
        onAnswerSubmit={handleSubmit}
        onInputChange={handleInputChange}
        onBack={handleBack}
      />
      <SettingsPanel />
      <ChaosPanel chaosState={chaosState} />
      <NavPanel onBack={handleBack} userId={userId} navigate={navigate} />
      
      {/* 🔹 FLOATING NAV (поверх всего) */}
      <FloatingNav 
        userId={userId}
        showBack={true}
        showMenu={true}
        showSettings={false}
        onBack={handleBack}
        theme="game"
      />
    </div>
  );
}