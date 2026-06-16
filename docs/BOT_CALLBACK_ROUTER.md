[#015]
Привет. Файл `handlers/universal_callback.py` получил. Это критически важный модуль — «диспетчер» всех нажатий кнопок в боте.

Ниже — готовая документация. Просто сохрани в `docs/BOT_CALLBACK_ROUTER.md`.

---

## 📄 Файл: `docs/BOT_CALLBACK_ROUTER.md`

```markdown
# 🔘 Universal Callback Handler — Диспетчер нажатий кнопок

> **Файл:** `handlers/universal_callback.py`  
> **Ответственность:** Маршрутизация `callback_query` от кнопок к специализированным обработчикам  
> **Ключевой принцип:** Единая точка входа для всех интерактивных элементов интерфейса

---

## 📋 Обзор

`universal_callback_handler` — это асинхронная функция, которая обрабатывает все нажатия кнопок (инлайн-кнопок) в боте. Вместо того чтобы регистрировать десятки отдельных `CallbackQueryHandler`, мы используем один универсальный хендлер, который по префиксу `data` определяет, какому модулю делегировать обработку.

```
Пользователь нажимает кнопку
         │
         ▼
┌─────────────────────┐
│ universal_callback  │
│ (единый вход)       │
└────────┬────────────┘
         │
    ┌────┴────┬────────────┬────────────┐
    ▼         ▼            ▼            ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ shop   │ │alchemy │ │back    │ │unknown │
│ buy_*  │ │craft_* │ │to_game │ │fallback│
└────┬───┘ └────┬───┘ └────┬───┘ └────┬───┘
     │          │          │          │
     ▼          ▼          ▼          ▼
handle_   handle_    edit_message   answer() +
shop_     alchemy_   caption/text   "❌ Неизвестная"
callback  callback
```

---

## ⚙️ Сигнатура функции

```python
async def universal_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
```

| Параметр | Тип | Описание |
|----------|-----|----------|
| `update` | `Update` | Объект обновления от Telegram API, содержит `callback_query` |
| `context` | `ContextTypes.DEFAULT_TYPE` | Контекст выполнения: доступ к `bot_data`, `user_data`, `chat_data` |

---

## 🔄 Логика маршрутизации

Функция анализирует `update.callback_query.data` и выбирает действие:

### 1. 🛒 Покупки в магазине (`buy_*`)

```python
if data.startswith("buy_"):
    await handle_shop_callback(update, context)
```

- **Префикс:** `buy_`
- **Примеры данных:** `buy_potion_luck`, `buy_ring_power`, `buy_crown_mathmage`
- **Делегирует:** `handlers.shop.handle_shop_callback()`
- **Ответственность:** Проверка баланса, списание очков, выдача предмета, обновление инвентаря

### 2. ⚗️ Алхимия / крафт (`craft_*`)

```python
elif data.startswith("craft_"):
    await handle_alchemy_callback(update, context)
```

- **Префикс:** `craft_`
- **Примеры данных:** `craft_health_potion`, `craft_wisdom_elixir`
- **Делегирует:** `handlers.alchemy.handle_alchemy_callback()`
- **Ответственность:** Проверка ресурсов, запуск анимации крафта, выдача результата

### 3. 🔙 Возврат в игру (`back_to_game`)

```python
elif data == "back_to_game":
    query = update.callback_query
    try:
        if query.message.photo:
            await query.edit_message_caption("Возвращаюсь в игру...")
        else:
            await query.edit_message_text("Возвращаюсь в игру...")
    except Exception:
        # Игнорируем ошибку "Message is not modified"
        pass
```

- **Точное совпадение:** `back_to_game`
- **Поведение:**
  1. Проверяет, является ли сообщение фотографией (`query.message.photo`)
  2. Если да → редактирует `caption`, если нет → редактирует `text`
  3. Игнорирует `TelegramError: Message is not modified` (частая ситуация, если пользователь быстро нажимает)
- **Важно:** Не использует `answer()` — визуальный отклик даёт редактирование сообщения

### 4. ❌ Неизвестная команда (fallback)

```python
else:
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("❌ Неизвестная команда")
```

- **Условие:** `data` не совпал ни с одним известным префиксом
- **Поведение:**
  1. `answer()` — отправляет пустой «тик» клиенту (убирает индикатор загрузки)
  2. `edit_message_text()` — заменяет текст сообщения на ошибку
- **Потенциальная проблема:** Если сообщение содержит фото, `edit_message_text()` вызовет ошибку. Рекомендуется добавить проверку, как в ветке `back_to_game`.

---

## ⚠️ Важные замечания и улучшения

### 1. Обработка фото в fallback-ветке

Текущий код в `else` не проверяет наличие фото:

```python
# Сейчас (может вызвать ошибку):
await query.edit_message_text("❌ Неизвестная команда")

# Рекомендуется (как в back_to_game):
try:
    if query.message.photo:
        await query.edit_message_caption("❌ Неизвестная команда")
    else:
        await query.edit_message_text("❌ Неизвестная команда")
except TelegramError:
    pass  # Игнорируем "Message is not modified"
```

### 2. Логирование неизвестных команд

Для отладки полезно логировать неизвестные `data`:

```python
else:
    logger.warning(f"❌ Unknown callback: user_id={update.effective_user.id}, data={data}")
    await update.callback_query.answer()
    # ...далее редактирование сообщения
```

### 3. Расширяемость: добавление новых префиксов

Чтобы добавить новый модуль, достаточно:
1. Создать хендлер в отдельном файле (например, `handlers/inventory.py`)
2. Импортировать его в `universal_callback.py`
3. Добавить ветку `elif data.startswith("inv_"):`

Пример:
```python
from handlers.inventory import handle_inventory_callback

# ...внутри функции:
elif data.startswith("inv_"):
    await handle_inventory_callback(update, context)
```

### 4. Безопасность: валидация `user_id`

Если в будущем появится логика, зависящая от прав пользователя, рекомендуется добавить проверку в начале:

```python
user_id = update.effective_user.id
if user_id is None:
    await update.callback_query.answer("⚠️ Ошибка: пользователь не определён")
    return
```

---

## 🔗 Интеграция с другими модулями

```
manyunya_bot.py
       │
       ▼
app.add_handler(CallbackQueryHandler(universal_callback_handler))
       │
       ▼
universal_callback.py
       │
   ┌───┴───┬────────────┐
   ▼       ▼            ▼
shop.py  alchemy.py  (back_to_game)
   │       │            │
   ▼       ▼            ▼
ScoreManager  ArtifactManager  edit_message_*
```

---

## 🧪 Примеры данных `callback_query.data`

| Префикс | Пример `data` | Назначение |
|---------|--------------|------------|
| `buy_` | `buy_potion_luck` | Купить зелье удачи |
| `buy_` | `buy_ring_power_3` | Купить кольцо силы уровня 3 |
| `craft_` | `craft_wisdom_elixir` | Создать эликсир мудрости |
| `craft_` | `craft_chaos_shard` | Создать осколок хаоса |
| `back_to_game` | `back_to_game` | Вернуться из меню в игровой процесс |
| `unknown` | `debug_test_123` | Попадёт в fallback-ветку |

---

## 🛠 Тестирование

Для локальной проверки маршрутизации можно использовать `pytest` с моками:

```python
# tests/test_universal_callback.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from handlers.universal_callback import universal_callback_handler

@pytest.mark.asyncio
async def test_buy_prefix_routes_to_shop():
    # Мокаем update и context
    update = MagicMock()
    update.callback_query.data = "buy_potion_luck"
    update.callback_query.answer = AsyncMock()
    
    context = MagicMock()
    
    # Мокаем handle_shop_callback
    with patch("handlers.universal_callback.handle_shop_callback") as mock_shop:
        await universal_callback_handler(update, context)
        mock_shop.assert_called_once_with(update, context)
```

---

## 📝 Чеклист при добавлении новой кнопки

1. [ ] Выбрать уникальный префикс (например, `quest_`, `pet_`, `guild_`)
2. [ ] Создать обработчик в отдельном файле `handlers/<module>.py`
3. [ ] Импортировать обработчик в `universal_callback.py`
4. [ ] Добавить ветку `elif data.startswith("<prefix>_"):`
5. [ ] Протестировать: нажать кнопку → проверить, что вызван нужный хендлер
6. [ ] Добавить логирование для отладки (опционально)

---

*Документация актуальна для версии 4.7. Последнее обновление: `$(date)`*
```

---

## ✅ Что делать:

1. Создай файл `docs/BOT_CALLBACK_ROUTER.md` → вставь код выше → сохрани.

2. Закоммить:
   ```powershell
   git add docs/BOT_CALLBACK_ROUTER.md
   git commit -m "docs: add universal callback handler documentation"
   ```

---

## 🔄 Что дальше?

Следующие кандидаты на документацию (по приоритету):

1. `handlers/shop.py` — логика магазина: покупка, проверка баланса, выдача предметов
2. `handlers/alchemy.py` — система крафта: рецепты, ресурсы, анимация
3. `core/score_manager.py` — начисление очков, артефакты, бонусы

Пришли код любого из этих файлов — сделаю документацию в том же формате.

Работаем медленно, но правильно. Жду твой выбор.