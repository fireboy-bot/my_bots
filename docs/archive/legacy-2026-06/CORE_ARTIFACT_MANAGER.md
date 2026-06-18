[#018]
Привет. Файл `core/artifact_manager.py` получил. Это модуль управления артефактами: прокачка, эффекты, баланс и зависимость от upkeep замка.

Ниже — готовая документация. Просто сохрани в `docs/CORE_ARTIFACT_MANAGER.md`.

---

## 📄 Файл: `docs/CORE_ARTIFACT_MANAGER.md`

```markdown
# 🔮 ArtifactManager — Управление артефактами

> **Файл:** `core/artifact_manager.py`  
> **Версия:** 1.1 (Fix: ARTIFACT_CONFIG Keys) 🔮✅  
> **Ответственность:** Прокачка артефактов, расчёт эффектов, проверка upkeep, применение бонусов

---

## 📋 Обзор

`ArtifactManager` — модуль, отвечающий за всё, что связано с артефактами в «Числяндии». Он обеспечивает:

| Функция | Описание |
|---------|----------|
| 🔧 Прокачка | Расчёт стоимости, проверка условий, обновление уровня |
| 💫 Эффекты | Бонусы к очкам, снижение штрафов, подсказки для боссов |
| 🔐 Upkeep-зависимость | Артефакты работают только при оплаченном содержании замка |
| 📊 Баланс | Капы эффектов, минимальные штрафы, лимиты за бой |

```
┌─────────────────────┐
│   ArtifactManager   │
├─────────────────────┤
│ • upgrade_artifact()│ ← Прокачка
│ • apply_*_bonus()   │ ← Применение эффектов
│ • get_upgrade_cost()│ ← Расчёт цены
│ • is_upkeep_active()│ ← Проверка замка
└────────┬────────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌──────────────┐
│Player  │ │CastleEngine  │
│Storage │ │(проверка     │
│(уровни)│ │upkeep)       │
└────────┘ └──────────────┘
```

---

## ⚙️ Инициализация

```python
artifact_manager = ArtifactManager(
    storage: PlayerStorage,
    castle_engine: Optional[CastleEngine] = None
)
```

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| `storage` | `PlayerStorage` | ✅ | Доступ к данным пользователя (уровни артефактов) |
| `castle_engine` | `CastleEngine` | ❌ | Для проверки статуса upkeep замка |

---

## 🎨 Конфигурация артефактов (`ARTIFACT_CONFIG`)

Встроенный словарь с параметрами всех артефактов. Не зависит от `items.py`.

```python
ARTIFACT_CONFIG = {
    "artifact_luck": { ... },    # 🍀 Бонус к очкам
    "artifact_power": { ... },   # ⚡ Снижение штрафов
    "artifact_wisdom": { ... },  # 🧠 Подсказки для боссов
}
```

### 📊 Параметры каждого артефакта

| Поле | Тип | Описание | Пример |
|------|-----|----------|--------|
| `name` | `str` | Отображаемое название | `"🍀 Артефакт Удачи"` |
| `base_price` | `int` | Цена первого уровня | `500` |
| `effect` | `str` | Тип эффекта | `"score_bonus"` |
| `base_value` | `float` | Базовое значение эффекта | `0.05` (+5%) |
| `per_level` | `float` | Прирост эффекта за уровень | `0.05` |
| `max_level` | `int` | Максимальный уровень прокачки | `10` |
| `max_value` | `float` | Кап значения эффекта | `0.40` (+40%) |
| `cost_multiplier` | `float` | Множитель роста цены | `1.4` |
| `requires_upkeep` | `bool` | Требует ли оплаты upkeep | `True` |
| `min_penalty` | `int` | Мин. штраф (только для `artifact_power`) | `2` |
| `max_per_battle` | `int` | Лимит за бой (только для `artifact_wisdom`) | `3` |

---

## 🔧 Основные методы

### `get_artifact_level(user_id, artifact_id) -> int`
Возвращает текущий уровень артефакта у игрока.

```python
level = artifact_manager.get_artifact_level("123456", "artifact_luck")
# → 3
```

---

### `get_upgrade_cost(artifact_id, current_level) -> int` 🎯
Считает стоимость следующего уровня по экспоненциальной формуле.

**Формула:**
```
стоимость = base_price × (cost_multiplier ^ current_level)
```

**Пример расчёта для `artifact_luck` (base_price=500, multiplier=1.4):**

| Уровень | Расчёт | Цена |
|---------|--------|------|
| 0 → 1 | 500 × 1.4⁰ | 500 |
| 1 → 2 | 500 × 1.4¹ | 700 |
| 2 → 3 | 500 × 1.4² | 980 |
| 3 → 4 | 500 × 1.4³ | 1 372 |
| ... | ... | ... |
| 9 → 10 | 500 × 1.4⁹ | ~10 541 |

```python
cost = artifact_manager.get_upgrade_cost("artifact_luck", current_level=2)
# → 980
```

---

### `get_effect_value(artifact_id, level) -> float`
Возвращает значение эффекта для уровня с учётом капа (`max_value`).

**Формула:**
```
значение = base_value + (per_level × (level - 1))
итог = min(значение, max_value)
```

**Пример для `artifact_luck` (base=0.05, per_level=0.05, max=0.40):**

| Уровень | Расчёт | Итог |
|---------|--------|------|
| 1 | 0.05 + 0.05×0 = 0.05 | 0.05 (+5%) |
| 3 | 0.05 + 0.05×2 = 0.15 | 0.15 (+15%) |
| 8 | 0.05 + 0.05×7 = 0.40 | 0.40 (+40%) ✅ кап |
| 10 | 0.05 + 0.05×9 = 0.50 | 0.40 (+40%) ✅ кап |

---

### `can_upgrade(user_id, artifact_id) -> Tuple[bool, str, int]`
Проверяет, можно ли улучшить артефакт.

**Возвращает:**
```python
(
    can_upgrade: bool,      # Можно ли улучшить
    message: str,           # Текст для пользователя
    cost: int               # Стоимость следующего уровня
)
```

**Логика проверки:**
```
1. Артефакт существует в ARTIFACT_CONFIG?
2. Игрок существует?
3. Текущий уровень < max_level?
4. Баланс игрока >= cost?
```

**Пример:**
```python
ok, msg, cost = artifact_manager.can_upgrade("123456", "artifact_luck")
if ok:
    await update.message.reply_text(f"✅ {msg}")
else:
    await update.message.reply_text(f"❌ {msg}")
```

---

### `upgrade_artifact(user_id, artifact_id) -> Tuple[bool, str]` 🎯
Выполняет улучшение артефакта.

**Алгоритм:**
```
1. Вызвать can_upgrade() → если ошибка, вернуть
2. Списать cost из score_balance
3. Обновить artifact_upgrades[user_id][artifact_id] += 1
4. Сохранить пользователя через storage.save_user()
5. Вернуть успешный результат с описанием нового эффекта
```

**Пример результата:**
```
✅ 🍀 Артефакт Удачи улучшен до уровня 4!
📊 Эффект: +20% к очкам за задачу
```

---

### `apply_score_bonus(user_id, base_score) -> int`
Применяет бонус от 🍀 Артефакта Удачи.

**Условия работы:**
- Уровень артефакта > 0
- ✅ Upkeep замка оплачен (`is_upkeep_active() == True`)

**Формула:**
```
бонус = base_score × effect_value
итог = base_score + бонус
```

**Пример:**
```python
# Уровень 3 → effect_value = 0.15 (+15%)
final = artifact_manager.apply_score_bonus("123456", base_score=50)
# → 50 + (50 × 0.15) = 57
```

> ⚠️ Если upkeep не оплачен — возвращается `base_score` без изменений.

---

### `apply_penalty_reduction(user_id, base_penalty) -> int`
Применяет снижение штрафа от ⚡ Артефакта Силы.

**Условия работы:**
- Уровень артефакта > 0
- ✅ Upkeep замка оплачен

**Формула:**
```
снижение = |base_penalty| × effect_value
новый_штраф = max(|base_penalty| - снижение, min_penalty)
итог = -новый_штраф  # сохраняем отрицательный знак
```

**Пример:**
```python
# Уровень 5 → effect_value = 0.50 (-50%), min_penalty = 2
# Базовый штраф: -25
final = artifact_manager.apply_penalty_reduction("123456", base_penalty=-25)
# → -max(25 × 0.5, 2) = -max(12.5, 2) = -12
```

> ⚠️ Минимальный штраф (`min_penalty`) гарантирует, что ошибка всегда имеет цену.

---

### `get_boss_hints(user_id) -> int`
Возвращает количество подсказок для боя с боссом от 🧠 Артефакта Мудрости.

**Условия работы:**
- Уровень артефакта > 0
- ✅ Upkeep замка оплачен
- Ограничение `max_per_battle` (по умолчанию 3)

**Пример:**
```python
# Уровень 7 → effect_value = 7, но max_per_battle = 3
hints = artifact_manager.get_boss_hints("123456")
# → min(7, 3) = 3
```

---

### `get_all_artifacts(user_id) -> Dict[str, Dict]`
Возвращает полную информацию по всем артефактам для отображения в интерфейсе.

**Структура возврата:**
```python
{
    "artifact_luck": {
        "name": "🍀 Артефакт Удачи",
        "level": 3,
        "max_level": 10,
        "effect": "+15% к очкам за задачу",
        "next_upgrade_cost": 1372,  # или None, если макс. уровень
        "is_maxed": False,
        "is_active": True  # только если requires_upkeep и upkeep оплачен
    },
    # ... другие артефакты
}
```

---

## 🔐 Зависимость от Upkeep замка

**Ключевое правило:** Артефакты с `requires_upkeep: True` работают **только** если содержание замка оплачено.

```python
def is_upkeep_active(self, user_id: str) -> bool:
    if not self.castle_engine:
        return True  # fallback: считаем активным
    castle_state = self.castle_engine.get_castle_state(user_id)
    return castle_state.get("bonuses_active", False)
```

**Почему это важно:**
- Создаёт стратегический выбор: тратить на замок или на артефакты?
- Предотвращает «фарм» бонусов без развития базы
- Усиливает роль `CastleEngine` в экономике игры

**Проверка в методах:**
```python
if not self.is_upkeep_active(user_id):
    logger.info(f"⚠️ Артефакт не активен: upkeep не оплачен")
    return base_value  # возвращаем значение без бонуса
```

---

## ⚠️ Важные замечания

### 1. Экспоненциальный рост цены
Формула `base × multiplier^level` быстро увеличивает стоимость:
- Уровень 1→2: ×1.4
- Уровень 9→10: ×~21 от базовой цены

**Совет:** Балансируйте `cost_multiplier` осторожно — слишком высокий множитель может сделать максимальный уровень недостижимым.

### 2. Капы эффектов обязательны
Все артефакты имеют `max_value`, чтобы избежать дисбаланса:
- Удача: макс. +40% к очкам
- Сила: макс. -75% штрафа (но не ниже `min_penalty`)
- Мудрость: макс. 10 подсказок, но не более 3 за бой

### 3. Логирование
Все важные действия логируются:
```python
logger.info(f"🔮 Артефакт {artifact_id} улучшен до уровня {new_level}")
logger.debug(f"🍀 Удача: {base_score} + {bonus} = {final_score}")
```
Проверяйте `logs/app.log` при отладке экономики.

### 4. Типы эффектов (`effect` поле)
| Значение | Метод применения | Описание |
|----------|-----------------|----------|
| `score_bonus` | `apply_score_bonus()` | Умножение награды на `(1 + value)` |
| `penalty_reduction` | `apply_penalty_reduction()` | Уменьшение штрафа с минимумом |
| `boss_hints` | `get_boss_hints()` | Количество подсказок за бой |

### 5. Безопасность данных
- Все изменения сохраняются через `storage.save_user()` — гарантируется целостность БД.
- Проверка `artifact_id in ARTIFACT_CONFIG` предотвращает инъекции несуществующих артефактов.

---

## 🔄 Интеграция с другими модулями

```
ScoreManager
     │
     ▼
ArtifactManager
     │
┌────┴────┬────────────┐
▼         ▼            ▼
apply_   upgrade_   get_all_
score_   artifact() artifacts()
bonus()
     │
     ▼
CastleEngine (опционально)
     │
     ▼
is_upkeep_active()
```

---

## 🧪 Примеры использования

```python
# 1. Проверка и улучшение артефакта
ok, msg, cost = artifact_manager.can_upgrade(user_id, "artifact_luck")
if ok:
    success, result_msg = artifact_manager.upgrade_artifact(user_id, "artifact_luck")
    await update.message.reply_text(result_msg)
else:
    await update.message.reply_text(f"❌ {msg}")

# 2. Применение бонуса при начислении очков
base_reward = 50
final_reward = artifact_manager.apply_score_bonus(user_id, base_reward)
score_manager.add_score(user_id, final_reward, reason="task_correct")

# 3. Отображение артефактов в интерфейсе
artifacts = artifact_manager.get_all_artifacts(user_id)
for art_id, data in artifacts.items():
    status = "✅" if data["is_active"] else "⏸"
    await update.message.reply_text(
        f"{status} {data['name']} [Ур. {data['level']}/{data['max_level']}]\n"
        f"📊 {data['effect']}"
        f"💰 След. уровень: {data['next_upgrade_cost']:,}" if data['next_upgrade_cost'] else ""
    )

# 4. Подсказки в бою с боссом
hints_available = artifact_manager.get_boss_hints(user_id)
if hints_available > 0:
    await update.message.reply_text(f"💡 У вас есть {hints_available} подсказок для этого боя!")
```

---

## 🛠 Чеклист при добавлении нового артефакта

1. [ ] Добавить запись в `ARTIFACT_CONFIG` с уникальным `artifact_id`
2. [ ] Указать все обязательные поля: `name`, `base_price`, `effect`, `base_value`, `per_level`, `max_level`, `max_value`, `cost_multiplier`
3. [ ] Если артефакт зависит от upkeep — добавить `"requires_upkeep": True`
4. [ ] Реализовать метод применения эффекта в `ArtifactManager` (или использовать существующий тип)
5. [ ] Добавить форматирование описания в `_format_effect()`
6. [ ] Протестировать: прокачка, применение эффекта, отключение при неоплаченном upkeep
7. [ ] Обновить `items.py` (если артефакт отображается в магазине)

---

*Документация актуальна для версии 1.1. Последнее обновление: `$(date)`*
```

---

## ✅ Что делать:

1. Создай файл `docs/CORE_ARTIFACT_MANAGER.md` → вставь код выше → сохрани.

2. Закоммить:
   ```powershell
   git add docs/CORE_ARTIFACT_MANAGER.md
   git commit -m "docs: add ArtifactManager core module documentation"
   ```

---

## 🔄 Что дальше?

Следующие кандидаты на документацию (по приоритету):

1. `core/castle_engine.py` — логика замка: upkeep, декорации, бонусы
2. `handlers/alchemy.py` — система крафта: рецепты, ресурсы, анимация
3. `handlers/narrative_manager.py` — управление фразами Владимира и персонажей

Пришли код любого из этих файлов — сделаю документацию в том же формате.

Работаем медленно, но правильно. Жду твой выбор.