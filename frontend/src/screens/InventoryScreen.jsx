import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FloatingNav } from '../components/FloatingNav';
import { botApi } from '../adapters/botAdapter';
import './InventoryScreen.css';

function ItemList({ title, items, emptyText }) {
  if (!items?.length) {
    return (
      <section className="inv-section">
        <h2 className="inv-section__title">{title}</h2>
        <p className="inv-section__empty">{emptyText}</p>
      </section>
    );
  }

  return (
    <section className="inv-section">
      <h2 className="inv-section__title">{title}</h2>
      <ul className="inv-list">
        {items.map((item) => (
          <li key={`${item.category}-${item.id}`} className="inv-list__item">
            <span className="inv-list__label">{item.label}</span>
            {item.count > 1 && <span className="inv-list__count">×{item.count}</span>}
            {item.level > 0 && <span className="inv-list__level">ур. {item.level}</span>}
          </li>
        ))}
      </ul>
    </section>
  );
}

export function InventoryScreen({ userId = '331113480' }) {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const result = await botApi.getInventory(userId);
        if (result?.error) setError(result.error);
        else setData(result);
      } catch (err) {
        setError('Не удалось загрузить инвентарь');
      } finally {
        setLoading(false);
      }
    };
    if (userId) load();
  }, [userId]);

  const handleBack = () => navigate(`/game/profile/${userId}`);

  if (loading) {
    return (
      <div className="inventory-screen">
        <div className="inventory-screen__loading">🎒 Загрузка...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="inventory-screen">
        <p className="inventory-screen__error">⚠️ {error}</p>
        <button type="button" onClick={handleBack}>← Назад</button>
        <FloatingNav userId={userId} showBack onBack={handleBack} showMenu theme="game" />
      </div>
    );
  }

  return (
    <div className="inventory-screen">
      <header className="inventory-screen__header">
        <h1>🎒 Инвентарь</h1>
        <p>{data.total_count} предмет(ов)</p>
      </header>

      {data.is_empty ? (
        <div className="inventory-screen__empty">
          <span>📭</span>
          <p>Пока пусто — решай задачи, побеждай боссов и создавай зелья в алхимии!</p>
        </div>
      ) : (
        <>
          <ItemList title="🧪 Расходники" items={data.consumables} emptyText="Нет расходников" />
          <ItemList title="🏆 Трофеи и награды" items={data.trophies} emptyText="Пока нет трофеев" />
          <ItemList title="🔮 Артефакты" items={data.artifacts} emptyText="Артефакты покупаются в замке" />
          {data.secret_items?.length > 0 && (
            <ItemList title="🗝️ Из тайной комнаты" items={data.secret_items} emptyText="" />
          )}
        </>
      )}

      <button type="button" className="inventory-screen__back" onClick={handleBack}>← В профиль</button>
      <FloatingNav userId={userId} showBack onBack={handleBack} showMenu theme="game" />
    </div>
  );
}
