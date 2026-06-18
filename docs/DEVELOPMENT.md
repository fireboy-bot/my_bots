# Разработка — быстрый старт

Проект: `C:\Users\Fireboy\Dev\Projects\Chislyandia`

## Окружение

- Python 3.14+ (venv в `venv/`)
- Node.js 18+ (для `frontend/`)
- SQLite: `data/progress.db`

## Локальный запуск

### API (web-ядро)

```powershell
cd C:\Users\Fireboy\Dev\Projects\Chislyandia
.\venv\Scripts\activate
python web\api_server.py
```

API: http://127.0.0.1:5000/api/health

### Frontend

```powershell
cd C:\Users\Fireboy\Dev\Projects\Chislyandia\frontend
npm install
npm run dev
```

В `.env` / `.env.local`: `VITE_API_URL=http://127.0.0.1:5000`

### Telegram-бот

```powershell
cd C:\Users\Fireboy\Dev\Projects\Chislyandia
.\venv\Scripts\activate
# .env с BOT_TOKEN
python manyunya_bot.py
```

## Тесты

```powershell
.\scripts\run-tests.ps1
```

Сейчас: smoke на Flask API (`tests/test_api_smoke.py`).

## Деплой staging

```powershell
.\scripts\deploy-staging.ps1
```

См. `docs/STAGING.md`.

## Демо-пользователь

- Web staging: `331113480`
- URL: http://147.45.225.173/game/menu/331113480

Профиль для теста Истинного Владыки (3 хранителя побеждены, `true_lord` открыт):

```powershell
python scripts/configure-demo-user.py
```

На VPS после деплоя:

```powershell
.\scripts\sync-db.ps1 configure-demo
```

## Синхронизация БД (local ↔ staging VPS)

```powershell
.\scripts\sync-db.ps1 pull-user    # VPS -> local data\progress.db
.\scripts\sync-db.ps1 push-user    # local -> VPS
.\scripts\sync-db.ps1 pull-db      # скачать всю БД в data\progress.from-vps.db
.\scripts\sync-db.ps1 push-db      # заменить БД на VPS (с бэкапом на сервере)
```

Один пользователь через JSON:

```powershell
python scripts/sync_user_db.py export 331113480 -o data/sync/user.json
python scripts/sync_user_db.py import 331113480 -i data/sync/user.json
```

## Чеклист перед коммитом фичи

1. Код в `core/`, не в `api_server.py` (если это логика).
2. Метод в `botAdapter.js`, если нужен новый запрос с фронта.
3. `.\scripts\run-tests.ps1` — зелёный.
4. Обновить `docs/WORK_COMPASS.md` + профильный doc (API / Frontend / Gameplay).

## Полезные ссылки внутри docs

| Вопрос | Файл |
|--------|------|
| Все эндпоинты | `WEB_API_SERVER.md` |
| Роуты и экраны | `FRONTEND.md` |
| Миры, боссы, V2 | `GAMEPLAY_SYSTEMS.md` |
| Слои и модули | `ARCHITECTURE.md` |
| Что готово / план | `WORK_COMPASS.md` |
