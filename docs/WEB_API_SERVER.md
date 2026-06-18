# Web API Server (`web/api_server.py`)

Flask API — тонкий адаптер между фронтендом и ядром (`ChislyandiaEngine`).
Бизнес-логика живет в `core/*`, API только валидирует вход и возвращает JSON.

## Базовая информация

- Локальный запуск: `python web/api_server.py`
- Порт: `5000` (`WEB_API_PORT`, если задан)
- Health: `GET /api/health`
- CORS: открыт на `"/api/*"` для всех origin

## Инициализация

При старте создаются singleton-объекты:

- `storage = PlayerStorage()`
- `score_manager = ScoreManager(storage)`
- `engine = ChislyandiaEngine(storage, score_manager)`

## Эндпоинты

### Health

- `GET /api/health`

### Профиль

- `GET /api/player/<user_id>/profile`
- `GET /api/game/progress/<user_id>` (алиас)

### Миры и забеги

- `GET /api/game/worlds/<user_id>`
- `POST /api/game/level/start`  
  body: `{ "user_id": "...", "world": "addition|subtraction|..." }`
- `GET /api/game/task?user_id=<id>&world=<world>`

### Ответ на задачу

- `POST /api/game/check_answer`
- `POST /api/game/answer` (алиас)

Минимальное тело:

```json
{
  "user_id": "331113480",
  "answer": "42",
  "task_id": "addition_xxx"
}
```

Дополнительно поддерживается:

- `expected_answer`
- `island_id`
- `operation_type`
- `is_transfer`

### Боссы

- `GET /api/game/bosses/<user_id>`
- `POST /api/game/boss/start`  
  body: `{ "user_id": "...", "boss_id": "null_void|...|true_lord" }`
- `GET /api/game/boss/state/<user_id>`
- `POST /api/game/boss/exit`

### Истинный Владыка (эпик-режим)

- `POST /api/game/true-lord/hint`  
  body: `{ "user_id": "..." }`

Примечание: сам бой стартует через обычный `POST /api/game/boss/start` с `boss_id="true_lord"`,
дальше ответы идут через стандартный `check_answer`, а логика делегируется в `core/true_lord_run.py`.

### Экономика

- `GET /api/bank/<user_id>`
- `POST /api/bank/<user_id>/deposit`
- `POST /api/bank/<user_id>/withdraw`

- `GET /api/castle/<user_id>`
- `POST /api/castle/<user_id>/upkeep`
- `POST /api/castle/<user_id>/upgrade_decoration`

- `GET /api/artifacts/<user_id>`
- `POST /api/artifacts/<user_id>/upgrade`

- `POST /api/alchemy/<user_id>/craft`

### Инвентарь и тайная комната

- `GET /api/inventory/<user_id>`
- `GET /api/secret_room/<user_id>`
- `POST /api/secret_room/<user_id>/explore`
- `POST /api/secret_room/<user_id>/answer`

## Контракт ошибок

- `400` — отсутствуют обязательные поля/невалидный запрос
- `403` — доступ заблокирован правилами прогрессии
- `404` — игрок/сущность не найдены
- `500` — исключение сервера

Ошибки возвращаются в формате:

```json
{ "error": "..." }
```

или для action-эндпоинтов:

```json
{ "success": false, "message": "..." }
```

## Проверка после деплоя

Минимальный smoke:

1. `GET /api/health` => `status=ok`
2. `GET /api/game/worlds/331113480` => список миров
3. `GET /api/game/bosses/331113480` => каталог боссов
4. `GET /api/inventory/331113480` => JSON без server error
