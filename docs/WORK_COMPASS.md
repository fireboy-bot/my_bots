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
| React frontend | ✅ | 8 экранов (+ WorldsScreen) |
| API ↔ Frontend | ✅ | `botAdapter.js`, порт 5000 |
| Алхимия web | ✅ | `POST /api/alchemy/:user_id/craft` |
| Тесты | ✅ | 13+ pytest smoke (`scripts/run-tests.ps1`) |
| Staging | ✅ | http://147.45.225.173 — VPS Timeweb, SSH `timeweb-vps` |
| Выбор мира (V2 ф.1) | 🟡 | `core/progression.py` + `/game/worlds/:userId` |

**Локально:** бот + `data/progress.db`  
**На VPS:** web + API + отдельная `progress.db` (демо-user `331113480`)

**Текущий этап:** V2 фаза 1 — карта миров  
**Следующий шаг:** level-up в web, затем боссы

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
- [ ] Level-up уведомление игрока (XP) — частично в ответе API
- [ ] Деплой V2 на staging

---

## 🧪 Ручной чеклист (staging)

```
[ ] GET /api/health → ok
[ ] Меню → «В БОЙ» → экран островов
[ ] Выбор открытого острова → задача
[ ] Закрытый остров — недоступен
[ ] Правильный / неправильный ответ
[ ] Банк, замок, артефакты, алхимия
[ ] F5 — данные не откатываются в мок
```

**URL:** http://147.45.225.173/game/menu/331113480

---

## 🧠 Технический долг (V2+)

- [ ] Web-экран боссов
- [ ] Level-up / прохождение острова (как в TG)
- [ ] Инвентарь
- [ ] Тайная комната
- [ ] Частицы хаоса — красивее (отложено)
- [ ] Синхронизация локальной БД бота и VPS

---

## 📝 Журнал сессий

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
