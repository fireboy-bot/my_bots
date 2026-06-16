[#014]
Привет. Файл `core/game_engine.py` получил. Это действительно сердце проекта — сложный, но хорошо структурированный модуль.

Ниже — готовая документация. Просто сохрани в `docs/CORE_GAME_ENGINE.md`.

---

## 📄 Файл: `docs/CORE_GAME_ENGINE.md`

```markdown
# 🧠 ChislyandiaEngine — Главное ядро игры

> **Файл:** `core/game_engine.py`  
> **Версия:** 3.3 (Chaos System Integration) 🧠🔮🌋✅  
> **Ответственность:** Обработка игровых действий, проверка задач, экономика, хаос-механики

---

## 📋 Обзор

`ChislyandiaEngine` — единая точка входа для всех игровых действий. Класс абстрагирует логику игры от платформ (Telegram, VK) и координирует работу подсистем:

```
┌─────────────────────┐
│   ChislyandiaEngine │
├─────────────────────┤
│ • solve_task()      │ ← Проверка ответов, награда, хаос
│ • Banking:          │
│   - deposit/withdraw│ ← Вклад/снятие с процентами
│   - get_bank_info() │ ← Информация о вкладе
│ • Castle:           │
│   - pay_upkeep()    │ ← Оплата содержания замка
│ • Artifacts:        │
│   - upgrade_artifact│ ← Улучшение артефактов
│ • Profile:          │
│   - get_player_...  │ ← Статистика игрока
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│   Зависимости:      │
│ • PlayerStorage     │ ← Работа с БД (SQLite)
│ • ScoreManager      │ ← Начисление очков, артефакты
│ • CastleEngine      │ ← Логика замка
└─────────────────────┘
```

---

## ⚙️ Инициализация

```python
engine = ChislyandiaEngine(storage: PlayerStorage, score_manager: ScoreManager)
```

| Параметр | Тип | Описание |
|----------|-----|----------|
| `storage` | `PlayerStorage` | Интерфейс для работы с базой данных пользователей |
| `score_manager` | `ScoreManager` | Менеджер очков, артефактов и бонусов |

**Что происходит при инициализации:**
1. Сохраняются ссылки на `storage` и `score_manager`
2. Создаётся экземпляр `CastleEngine` для управления замком
3. Запись в лог: `✅ ChislyandiaEngine (ядро) инициализировано`

---

## 🔥 Chaos System — Механика «Разлома»

Система динамической сложности, реагирующая на ошибки игрока.

### 📊 Стадии Разлома (`_calculate_rift_stage`)

| Ошибок подряд | Стадия | Эффект |
|--------------|--------|--------|
| 0 | 0 — Спокойствие | Нормальный режим |
| 1–2 | 1 — Лёгкий треск | Числа слегка «плывут» |
| 3–4 | 2 — Числа плывут | Визуальные искажения |
| 5–6 | 3 — Нестабильность | Подсказки от персонажа |
| 7+ | 4 — Перегрузка | Блокировка наград, срочная помощь |

### 🌀 Состояния Артефакта Хаоса (`_get_artifact_chaos_state`)

```python
# Логика определения состояния:
if rift_stage >= 4 or chaos_energy >= 100:
    return "overload"    # 🔴 Перегрузка
elif chaos_energy >= 60:
    return "active"      # 🟡 Активен
elif chaos_energy >= 20:
    return "awakened"    # 🟢 Пробуждён
else:
    return "dormant"     # ⚪ Спящий
```

### 🔄 Энергия Хаоса

| Событие | Изменение `chaos_energy` |
|---------|-------------------------|
| ✅ Правильный ответ | `-10` (мин. 0) |
| ❌ Ошибка | `+20` (макс. 100) |
| 🔁 Задача-перенос решена | Дополнительный бонус |

---

## 🎯 Основной метод: `solve_task()`

```python
result = engine.solve_task(
    user_id: str,
    answer: Any,
    task_id: str,
    expected_answer: Any,
    island_id: Optional[str] = None,
    operation_type: Optional[str] = None,
    is_transfer: bool = False
) -> Dict[str, Any]
```

### 📥 Параметры

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| `user_id` | `str` | ✅ | Уникальный идентификатор игрока |
| `answer` | `Any` | ✅ | Ответ игрока (строка или число) |
| `task_id` | `str` | ✅ | ID задачи для логирования |
| `expected_answer` | `Any` | ✅ | Правильный ответ для сравнения |
| `island_id` | `str` | ❌ | ID острова (для контекста) |
| `operation_type` | `str` | ❌ | Тип операции: `addition`, `multiply` и т.д. |
| `is_transfer` | `bool` | ❌ | Флаг задачи-переноса (после ошибки) |

### 📤 Возвращаемое значение

```python
{
    "correct": bool,              # Был ли ответ верным
    "reward": int,                # Начислено/списано очков
    "message": str,               # Сообщение от персонажа
    "level_up": bool,             # Повышен ли уровень
    "chaos_state": {              # Состояние хаос-системы
        "rift_stage": int,        # 0–4
        "chaos_energy": int,      # 0–100
        "artifact_state": str,    # 'dormant'/'awakened'/'active'/'overload'
        "consecutive_errors": int # Ошибок подряд
    },
    "transfer_task": dict|None,   # Новая задача-перенос (если сгенерирована)
    "new_balance": int,           # Текущий баланс игрока
    "new_total_score": int        # Общий счёт за всё время
}
```

### 🔄 Логика работы

1. **Сравнение ответа**: `str(answer).strip() == str(expected_answer).strip()`
2. **Обновление статистики ошибок**:
   - ✅ Правильно → `consecutive_errors = 0`, `chaos_energy -= 10`
   - ❌ Ошибка → `consecutive_errors += 1`, `chaos_energy += 20`
3. **Расчёт награды**:
   - Базовая: `+50` за правильный, `-25` за ошибку
   - Анти-абуз: при 7+ ошибках подряд награда = `0` (штраф остаётся)
   - Задача-перенос: награда `-5` от базовой
4. **Генерация задачи-переноса** (если ошибка + 2+ подряд + не перенос):
   - Для `addition`/`multiplication`: перестановка слагаемых/множителей
   - Для других: заглушка с подсказкой
5. **Сообщение от персонажа** (Владимир) в зависимости от стадии Разлома
6. **Обновление профиля**: статистика, уровень, хаос-поля
7. **Логирование**: попытка задачи в `storage.log_task_attempt()`

---

## 🏦 Банковская система

### `get_bank_info(user_id: str) -> Dict`

Возвращает информацию о вкладе игрока.

```python
{
    "balance": int,           # Золото на руках (из кэша)
    "bank_balance": int,      # Вклад в банке (прямой запрос к БД)
    "interest_earned": int,   # Накопленные проценты
    "bank_interest": float,   # Ставка (по умолчанию 0.10 = 10%)
    "days_passed": int        # Дней с последнего начисления
}
```

> ⚠️ **Важно**: Банковские поля читаются **напрямую из БД**, минуя кэш `storage.get_user()`, чтобы избежать рассинхрона.

### `deposit_to_bank(user_id: str, amount: int) -> Tuple[bool, str]`

Положить золото в банк.

**Логика:**
1. Проверка баланса через `score_manager.spend_score()`
2. Прямое обновление `bank_balance` в БД
3. Сброс таймера процентов: `bank_last_interest_at = now`

**Возврат:** `(True, "✅ Вклад успешен!...")` или `(False, "❌ Ошибка...")`

### `withdraw_from_bank(user_id: str) -> Tuple[bool, str, int]`

Забрать вклад с процентами.

**Логика:**
1. Начисление накопленных процентов (`_apply_bank_interest()`)
2. Расчёт суммы: `bank_balance + interest_earned`
3. Обнуление вклада в БД
4. Начисление суммы на баланс через `score_manager.add_score()`

**Возврат:** `(True, "✅ Забрано ...", total_amount)` или `(False, "❌ ...", 0)`

### `_apply_bank_interest(conn, user_id)`

Внутренний метод: начисляет проценты за полные прошедшие дни.

```python
# Формула:
add_interest = bank_balance * bank_interest * full_days
```

> ✅ Вызывается автоматически при `get_bank_info()`, `deposit`, `withdraw`.

---

## 🏰 Замок (CastleEngine)

Делегирует управление замком отдельному модулю:

| Метод | Описание |
|-------|----------|
| `get_castle_info(user_id)` | Возвращает состояние замка (уровень, украшения, содержание) |
| `pay_castle_upkeep(user_id, days=1)` | Оплата содержания за указанное количество дней |

---

## 👤 Профиль игрока

### `get_player_profile(user_id: str) -> Dict`

Возвращает сводную статистику:

```python
{
    "user_id": str,
    "level": int,
    "xp": int,
    "total_score": int,          # Всего заработано
    "score_balance": int,        # Доступно сейчас
    "tasks_solved": int,         # Всего попыток
    "tasks_correct": int,        # Правильных ответов
    "inventory": List,           # Предметы
    "artifact_upgrades": Dict,   # Уровни артефактов
    # Chaos System:
    "chaos_energy": int,
    "rift_stage": int,
    "artifact_chaos_state": str,
    "consecutive_errors": int
}
```

---

## 🔮 Артефакты

Делегирует управление артефактами `score_manager.artifact_manager`:

| Метод | Описание |
|-------|----------|
| `get_artifact_info(user_id)` | Список артефактов игрока с уровнями и эффектами |
| `upgrade_artifact(user_id, artifact_id)` | Улучшение артефакта (проверка ресурсов, применение бонусов) |

---

## 🔧 Вспомогательные методы

| Метр | Назначение |
|------|-----------|
| `_generate_options()` | Генерация вариантов ответа для задач (правильный + 3 неверных) |
| `_generate_transfer_task()` | Создание задачи-переноса на основе оригинальной |
| `_get_character_message()` | Формирование реплики Владимира в зависимости от стадии хаоса |
| `_ensure_bank_columns()` | Миграция БД: добавление банковских полей при первом запуске |
| `_get_task_reward()` / `_get_task_penalty()` | Базовые значения награды/штрафа (заглушки для расширения) |
| `_check_level_progress()` | Проверка условия повышения уровня (заглушка) |

---

## ⚠️ Важные замечания

1. **Прямые запросы к БД**: Банковские операции используют прямые `sqlite3.connect()` запросы, минуя кэш `PlayerStorage`. Это гарантирует актуальность данных, но требует осторожности при рефакторинге.

2. **Анти-абуз**: При 7+ ошибках подряд награда за правильный ответ = `0`. Это предотвращает «фарм» очков через угадывание.

3. **Задачи-переносы**: Генерируются только если:
   - Ответ неверный
   - Ошибок подряд ≥ 2
   - Это не уже задача-перенос (`is_transfer=False`)

4. **Логирование**: Метод `log_task_attempt()` может отсутствовать в старых версиях `storage.py`. Ошибка обрабатывается через `try/except AttributeError`.

5. **Часовые пояса**: Все временные метки используют `datetime.now(timezone.utc)` для консистентности.

---

## 🔄 Интеграция с другими модулями

```
manyunya_bot.py
       │
       ▼
ChislyandiaEngine
       │
   ┌───┴───┬────────────┬────────────┐
   ▼       ▼            ▼            ▼
PlayerStorage  ScoreManager  CastleEngine  (артефакты)
   │            │            │            │
   ▼            ▼            ▼            ▼
SQLite БД   Начисление    Замок,     Эффекты,
пользователей  очков,     содержание  улучшения
              бонусы
```

---

## 🧪 Пример использования

```python
# Инициализация
engine = ChislyandiaEngine(storage, score_manager)

# Проверка ответа
result = engine.solve_task(
    user_id="123456",
    answer="42",
    task_id="add_001",
    expected_answer="42",
    island_id="addition",
    operation_type="addition"
)

# Обработка результата
if result["correct"]:
    await update.message.reply_text(f"✅ {result['message']} +{result['reward']} очков")
    if result["transfer_task"]:
        # Показать задачу-перенос
        pass
else:
    await update.message.reply_text(f"❌ {result['message']}")

# Проверка состояния хаоса
chaos = result["chaos_state"]
if chaos["artifact_state"] == "overload":
    await update.message.reply_text("🔴 Артефакт перегружен! Дайте ему отдохнуть.")
```

---

*Документация актуальна для версии 3.3. Последнее обновление: `$(date)`*
```

---

## ✅ Что делать:

1. Создай файл `docs/CORE_GAME_ENGINE.md` → вставь код выше → сохрани.

2. Закоммить:
   ```powershell
   git add docs/CORE_GAME_ENGINE.md
   git commit -m "docs: add ChislyandiaEngine core module documentation"
   ```

---

## 🔄 Что дальше?

Следующие кандидаты на документацию (по приоритету):

1. `handlers/universal_callback.py` — как обрабатываются нажатия кнопок (критично для UI)
2. `platforms/telegram_adapter.py` — интеграция с Telegram API
3. `core/score_manager.py` — логика начисления очков и артефактов

Пришли код любого из этих файлов — сделаю документацию в том же формате.

Работаем медленно, но правильно. Жду твой выбор.