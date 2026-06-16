import { useState } from 'react';
import './AnswerInput.css';

export function AnswerInput({ onSubmit, disabled = false }) {
  const [answer, setAnswer] = useState('');

  const handleSubmit = () => {
    if (answer.trim() && !disabled) {
      onSubmit(answer);
      setAnswer('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSubmit();
    }
  };

  return (
    <div className="answer-input-container fade-in">
      <input
        type="number"
        className="answer-input"
        value={answer}
        onChange={(e) => setAnswer(e.target.value)}
        onKeyPress={handleKeyPress}
        placeholder="Твой ответ..."
        disabled={disabled}
        autoFocus
      />
      <button 
        className="submit-btn" 
        onClick={handleSubmit}
        disabled={disabled || !answer.trim()}
      >
        ✨ АКТИВИРОВАТЬ ✨
      </button>
    </div>
  );
}