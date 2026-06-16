[#019]
Привет. Файл `core/castle_engine.py` получил. Это модуль управления замком: декорации, upkeep, бонусы и прямые обновления БД.

Ниже — готовая документация. Просто сохрани в `docs/CORE_CASTLE_ENGINE.md`.

---

## 📄 Файл: `docs/CORE_CASTLE_ENGINE.md`

```markdown
# 🏰 CastleEngine — Управление замком и декорациями

> **Файл:** `core/castle_engine.py`  
> **Версия:** 2.2 (Fix: JSON Parse in get_decoration_level) 🏰✨✅  
> **Ответственность:** Декорации замка, оплата upkeep, расчёт бонусов, прямые обновления БД

---

## 📋 Обзор

`CastleEngine` — модуль, отвечающий за систему замка в «Числяндии». Он обеспечивает:

| Функция | Описание |
|---------|----------|
| 🎨 Декорации | Покупка и улучшение декораций с экспоненциальным ростом цены |
| 🔁 Upkeep | Оплата содержания замка для активации бонусов |
| 📊 Бонусы | Расчёт суммарного бонуса от всех декораций |
| 🗄 Прямые обновления БД | Минуя кэш `storage.save_user()` для критичных полей |

```
┌─────────────────┐
│   CastleEngine  │
├─────────────────┤
│ • upgrade_decoration() │ ← Покупка/улучшение
│ • pay_upkeep()        │ ← Оплата содержания
│ • get_castle_state()  │ ← Состояние замка
│ • _calculate_...()    │ ← Расчёт бонусов
└────────┬─────────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌──────────────┐
│Player  │ │CASTLE_       │
│Storage │ │DECORATIONS   │
│(БД)    │ │(конфиг)      │
└────────┘ └──────────────┘
```

---

## ⚙️ Инициализация

```python
castle_engine = CastleEngine(storage: PlayerStorage)
```

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| `storage` | `PlayerStorage` | ✅ | Интерфейс для работы с базой данных пользователей |

**Что происходит при инициализации:**
1. Сохраняется ссылка на `storage`
2. Запись в лог: `✅ CastleEngine инициализирован`

---

## 🎨 Конфигурация декораций (`CASTLE_DECORATIONS`)

Внешний словарь (импортируется из `items.py`) с параметрами всех декораций.

**Структура одной декорации:**
```python
{
    "id": "fountain",                    # Уникальный идентификатор
    "name": "✨ Фонтан Мудрости",        # Отображаемое название
    "description": "+5% к очкам",        # Описание эффекта
    "base_price": 300,                   # Цена первого уровня
    "bonus_per_level": 0.05,             # Бонус за уровень (5%)
    "max_bonus": 0.25,                   # Максимальный бонус (25%)
    "max_level": 5,                      # Максимальный уровень прокачки
    "cost_multiplier": 1.5,              # Множитель роста цены
}
```

---

## 🔧 Основные методы

### `get_castle_state(user_id: str) -> Dict[str, Any]`
Возвращает полное состояние замка игрока.

**Возвращаемое значение:**
```python
{
    "upkeep_paid_until": float,      # Timestamp окончания upkeep
    "bonuses_active": bool,          # Активны ли бонусы сейчас
    "days_remaining": int,           # Дней до конца upkeep
    "decoration_upgrades": Dict,     # {decoration_id: level}
    "total_bonus": float,            # Суммарный бонус (0.0–1.0)
    "total_bonus_display": str       # Форматированный бонус для UI
}
```

**Логика проверки upkeep:**
```python
now = datetime.now(timezone.utc).timestamp()
bonuses_active = upkeep_paid_until > now
```

> ⚠️ **Важно:** Метод конвертирует `upkeep_paid_until` из строки в float для обратной совместимости.

---

### `get_decoration_level(user_id, decoration_id) -> int`
Возвращает текущий уровень декорации у игрока.

**Особенность:** Использует `_parse_decoration_upgrades()` для обработки как `dict`, так и `JSON-строки`.

```python
level = castle_engine.get_decoration_level("123456", "fountain")
# → 3
```

---

### `get_decoration_bonus(decoration_id, level) -> float`
Возвращает значение бонуса для указанного уровня с учётом капа.

**Формула:**
```
бонус = bonus_per_level + (bonus_per_level × (level - 1))
итог = min(бонус, max_bonus)
```

**Пример для фонтана (base=0.05, max=0.25):**

| Уровень | Расчёт | Итог |
|---------|--------|------|
| 1 | 0.05 + 0.05×0 = 0.05 | 0.05 (+5%) |
| 3 | 0.05 + 0.05×2 = 0.15 | 0.15 (+15%) |
| 5 | 0.05 + 0.05×4 = 0.25 | 0.25 (+25%) ✅ кап |
| 6 | 0.05 + 0.05×5 = 0.30 | 0.25 (+25%) ✅ кап |

---

### `get_upgrade_cost(decoration_id, current_level) -> int` 🎯
Считает стоимость следующего уровня по экспоненциальной формуле.

**Формула:**
```
стоимость = base_price × (cost_multiplier ^ current_level)
```

**Пример для фонтана (base_price=300, multiplier=1.5):**

| Уровень | Расчёт | Цена |
|---------|--------|------|
| 0 → 1 | 300 × 1.5⁰ | 300 |
| 1 → 2 | 300 × 1.5¹ | 450 |
| 2 → 3 | 300 × 1.5² | 675 |
| 3 → 4 | 300 × 1.5³ | 1 012 |
| 4 → 5 | 300 × 1.5⁴ | 1 518 |

---

### `upgrade_decoration(user_id, decoration_id) -> Tuple[bool, str]` 🎯
Выполняет покупку или улучшение декорации.

**Алгоритм:**
```
1. Найти конфигурацию декорации в CASTLE_DECORATIONS
2. Получить текущий уровень через get_decoration_level()
3. Проверить: уровень < max_level?
4. Рассчитать стоимость через get_upgrade_cost()
5. Проверить баланс игрока
6. Списать золото через ScoreManager.spend_score()
7. ✅ ПРЯМО ОБНОВИТЬ БД:
   - Получить текущие decoration_upgrades (парсинг JSON)
   - Обновить уровень: current_upgrades[decoration_id] = new_level
   - Сохранить: json.dumps(current_upgrades)
8. Вернуть успешный результат с описанием нового бонуса
```

**Пример результата:**
```
✅ ✨ Фонтан Мудрости улучшена до уровня 3!
📊 Бонус: +15% к очкам
💰 Списано: 675 золотых
```

> ⚠️ **Важно:** Метод использует прямое подключение к БД (`sqlite3.connect()`) для обновления `decoration_upgrades`, минуя кэш `storage.save_user()`. Это гарантирует актуальность данных, но требует осторожности при рефакторинге.

---

### `pay_upkeep(user_id, days=1) -> Tuple[bool, str]`
Оплачивает содержание замка на указанное количество дней.

**Параметры:**
| Параметр | Тип | По умолчанию | Описание |
|----------|-----|-------------|----------|
| `user_id` | `str` | — | ID пользователя |
| `days` | `int` | `1` | Количество дней для оплаты |

**Стоимость:** `50 золота × days`

**Логика:**
```
1. Рассчитать стоимость: cost = 50 * days
2. Проверить баланс через user.get("score_balance")
3. Списать золото через ScoreManager.spend_score()
4. Получить текущий upkeep_paid_until из castle_data
5. ✅ Конвертировать строку в float (обратная совместимость)
6. Если upkeep уже активен → добавить дни к текущей дате
   Иначе → установить новую дату от текущего времени
7. Обновить castle_data["upkeep_paid_until"] и сохранить пользователя
8. Вернуть успешный результат
```

**Пример:**
```python
success, message = castle_engine.pay_upkeep("123456", days=7)
# → (True, "✅ Содержание замка оплачено на 7 дн.!\n💰 Списано: 350 золотых...")
```

---

### `get_total_castle_bonus(user_id) -> float`
Возвращает суммарный бонус замка с учётом статуса upkeep.

```python
bonus = castle_engine.get_total_castle_bonus("123456")
# → 0.25 (если upkeep активен и есть декорации)
# → 0.0  (если upkeep не оплачен)
```

> ⚠️ Если `bonuses_active == False`, метод возвращает `0.0` независимо от уровней декораций.

---

## 🔧 Вспомогательные функции

### `_parse_decoration_upgrades(data) -> Dict[str, int]`
Универсальный парсер для поля `decoration_upgrades`.

**Логика:**
```python
if data is None:
    return {}
if isinstance(data, dict):
    return data                      # Уже dict — возвращаем как есть
if isinstance(data, str):
    try:
        return json.loads(data)      # Парсим JSON-строку
    except:
        return {}                    # Ошибка парсинга → пустой dict
return {}
```

**Зачем это нужно:**
- В старых версиях бота `decoration_upgrades` мог сохраняться как JSON-строка
- В новых — как `dict`
- Функция обеспечивает обратную совместимость без миграции БД

---

### `_calculate_total_bonus(decoration_upgrades, bonuses_active) -> float`
Считает суммарный бонус от всех декораций.

**Алгоритм:**
```
1. Если bonuses_active == False → вернуть 0.0
2. Для каждой декорации в CASTLE_DECORATIONS:
   ├─ Получить уровень из decoration_upgrades
   ├─ Если level > 0:
   │  ├─ Рассчитать бонус: base + (per_level × (level - 1))
   │  ├─ Применить кап: min(bonus, max_bonus)
   │  └─ Добавить к total_bonus
3. Вернуть total_bonus
```

**Пример:**
```
Игрок имеет:
- Фонтан (ур. 3, бонус +15%)
- Сад (ур. 2, бонус +10%)
- Флаг (ур. 1, бонус +5%)

total_bonus = 0.15 + 0.10 + 0.05 = 0.30 (+30%)
```

---

## ⚠️ Важные замечания

### 1. Прямые обновления БД
Методы `upgrade_decoration()` и `pay_upkeep()` используют прямое подключение к БД:
```python
conn = sqlite3.connect("data/progress.db")
c = conn.cursor()
# ... запросы ...
conn.commit()
conn.close()
```

**Почему так:**
- Гарантирует атомарность обновления конкретного поля
- Избегает рассинхрона между кэшем `storage.get_user()` и БД
- Ускоряет операцию (не нужно загружать/сохранять весь профиль)

**Риски:**
- При изменении схемы БД нужно обновлять запросы вручную
- Нет автоматического логирования через `storage.log_*()`

### 2. Конвертация строк в float
Методы обрабатывают `upkeep_paid_until` как возможную строку:
```python
if isinstance(upkeep_paid_until, str):
    try:
        upkeep_paid_until = float(upkeep_paid_until)
    except (ValueError, TypeError):
        upkeep_paid_until = 0
```

Это обеспечивает совместимость со старыми записями БД.

### 3. Зависимость от ScoreManager
Для списания золота используется `ScoreManager.spend_score()`, а не прямое изменение баланса:
```python
from core.score_manager import ScoreManager
score_manager = ScoreManager(self.storage)
success, message = score_manager.spend_score(...)
```

Это гарантирует:
- Единое логирование транзакций
- Применение эффектов артефактов (если будут)
- Валидацию баланса в одном месте

### 4. Upkeep как «выключатель» бонусов
Бонусы декораций работают **только** при активном upkeep:
```
if not bonuses_active:
    return 0.0  # Все бонусы отключены
```

Это создаёт стратегический выбор: платить за upkeep или терять бонусы.

---

## 🔄 Интеграция с другими модулями

```
manyunya_bot.py
     │
     ▼
ChislyandiaEngine
     │
     ▼
CastleEngine
     │
┌────┴────┬────────────┐
▼         ▼            ▼
upgrade_  pay_     get_castle_
decoration() upkeep() state()
     │         │            │
     ▼         ▼            ▼
ScoreManager  sqlite3   CASTLE_
(списание)    (прямые   DECORATIONS
              запросы)  (конфиг)
```

---

## 🧪 Примеры использования

```python
# 1. Проверка состояния замка
state = castle_engine.get_castle_state(user_id)
if state["bonuses_active"]:
    await update.message.reply_text(
        f"🏰 Бонусы активны: {state['total_bonus_display']}\n"
        f"⏳ Осталось дней: {state['days_remaining']}"
    )
else:
    await update.message.reply_text(
        "❌ Бонусы не активны! Оплатите upkeep в /castle"
    )

# 2. Улучшение декорации
success, message = castle_engine.upgrade_decoration(user_id, "fountain")
await update.message.reply_text(message)

# 3. Оплата upkeep
success, message = castle_engine.pay_upkeep(user_id, days=30)
if success:
    await update.message.reply_text(f"✅ {message}\n🎁 Бонусы активированы!")

# 4. Расчёт бонуса для задачи
bonus = castle_engine.get_total_castle_bonus(user_id)
final_score = int(base_score * (1 + bonus))
```

---

## 🛠 Чеклист при добавлении новой декорации

1. [ ] Добавить запись в `CASTLE_DECORATIONS` (в `items.py`) с уникальным `id`
2. [ ] Указать все обязательные поля: `name`, `base_price`, `bonus_per_level`, `max_bonus`, `max_level`, `cost_multiplier`
3. [ ] Протестировать: покупка, улучшение, расчёт бонуса, отключение при неоплаченном upkeep
4. [ ] Обновить интерфейс `/castle` для отображения новой декорации
5. [ ] Добавить фразу для Владимира в `vladimir_phrases.json` (опционально)

---

*Документация актуальна для версии 2.2. Последнее обновление: `$(date)`*
```

---

## ✅ Что делать:

1. Создай файл `docs/CORE_CASTLE_ENGINE.md` → вставь код выше → сохрани.

2. Закоммить:
   ```powershell
   git add docs/CORE_CASTLE_ENGINE.md
   git commit -m "docs: add CastleEngine core module documentation"
   ```

---

## 🔄 Что дальше?

Следующие кандидаты на документацию (по приоритету):

1. `handlers/alchemy.py` — система крафта: рецепты, ресурсы, анимация
2. `handlers/narrative_manager.py` — управление фразами Владимира и персонажей
3. `database/storage.py` — работа с БД: пользователи, прогресс, логирование

Пришли код любого из этих файлов — сделаю документацию в том же формате.

Работаем медленно, но правильно. Жду твой выбор.