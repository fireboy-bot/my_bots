import './MessageBubble.css';

export function MessageBubble({ text, type = 'player' }) {
  return (
    <div className={`message-bubble ${type} fade-in`}>
      <div className="bubble-content">{text}</div>
    </div>
  );
}