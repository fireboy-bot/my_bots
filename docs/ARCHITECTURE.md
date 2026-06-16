┌─────────────────┐
│ manyunya_bot.py │ ← Точка входа
└────────┬────────┘
│
▼
┌─────────────────┐
│ Application │ ← python-telegram-bot
│ (post_init) │
└────────┬────────┘
│
┌────┴────┐
▼ ▼
┌────────┐ ┌────────┐
│Telegram│ │ Max/VK │ ← Адаптеры
│Adapter │ │Adapter │
└────┬───┘ └────┬───┘
│ │
▼ ▼
┌─────────────────┐
│ universal_callback │ ← Единый роутер
│ handle_message │
└────────┬────────┘
│
▼
┌─────────────────┐
│ ChislyandiaEngine │ ← Игровая логика
│ ScoreManager │ ← Прогресс, очки
│ Bank/Castle/Shop │ ← Экономические модули
└────────┬────────┘
│
▼
┌─────────────────┐
│ PlayerStorage │ ← SQLite/PostgreSQL
│ (database/) │
└────────┬────────┘
│
▼
┌─────────────────┐
│ JSON-контент │ ← data/tasks.json, bosses/, worlds/
└─────────────────┘


## 🧩 Ключевые модули

### `manyunya_bot.py` — Точка входа
| Компонент | Назначение |
|-----------|------------|
| `post_init()` | Асинхронная инициализация: адаптеры, кэш аватарок, ScoreManager, Engine |
| `main()` | Настройка Application, регистрация хендлеров, запуск polling |
| `graceful_shutdown_*` | Корректное завершение: закрытие адаптеров, БД |
| `global_error_handler` | Логирование ошибок, уведомление админов |

**Порядок регистрации хендлеров (критично!):**
1. Навигация (`get_navigation_handlers()`) — первым, чтобы перехватывать `/back`, `/menu`
2. Специфичные модули (банк, замок, магазин, артефакты)
3. Админ-команды (только в dev-режиме)
4. Босс-команды (dev-режим)
5. Общие: `MessageHandler` + `CallbackQueryHandler` — последними

### `config.py` — Конфигурация
| Переменная | Описание | Пример |
|------------|----------|--------|
| `BOT_TOKEN` | Токен Telegram-бота | `123456:AAH...` |
| `APP_ENV` | Режим: `development` / `production` | `production` |
| `ADMIN_IDS` | Список ID администраторов | `[123456789, 987654321]` |
| `BACKUP_KEEP_COUNT` | Сколько бэкапов хранить | `14` |
| `SPAM_*` | Настройки анти-спама | `0.45`, `3.0`, `4.0` |

**Валидация:** `validate_config()` вызывается при импорте, выбрасывает `ValueError` при ошибках.

## 🔄 Адаптеры (платформы)

platforms/
├── base_adapter.py # Абстрактный базовый класс
├── telegram_adapter.py # Реализация для python-telegram-bot
└── max_adapter.py # Реализация для VK/MAX API


**Принцип работы:**
- Все адаптеры наследуют общий интерфейс
- Бот сохраняет список `bot_data['adapters']`
- `universal_callback_handler` определяет платформу по `update` и делегирует

## 🎮 Игровое ядро (`core/`)

| Модуль | Ответственность |
|--------|----------------|
| `game_engine.py` | Основной цикл: генерация задач, проверка ответов, прогресс уровня |
| `score_manager.py` | Подсчёт очков, множители, бонусы, статистика |
| `castle_engine.py` | Логика замка как хаба, разблокировка контента |
| `bank_manager.py` | Экономика: баланс, транзакции, цены |
| `artifact_manager.py` | Артефакты: эффекты, активация, инвентарь |
| `difficulty_manager.py` | Адаптивная сложность задач |
| `avatar_cache.py` | Кэширование изображений персонажей |
| `vladimir_persona.py` | Личность и диалоги персонажа-помощника |

## 🗄 Данные (`data/`)

data/
├── progress.db # SQLite: пользователи, прогресс, инвентарь
├── tasks.json # Банк математических задач
├── shards.json # Осколки знаний (коллекционные предметы)
├── phrases.json # Фразы персонажей, подсказки
├── bosses/ # Конфиги боссов: здоровье, способности, фазы
└── worlds/ # Уровни-миры: сложность, темы, награды

**Схема БД (упрощённо):**
```sql
users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    current_level TEXT,
    balance INTEGER,
    artifacts JSON,
    progress JSON,
    created_at TIMESTAMP
)

🌐 Веб-интерфейс (frontend/ + web/)
Frontend: React + Vite, адаптивный дизайн
Backend: Flask API (web/api_server.py)
Связь: Бот ↔ Flask ↔ React через REST/JSON
Основные экраны:
MenuScreen — главное меню
TaskScreen — решение задач
CastleScreen — хаб-локация
BankScreen / ShopScreen — экономика
ArtifactsScreen — коллекция артефактов
🔐 Безопасность и деплой
Секреты: Только через .env, никогда в коде
Бэкапы: Автоматическая ротация (BACKUP_KEEP_COUNT)
Логи: logs/app.log, уровень LOG_LEVEL
Деплой:
Dev: локально через python manyunya_bot.py
Prod: systemd-сервис или Docker, polling-режим
Схема актуальна для версии 4.7