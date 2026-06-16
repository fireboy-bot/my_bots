import './StoryCard.css';

export function StoryCard({ text, character = 'manyaunya' }) {
  return (
    <div className="story-card fade-in">
      <div className="story-bubble">
        <div className="story-text">{text}</div>
        <div className="story-arrow"></div>
      </div>
      <div className="story-character-name">
        {character === 'manyaunya' ? '🧙 Манюня' : '🥕 Морковка'}
      </div>
    </div>
  );
}