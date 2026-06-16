import './TaskCard.css';

export function TaskCard({ question, taskType = 'addition' }) {
  return (
    <div className="task-card fade-in">
      <div className="task-icon">
        {taskType === 'addition' ? '➕' : 
         taskType === 'subtraction' ? '➖' : 
         taskType === 'multiplication' ? '✖️' : '➗'}
      </div>
      <div className="task-question">{question}</div>
      <div className="task-glow"></div>
    </div>
  );
}