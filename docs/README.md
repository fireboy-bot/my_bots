# 🎮 Числяндия — Образовательный бот для детей

> **Версия:** 4.7 (Full Restore + run_polling Fix) 🟢🟣✅  
> **Язык:** Python 3.14+  
> **Платформы:** Telegram, VK/MAX (через адаптеры)  
> **Цель:** Обучение математике через игровую механику для детей 6-12 лет

## 🚀 Быстрый старт

### Требования
- Python 3.14+
- SQLite (по умолчанию `data/progress.db`)
- Node.js 18+ (для фронтенда `frontend/`)

### Установка
```powershell
# 1. Клонировать репозиторий
git clone <repo_url>
cd chislyandia

# 2. Создать виртуальное окружение
python -m venv venv
venv\Scripts\activate

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Настроить окружение
cp .env.example .env
# Отредактировать .env: добавить BOT_TOKEN, ADMIN_IDS и т.д.

# 5. Запустить бота
python manyunya_bot.py

📦 chislyandia/
├── 📄 manyunya_bot.py    # Точка входа, инициализация, роутинг
├── 📄 config.py          # Конфигурация, валидация, пути
├── 📁 core/              # Ядро: game_engine, score_manager, avatar_cache
├── 📁 handlers/          # Обработчики команд и callback'ов
├── 📁 platforms/         # Адаптеры: TelegramAdapter, MaxAdapter
├── 📁 database/          # Работа с БД: schema, storage
├── 📁 data/              # JSON-контент: задачи, боссы, фразы
├── 📁 frontend/          # React-интерфейс (Vite)
├── 📁 web/               # Flask API для веб-версии
└── 📁 docs/              # Документация (этот раздел)
🔑 Ключевые фичи
Фича
Описание
🔄 Мульти-платформенность
Один код → Telegram + VK через адаптеры
🎨 Аватарки персонажей
Кэширование, фоновая загрузка
👑 Боссы и уровни
9 боссов, прогрессия сложности, психологические атаки
💰 Экономика
Банк, магазин, артефакты, алхимия
👨‍👩‍👧 Семейный режим
Отслеживание прогресса ребёнка (опционально)
🔐 Безопасность
Валидация конфига, .env, админ-команды
🛠 Админ-команды (только для ADMIN_IDS)
12345678
📚 Документация по модулям
ARCHITECTURE.md — Схема взаимодействия модулей
CORE_MODULES.md — Ядро: game_engine, score_manager
BOT_HANDLERS.md — Обработчики команд и UI
DATA_AND_FRONTEND.md — Контент и веб-интерфейс
⚠️ Важные предупреждения
Никогда не коммить .env — только .env.example с заглушками.
Бэкапы БД — файлы progress_backup_*.db игнорируются в .gitignore.
Токены — BOT_TOKEN, VK_TOKEN хранятся только в .env.
Админ-команды — доступны только по ADMIN_IDS, не включать в продакшене без необходимости.
🤝 Вклад в проект
Создай ветку: git checkout -b feature/your-feature
Вноси изменения, пиши тесты
Коммить с понятным сообщением: feat: add new boss ability
Пуш и пул-реквест
Документация актуальна для версии 4.7