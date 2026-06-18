# Документация Chislyandia

Единая точка входа. **Одна тема — один файл.** Не дублировать API/роуты в нескольких местах.

## Быстрый старт

| Шаг | Файл |
|-----|------|
| 1 | Корневой `README.md` (если есть) или `docs/DEVELOPMENT.md` |
| 2 | Этот `INDEX.md` |
| 3 | `WORK_COMPASS.md` — что уже сделано и что дальше |

## Активные документы (источник правды)

| Документ | Зачем |
|----------|--------|
| [DEVELOPMENT.md](./DEVELOPMENT.md) | Запуск локально, тесты, деплой, чеклист перед коммитом |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Слои, ядро, куда класть код |
| [WEB_API_SERVER.md](./WEB_API_SERVER.md) | Все эндпоинты Flask |
| [FRONTEND.md](./FRONTEND.md) | Роуты React, экраны, `botAdapter.js` |
| [GAMEPLAY_SYSTEMS.md](./GAMEPLAY_SYSTEMS.md) | Миры, боссы, инвентарь, тайная комната, True Lord |
| [STAGING.md](./STAGING.md) | VPS, деплой, проверка после выкладки |
| [WORK_COMPASS.md](./WORK_COMPASS.md) | Статус V2 и журнал |
| [DOCS_AUDIT.md](./DOCS_AUDIT.md) | История чистки docs |

## Архив

Старые черновики: [archive/legacy-2026-06/](./archive/legacy-2026-06/) (20 файлов).  
**Не ссылаться** из новых фич — только для справки по истории.

## Правило обновления

После каждой фичи:

1. `WORK_COMPASS.md` — статус.
2. Один профильный файл: `WEB_API_SERVER.md` / `FRONTEND.md` / `GAMEPLAY_SYSTEMS.md`.
3. При смене слоёв — `ARCHITECTURE.md`.
