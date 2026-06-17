# 🧭 Числяндия — Рабочий компас (Web MVP → V2)

> Обновляй этот файл после каждой сессии.  
> Правило: один чекбокс = одна законченная задача.

**Проект:** `C:\Users\Fireboy\Dev\Projects\Chislyandia`  
**Старт спринта:** 2026-06-16  
**Фокус:** Web MVP закрыт → V2 (карта миров, боссы, паритет с TG)

---

## 🎯 Цель спринта (MVP) — выполнено

Собрать **играбельный web** на том же ядре/SQLite, что и Telegram:
- меню → задачи → очки
- банк / замок / артефакты / алхимия
- staging для демо

**Не в MVP:** полный паритет с TG (боссы, level-up в web, инвентарь → V2).

---

## 📍 Где мы сейчас (снимок)

| Зона | Статус | Комментарий |
|------|--------|-------------|
| Telegram бот | ✅ | `manyunya_bot.py` — полевые тесты локально |
| Flask API | ✅ | `web/api_server.py` — прокси к ядру |
| React frontend | ✅ | 8 экранов + Worlds + Boss |
| API ↔ Frontend | ✅ | `botAdapter.js`, порт 5000 |
| Алхимия web | ✅ | `core/alchemy.py`, без telegram |
| Тесты | ✅ | pytest smoke (`scripts/run-tests.ps1`) |
| Staging | ✅ | http://147.45.225.173 — проверен вручную |
| Выбор мира (V2 ф.1) | ✅ | карта островов, забеги 10 задач |
| Боссы web | ✅ | `BossScreen`, API boss_run |
| Level-up / победа UI | 🟡 | `GameEventOverlay` — только что |

**Локально:** бот + `data/progress.db`  
**На VPS:** web + API + отдельная `progress.db` (демо-user `331113480`)

**Текущий этап:** V2 фаза 2 — полировка UX  
**Следующий шаг:** финальный босс, артефакты, визуал

---

## ✅ Definition of Done (web MVP)

- [x] Один API-адаптер (`botAdapter.js`)
- [x] `VITE_API_URL` согласован
- [x] TaskScreen — реальный профиль
- [x] Меню → задача → ответ → баланс в SQLite
- [x] Банк, замок, артефакты, алхимия
- [x] `userId` из URL
- [x] `npm run build` проходит
- [x] pytest smoke на API
- [x] Staging поднят
- [ ] Ручной чеклист на staging (частично — «всё включилось»)

---

## 🗓️ V2 — фаза 1 (в работе)

- [x] `core/progression.py` — каталог миров, `unlocked_zones`
- [x] API: `GET /api/game/worlds/:user_id`
- [x] `WorldsScreen` + роут `/game/worlds/:userId`
- [x] TaskScreen: мир из URL `/game/task/:userId/:worldId`
- [x] Проверка закрытых миров (403 на API)
- [x] Забег 10 задач + завершение острова (`core/level_run.py`)
- [x] Открытие следующего острова после прохождения
- [x] Web-экран боссов (`BossScreen`)
- [x] Level-up / победа — `GameEventOverlay`
- [x] Деплой V2 на staging (nginx + CSS-in-JS)

---

## 🧪 Ручной чеклист (staging)

```
[x] GET /api/health → ok
[x] Меню, банк, алхимия, F5 — прогресс сохраняется
[ ] Меню → «В БОЙ» → экран островов
[ ] Выбор открытого острова → задача
[ ] Закрытый остров — недоступен
[ ] Правильный / неправильный ответ
[ ] Победа острова / level-up overlay
[ ] Бой с боссом → победа overlay
```

**URL:** http://147.45.225.173/game/menu/331113480

---

## 🧠 Технический долг (V2+)

- [ ] Финальный босс + артефакты (web)
- [ ] Инвентарь в UI
- [ ] Тайная комната
- [ ] Визуальный редизайн (отложено)
- [ ] Синхронизация локальной БД бота и VPS

---

## 📝 Журнал сессий

### 2026-06-17 — Staging стабилен + V2 UX
**Сделано:**
- Фикс nginx (gzip/sendfile off), CSS встроен в JS-бандл
- Алхимия через `core/alchemy.py`, seed не затирает прогресс
- Ручной чеклист staging пройден (алхимия, банк, F5)
- `GameEventOverlay` — level-up, победа острова, победа босса
- Коммит `bf0403d`

### 2026-06-16 — Сессия 4 (staging + V2 ф.1)
**Сделано:**
- Staging на Timeweb: nginx, gunicorn, seed user `331113480`
- Фиксы: transfer-задачи, частицы, CSS/gzip, ErrorBoundary
- `core/progression.py`, WorldsScreen, API `/api/game/worlds`
- TaskScreen читает мир из URL, не `unlocked_zones[-1]`

**Команды:**
```powershell
.\scripts\run-tests.ps1
.\scripts\deploy-staging.ps1
```

### 2026-06-16 — Сессия 3 (тесты)
- `tests/test_api_smoke.py` — smoke на API
- Фиксы: банк, штраф −25, castle migration

---

## 🎛 Режимы работы с AI

| Задача | Режим |
|--------|-------|
| План, приоритеты | Без агент-режима |
| Код, тесты, деплой | Агент-режим |
