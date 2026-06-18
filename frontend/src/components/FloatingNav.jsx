import { useNavigate, useLocation } from 'react-router-dom';
import './FloatingNav.css';

/**
 * 🔹 Плавающая навигация — правый нижний угол
 */
export function FloatingNav({
  userId,
  showBack = true,
  showMenu = true,
  showSettings = true,
  onBack,
  onMenu,
  onSettings,
  theme = 'default'
}) {
  const navigate = useNavigate();
  const location = useLocation();

  // 🔹 Авто-определение: скрывать меню если мы уже в меню
  const isMenuScreen = location.pathname.includes('/menu');
  const shouldShowMenu = showMenu && !isMenuScreen;

  // 🔹 Дефолтные обработчики
  const handleBack = () => {
    if (onBack) {
      onBack();
    } else {
      navigate(-1);
    }
  };

  const handleMenu = () => {
    if (onMenu) {
      onMenu();
    } else if (userId) {
      navigate(`/game/menu/${userId}`);
    }
  };

  const handleSettings = () => {
    if (onSettings) {
      onSettings();
    } else if (userId) {
      navigate(`/game/profile/${userId}`);
    }
  };

  return (
    <div className={`floating-nav floating-nav--${theme}`} aria-label="Навигация">
      {showBack && (
        <button 
          className="nav-btn nav-btn--back" 
          onClick={handleBack}
          title="Назад"
          aria-label="Назад"
        >
          ⬅️
        </button>
      )}
      
      {shouldShowMenu && (
        <button 
          className="nav-btn nav-btn--menu" 
          onClick={handleMenu}
          title="Меню"
          aria-label="Меню"
        >
          📋
        </button>
      )}
      
      {showSettings && (
        <button 
          className="nav-btn nav-btn--settings" 
          onClick={handleSettings}
          title="Профиль"
          aria-label="Профиль"
        >
          👤
        </button>
      )}
    </div>
  );
}