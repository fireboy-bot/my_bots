import { useState, useEffect, useRef, useCallback } from 'react';
import { CharacterCard } from './CharacterCard';

export function TaskArea({ 
  task, 
  transferTask, 
  feedback, 
  processing, 
  chaosState,
  onAnswerSubmit,
  onInputChange,
  answerInput,
  onBack
}) {
  const inputRef = useRef(null);
  const cardRef = useRef(null);
  const [isFocused, setIsFocused] = useState(false);
  const [flashState, setFlashState] = useState(null); // 'correct' | 'error' | null

  const activeTask = transferTask || task;
  
  // 🔹 Автофокус при смене задачи
  useEffect(() => {
    if (activeTask && inputRef.current && !processing && !feedback) {
      inputRef.current.focus();
    }
  }, [activeTask, processing, feedback]);

  // 🔹 Запуск анимации вспышки при получении фидбека
  useEffect(() => {
    if (feedback?.type === 'success') {
      setFlashState('correct');
    } else if (feedback?.type === 'error') {
      setFlashState('error');
    }
    // Сброс после завершения анимации (400ms)
    if (feedback) {
      const timer = setTimeout(() => setFlashState(null), 450);
      return () => clearTimeout(timer);
    }
  }, [feedback]);
  
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !processing && !feedback) {
      onAnswerSubmit();
    }
  };
  
  const flashClass = flashState ? `flash-${flashState}` : '';
  const focusedClass = isFocused ? 'focused' : '';

  return (
    <main className="game-center">
      <CharacterCard 
        character={getCharacterForChaos(chaosState)}
        mood={getMoodForChaos(chaosState, feedback)}
        message={feedback?.text}
      />
      
      <div 
        ref={cardRef}
        className={`task-card ${focusedClass} ${flashClass}`} 
        data-task-id={task?.id || 'unknown'}
      >
        <p className="task-question">{activeTask?.question}</p>
        
        <input
          ref={inputRef}
          type="tel"
          inputMode="numeric"
          pattern="[0-9]*"
          className="answer-input"
          value={answerInput}
          onChange={onInputChange}
          onKeyDown={handleKeyDown}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder="Введи ответ..."
          disabled={processing || !!feedback}
        />
        
        <button 
          className="btn-submit" 
          onClick={onAnswerSubmit}
          disabled={!answerInput.trim() || processing || !!feedback}
        >
          {processing ? '⏳ Проверка...' : '✅ Ответить'}
        </button>
        
        {feedback && feedback.type !== 'transfer' && (
          <div className={`feedback feedback--${feedback.type}`}>
            {feedback.text}
            {feedback.reward !== undefined && feedback.reward !== 0 && (
              <span> {feedback.reward > 0 ? `+${feedback.reward}` : feedback.reward} 🪙</span>
            )}
          </div>
        )}
      </div>
    </main>
  );
}

function getCharacterForChaos(s) { 
  return s.rift_stage >= 3 ? 'alchemist' : s.consecutive_errors >= 2 ? 'vladimir' : 'manunya'; 
}

function getMoodForChaos(s, f) {
  if (!f) return 'idle';
  if (f.type === 'success') return 'happy';
  if (f.type === 'error') return s.rift_stage >= 3 ? 'overwhelmed' : 'concerned';
  if (f.type === 'transfer') return 'thinking';
  return 'idle';
}