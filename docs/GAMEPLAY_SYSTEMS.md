# Gameplay Systems (Web V2)

Этот файл фиксирует фактическое состояние игровых систем в web-версии.

## Прогрессия

- Миры берутся из `core/progression.py` и `core/level_run.py`.
- Островной забег: 10 задач, затем бой с островным боссом.
- После победы над островными боссами открывается `final_boss`.
- После `final_boss` открываются пост-гейм миры (`time_world`, `measure_world`, `logic_world`) и доступ к хранителям.
- После победы над 3 хранителями открывается `true_lord`.

## Боссы (обычный режим)

Логика: `core/boss_run.py`

- Стандартные боссы: 5 HP.
- `true_lord` в обычном режиме не используется, для него есть спец-движок.
- Ответы проходят через `/api/game/check_answer` с `operation_type: "boss"`.

## Истинный Владыка (эпический режим)

Логика: `core/true_lord_run.py` + `frontend/src/screens/TrueLordScreen.jsx`

- HP: 20
- Задачи: 60 случайных из `data/bosses/true_lord.json`
- Фазы:
  - `calm` (>30% HP)
  - `angry` (1..30% HP)
  - `desperate` (0% HP)
- При ошибке текущая задача не меняется.
- Экономика:
  - верный ответ: +150 очков, +XP
  - ошибка: -20 очков, -10 XP
  - победа: +500 очков, +200 XP
- Награда: `душа_числяндии`
- Подсказка: `/api/game/true-lord/hint` (штраф или бесплатно по модификаторам)
- Секретный текст: только если бой пройден без подсказок.

## Тайная комната

Логика: `core/secret_room_engine.py`

API:

- `GET /api/secret_room/<user_id>`
- `POST /api/secret_room/<user_id>/explore`
- `POST /api/secret_room/<user_id>/answer`

UI: `SecretRoomScreen`.

## Инвентарь

Логика: `core/inventory_view.py`

API:

- `GET /api/inventory/<user_id>`

UI: `InventoryScreen`.

Группы в выдаче:

- `consumables`
- `trophies`
- `artifacts`
- `secret_items`

## Что ещё в техдолге

- Синхронизация БД bot ↔ VPS.
- Редизайн UI (единый визуальный стиль).
- Расширение взаимодействия предметов с боевыми экранами.
