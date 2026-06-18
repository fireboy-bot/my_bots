[#017]
Привет. Файл `core/score_manager.py` получил. Это финансовый центр «Числяндии» — управление балансом, начислениями, штрафами и интеграция с артефактами.

Ниже — готовая документация. Просто сохрани в `docs/CORE_SCORE_MANAGER.md`.

---

## 📄 Файл: `docs/CORE_SCORE_MANAGER.md`

```markdown
# 💰 ScoreManager — Управление очками и экономикой

> **Файл:** `core/score_manager.py`  
> **Версия:** 2.1 (Artifact Manager Init Fix) 💰🔮✅  
> **Ответственность:** Начисление/списание очков, применение бонусов артефактов, логирование транзакций

---

## 📋 Обзор

`ScoreManager` — центральный класс для управления игровой экономикой. Он абстрагирует все операции с очками, обеспечивая:

| Функция | Описание |
|---------|----------|
| 💰 Баланс | Чтение/запись `score_balance` (доступные очки) |
| 📈 Рейтинг | Накопление `total_score` (общий счёт за всё время) |
| 🎁 Бонусы | Применение эффектов артефактов при начислении |
| ⚠️ Штрафы | Снижение ущерба от Артефакта Силы |
| 📜 Логирование | Запись всех транзакций в `score_log` |
| 🔄 Переводы | Перемещение очков между игроками (админ) |

```
┌─────────────────┐
│   ScoreManager  │
├─────────────────┤
│ • add_score()   │ ← Начисление с бонусами
│ • spend_score() │ ← Покупки, траты
│ • apply_penalty│ ← Штрафы с защитой
│ • transfer_... │ ← Переводы (админ)
│ • reset_score()│ ← Сброс (админ)
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌──────────────┐
│Player  │ │ArtifactManager│
│Storage │ │(бонусы/штрафы)│
└────────┘ └──────────────┘
```

---

## ⚙️ Инициализация

```python
score_manager = ScoreManager(
    storage: PlayerStorage,
    castle_engine: Optional[CastleEngine] = None
)
```

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| `storage` | `PlayerStorage` | ✅ | Интерфейс для работы с БД пользователей |
| `castle_engine` | `CastleEngine` | ❌ | Ссылка на движок замка (для будущих интеграций) |

**Что происходит при инициализации:**
1. Сохраняются ссылки на `storage` и `castle_engine`
2. Создаётся экземпляр `ArtifactManager` для расчёта бонусов
3. Запись в лог: `✅ ScoreManager инициализирован с ArtifactManager`

---

## 💰 Основные методы

### `get_balance(user_id: str) -> int`
Возвращает доступный баланс игрока.

```python
balance = score_manager.get_balance("123456")
# → 1250
```

### `get_total_score(user_id: str) -> int`
Возвращает общий рейтинг (накопленные очки за всё время).

```python
rating = score_manager.get_total_score("123456")
# → 15420
```

> ⚠️ `total_score` никогда не уменьшается — только растёт или остаётся неизменным.

---

### `add_score(...) -> int` 🎯 Ключевой метод
Начисляет очки с учётом бонусов артефактов.

```python
def add_score(
    user_id: str,
    amount: int,                    # Базовое количество (без бонусов)
    reason: str,                    # Причина: "task_correct", "boss_defeat", etc.
    context: str = None,           # Доп. контекст: "island:addition", "boss:final"
    apply_artifacts: bool = True   # Применять бонусы артефактов?
) -> int:
    """
    Returns:
        int: Фактически начисленная сумма (с бонусами)
    """
```

**Алгоритм:**
```
1. Получить пользователя из storage
2. Если apply_artifacts=True и amount>0:
   └─ Вызвать artifact_manager.apply_score_bonus(user_id, amount)
3. Обновить score_balance и total_score
4. Сохранить пользователя
5. Записать в лог: logger.info(...)
6. Вызвать log_score_change() для детального лога
7. Вернуть final_amount
```

**Пример использования:**
```python
# Задача решена верно, базовая награда 50 очков
final = score_manager.add_score(
    user_id="123456",
    amount=50,
    reason="task_correct",
    context="island:addition,level:3"
)
# При наличии Артефакта Удачи (+10%): final = 55
```

**Бонусы артефактов:**
| Артефакт | Эффект | Применяется в |
|----------|--------|--------------|
| 🍀 Артефакт Удачи | +10% к награде | `add_score()` при `apply_artifacts=True` |
| ⚡ Артефакт Силы | Не применяется | — |

---

### `spend_score(...) -> Tuple[bool, str]`
Списывает очки (покупки, траты).

```python
def spend_score(
    user_id: str,
    amount: int,
    reason: str,
    context: str = None
) -> Tuple[bool, str]:
    """
    Returns:
        (True, "✅ Списано...") при успехе
        (False, "❌ Недостаточно очков!") при ошибке
    """
```

**Алгоритм:**
```
1. Проверить наличие пользователя
2. Проверить баланс: if balance < amount → ошибка
3. Списать: user["score_balance"] -= amount
4. Сохранить пользователя
5. Записать в лог
6. Вызвать log_score_change()
7. Вернуть результат
```

**Пример:**
```python
success, message = score_manager.spend_score(
    user_id="123456",
    amount=300,
    reason="shop_purchase",
    context="item:potion_health"
)
if success:
    await update.message.reply_text(message)
else:
    await update.message.reply_text(f"❌ {message}")
```

---

### `apply_penalty(...) -> int`
Применяет штраф за ошибку с учётом защиты артефактов.

```python
def apply_penalty(
    user_id: str,
    base_penalty: int,          # Отрицательное число, напр. -25
    reason: str = "mistake",
    context: str = None
) -> int:
    """
    Returns:
        int: Фактический штраф (может быть меньше базового)
    """
```

**Алгоритм:**
```
1. Вызвать artifact_manager.apply_penalty_reduction(user_id, base_penalty)
   └─ Артефакт Силы может снизить штраф на 20-50%
2. Обновить score_balance (уменьшить)
3. Обновить total_score: max(0, old_total + final_penalty)
   └─ Рейтинг никогда не уходит в минус!
4. Сохранить и залогировать
5. Вернуть final_penalty
```

**Пример:**
```python
# Базовый штраф -25, но есть Артефакт Силы (-30% к штрафам)
actual = score_manager.apply_penalty(
    user_id="123456",
    base_penalty=-25,
    reason="task_mistake",
    context="island:subtraction"
)
# actual = -18 (25 × 0.7 ≈ 18)
```

**Защита артефактов:**
| Артефакт | Эффект | Применяется в |
|----------|--------|--------------|
| ⚡ Артефакт Силы | -20%/-35%/-50% к штрафам | `apply_penalty()` |
| 🍀 Артефакт Удачи | Не применяется | — |

---

### `log_score_change(...) -> bool`
Записывает детальную запись о транзакции в `score_log`.

```python
def log_score_change(
    user_id: str,
    amount: int,          # Положительное или отрицательное
    reason: str,          # "task_correct", "shop_purchase", etc.
    context: str = None   # Доп. информация
) -> bool:
```

**Структура записи в БД:**
```python
{
    "user_id": "123456",
    "season_id": 1,
    "amount": 55,
    "reason": "task_correct",
    "context": "island:addition,level:3",
    "timestamp": "2026-04-05T14:30:00Z"
}
```

> ⚠️ Метод обернут в `try/except` — ошибка логирования не прерывает основную логику.

---

### `transfer_score(...) -> Tuple[bool, str]`
Переводит очки между игроками (только для админов).

```python
success, message = score_manager.transfer_score(
    from_user_id="123456",
    to_user_id="789012",
    amount=100,
    reason="admin_gift"
)
```

**Алгоритм:**
```
1. Вызвать spend_score(from_user_id, amount)
2. Если успех → вызвать add_score(to_user_id, amount)
3. Если неудача → вернуть ошибку без изменений
4. Записать в лог: 🔄 TRANSFER: A → B, N очков
```

> ⚠️ Не атомарная операция! При сбое после списания, но до начисления — возможна потеря очков. Для продакшена рекомендуется использовать транзакции БД.

---

### `reset_score(user_id: str) -> bool`
Сбрасывает баланс и рейтинг игрока (только для админов).

```python
if score_manager.reset_score("123456"):
    logger.info("✅ Score reset for user 123456")
```

**Что сбрасывается:**
| Поле | Новое значение |
|------|---------------|
| `score_balance` | `0` |
| `total_score` | `0` |

**Что НЕ сбрасывается:**
- Прогресс уровней
- Инвентарь и артефакты
- Статистика задач
- Данные банка

> ⚠️ Использовать с осторожностью! Не отменяет транзакции в `score_log`.

---

## 🔗 Интеграция с ArtifactManager

`ScoreManager` делегирует расчёт бонусов/штрафов классу `ArtifactManager`:

```python
# В add_score():
if apply_artifacts and amount > 0:
    final_amount = self.artifact_manager.apply_score_bonus(user_id, amount)

# В apply_penalty():
final_penalty = self.artifact_manager.apply_penalty_reduction(user_id, base_penalty)
```

**Поток данных:**
```
ScoreManager.add_score()
         │
         ▼
ArtifactManager.apply_score_bonus()
         │
         ▼
Проверка: есть ли у игрока "luck_artifact"?
         │
    ┌────┴────┐
    ▼         ▼
✅ Да      ❌ Нет
│         │
▼         ▼
amount × 1.10   amount
(уровень 1)
```

---

## ⚠️ Важные замечания

### 1. `total_score` никогда не уменьшается
```python
user["total_score"] = max(0, old_total + final_penalty)
```
Это предотвращает «откат» рейтинга при ошибках. Игрок может потерять доступные очки (`score_balance`), но не накопленный прогресс.

### 2. Бонусы применяются только при `amount > 0`
```python
if apply_artifacts and amount > 0:
    final_amount = self.artifact_manager.apply_score_bonus(...)
```
Это предотвращает некорректное применение бонусов к отрицательным значениям.

### 3. Логирование не критично
```python
try:
    self.storage.log_score_change(...)
except Exception as e:
    logger.error(f"❌ Ошибка log_score_change: {e}")
    return False  # Но основная операция уже выполнена!
```
Ошибка в логе не отменяет начисление/списание очков.

### 4. Типы `reason` для аналитики
Рекомендуемые значения для поля `reason`:
```
# Награды:
"task_correct", "boss_defeat", "level_complete", "daily_bonus"

# Траты:
"shop_purchase", "bank_deposit", "castle_upkeep", "artifact_upgrade"

# Штрафы:
"task_mistake", "boss_ability", "chaos_penalty"

# Админ:
"admin_gift", "admin_penalty", "transfer", "reset"
```

### 5. Сезонность
Метод `log_score_change()` автоматически добавляет `season_id` из профиля пользователя. Это позволяет фильтровать статистику по сезонам.

---

## 🧪 Примеры использования

```python
# 1. Награда за правильную задачу
score_manager.add_score(
    user_id=user_id,
    amount=50,
    reason="task_correct",
    context=f"island:{island_id},difficulty:easy"
)

# 2. Покупка в магазине
success, msg = score_manager.spend_score(
    user_id=user_id,
    amount=300,
    reason="shop_purchase",
    context="item:potion_health"
)
if not success:
    await update.message.reply_text(msg)

# 3. Штраф за ошибку (с защитой артефакта)
actual_penalty = score_manager.apply_penalty(
    user_id=user_id,
    base_penalty=-25,
    reason="task_mistake",
    context=f"island:{island_id}"
)

# 4. Перевод очков (админ)
success, msg = score_manager.transfer_score(
    from_user_id=admin_id,
    to_user_id=target_id,
    amount=1000,
    reason="admin_gift"
)

# 5. Получение баланса для отображения
balance = score_manager.get_balance(user_id)
total = score_manager.get_total_score(user_id)
await update.message.reply_text(f"💰 Баланс: {balance:,} | 🏆 Рейтинг: {total:,}")
```

---

## 🔄 Интеграция с другими модулями

```
manyunya_bot.py
       │
       ▼
ChislyandiaEngine
       │
       ▼
ScoreManager
       │
   ┌───┴───┬────────────┐
   ▼       ▼            ▼
add_   spend_    apply_
score() score()  penalty()
   │       │            │
   ▼       ▼            ▼
ArtifactManager  PlayerStorage  logger
(бонусы/штрафы)  (БД)          (логи)
```

---

*Документация актуальна для версии 2.1. Последнее обновление: `$(date)`*
```

---

## ✅ Что делать:

1. Создай файл `docs/CORE_SCORE_MANAGER.md` → вставь код выше → сохрани.

2. Закоммить:
   ```powershell
   git add docs/CORE_SCORE_MANAGER.md
   git commit -m "docs: add ScoreManager core module documentation"
   ```

---

## 🔄 Что дальше?

Следующие кандидаты на документацию (по приоритету):

1. `core/artifact_manager.py` — логика артефактов: бонусы, уровни, эффекты
2. `handlers/alchemy.py` — система крафта: рецепты, ресурсы, анимация
3. `core/castle_engine.py` — управление замком: декорации, содержание, разблокировка

Пришли код любого из этих файлов — сделаю документацию в том же формате.

Работаем медленно, но правильно. Жду твой выбор.