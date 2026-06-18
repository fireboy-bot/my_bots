# WORK COMPASS — Web V2

Проект: `C:\Users\Fireboy\Dev\Projects\Chislyandia`  
Staging: [http://147.45.225.173](http://147.45.225.173)  
Демо-пользователь: `331113480`

## Текущий статус

### Уже готово

- Web MVP (меню, задачи, экономика, деплой).
- Карта миров (`WorldsScreen`) и забеги по островам.
- Боссы web:
  - обычные боссы в `BossScreen`
  - отдельный эпический `TrueLordScreen`
- Профиль игрока (`/game/profile/:userId`)
- Инвентарь (`/game/inventory/:userId`)
- Тайная комната (`/game/secret-room/:userId`)
- Overlay событий (включая абсолютную победу)

### Критические API, которые должны жить

- `/api/health`
- `/api/game/worlds/<user_id>`
- `/api/game/bosses/<user_id>`
- `/api/game/boss/start`
- `/api/game/check_answer`
- `/api/inventory/<user_id>`
- `/api/secret_room/<user_id>`

## Последние крупные изменения

### 2026-06-17 / 2026-06-18

- Исправлен инвентарь на staging (убрана web-зависимость от `telegram` в inventory view).
- Добавлен эпический web-режим Истинного Владыки:
  - `core/true_lord_run.py`
  - `TrueLordScreen`
  - endpoint подсказки `/api/game/true-lord/hint`
  - абсолютная победа в `GameEventOverlay`
- Nginx настроен отдавать аватары Истинного Владыки (`/images/true_lord_*.jpg`).
- Smoke тесты API: `30 passed`.
- Скрипты стабильности:
  - `scripts/configure-demo-user.py` — пост-гейм профиль для staging
  - `scripts/sync_user_db.py` + `scripts/sync-db.ps1` — синхронизация user/db bot ↔ VPS

## Ручной чеклист staging

- [x] `GET /api/health`
- [x] Главные роуты фронта открываются
- [x] Инвентарь грузится
- [x] Тайная комната открывается по условиям
- [x] Бандл обновляется после деплоя
- [ ] Полный ручной прогон эпик-боя Истинного Владыки на боевом профиле (демо настроен: `.\scripts\sync-db.ps1 configure-demo`)
- [x] Инструменты синхронизации БД bot ↔ VPS (`sync-db.ps1`, `sync_user_db.py`)

## Документация

- Активный набор: `docs/INDEX.md` (10 файлов).
- Legacy перенесён в `docs/archive/legacy-2026-06/`.
- Добавлены: `ARCHITECTURE.md` (V2), `DEVELOPMENT.md`.

## Следующие шаги (рефакторинг-ready)

1. Держать в актуале `INDEX`, `WEB_API_SERVER`, `FRONTEND`, `GAMEPLAY_SYSTEMS`.
2. Подготовить план рефакторинга:
   - унификация API-ответов (`success/error` contract),
   - унификация игровых событий (обычные боссы vs true lord),
   - изоляция UI-логики от сетевых вызовов.
3. Ручной прогон True Lord на staging после `configure-demo`.

## Рабочие команды

```powershell
cd C:\Users\Fireboy\Dev\Projects\Chislyandia
.\scripts\run-tests.ps1
.\scripts\deploy-staging.ps1
.\scripts\sync-db.ps1 configure-demo
.\scripts\sync-db.ps1 pull-user
```
