import './CharacterCard.css';

export function CharacterCard({ character = 'manyaunya', alt = 'Манюня' }) {
  return (
    <div className="character-card fade-in">
      <div className="character-image-wrapper">
        <img 
          src="/images/characters/manyaunya.jpg"  // ← .jpg вместо .png!
          alt={alt}
          className="character-image"
          onError={(e) => {
            // Если картинка не загрузилась — показываем эмодзи-заглушку
            e.target.style.display = 'none';
            e.target.parentElement.innerHTML = `
              <div style="
                width: 100%;
                aspect-ratio: 1/1;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 64px;
                background: linear-gradient(135deg, #7C3AED, #22D3EE);
                border-radius: 24px;
              ">🧙</div>
            `;
          }}
        />
      </div>
    </div>
  );
}