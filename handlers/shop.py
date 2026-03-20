# handlers/shop.py
"""
Магазин Числяндии — покупка предметов и артефактов.
Версия: 5.0 (Shop Keeper Avatar + Vladimir Comments) 🛒🎩✅
"""

import asyncio
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from core.logger import log_user_action
from core.ui_helpers import get_persistent_keyboard
from items import SHOP_ITEMS, ARTIFACTS
from handlers.narrative_manager import PhraseManager, send_character_message

logger = logging.getLogger(__name__)
phrase_manager = PhraseManager()


async def show_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать магазин — с аватаркой Торговца!"""
    adapter = context.bot_data.get('adapter')
    if not adapter:
        await update.message.reply_text("⚠️ Ошибка: адаптер не инициализирован.")
        return
    
    raw_user_id = update.effective_user.id if update.effective_user else 0
    user_id = adapter.normalize_user_id(raw_user_id)
    
    log_user_action(user_id, "SHOP_OPEN")
    
    storage = context.bot_data.get('storage')
    if not storage:
        await adapter.send_message(user_id, "⚠️ Ошибка: хранилище не инициализировано.")
        return
    
    user_data = storage.get_user(user_id)
    balance = user_data.get("score_balance", 0)
    
    msg = "🛒 *ДОБРО ПОЖАЛОВАТЬ В МАГАЗИН!*\n\n"
    msg += f"💰 *Ваш баланс:* {balance:,} золотых\n\n"
    msg += "*Категории:*\n"
    msg += "🧪 Зелья и расходуемые предметы\n"
    msg += "⚡ Артефакты (прокачиваемые бонусы)\n\n"
    msg += "Выберите категорию:"
    
    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton("🧪 Зелья"), KeyboardButton("⚡ Артефакты")],
            [KeyboardButton("⬅️ Назад")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    
    # ✅ ОТПРАВЛЯЕМ С АВАТАРКОЙ ТОРГОВЦА!
    await send_character_message(
        update, context, "shop_keeper",
        "🛒 *ДОБРО ПОЖАЛОВАТЬ!*\n\n«Золото есть? Товар есть! Выбирай!»",
        mood="calm"
    )
    
    await adapter.send_message(
        user_id=user_id,
        text=msg,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


async def show_potions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать зелья"""
    adapter = context.bot_data.get('adapter')
    if not adapter:
        await update.message.reply_text("⚠️ Ошибка: адаптер не инициализирован.")
        return
    
    raw_user_id = update.effective_user.id if update.effective_user else 0
    user_id = adapter.normalize_user_id(raw_user_id)
    
    storage = context.bot_data.get('storage')
    user_data = storage.get_user(user_id)
    balance = user_data.get("score_balance", 0)
    
    msg = "🧪 *ЗЕЛЬЯ И РАСХОДУЕМЫЕ ПРЕДМЕТЫ*\n\n"
    
    for item_id, item in SHOP_ITEMS.items():
        if item.get("type") == "consumable":
            can_buy = "✅" if balance >= item.get("price", 0) else "❌"
            msg += f"{can_buy} {item['name']} — {item['price']} золотых\n"
    
    msg += "\n_Нажми на предмет для покупки_"
    
    rows = [[KeyboardButton(item["name"])] for item_id, item in SHOP_ITEMS.items() if item.get("type") == "consumable"]
    rows.append(["⬅️ Назад"])
    
    keyboard = ReplyKeyboardMarkup(rows, resize_keyboard=True)
    
    await adapter.send_message(
        user_id=user_id,
        text=msg,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


async def show_artifacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показать артефакты для покупки/улучшения.
    ✅ Цена рассчитывается автоматически на основе текущего уровня!
    """
    adapter = context.bot_data.get('adapter')
    if not adapter:
        await update.message.reply_text("⚠️ Ошибка: адаптер не инициализирован.")
        return
    
    raw_user_id = update.effective_user.id if update.effective_user else 0
    user_id = adapter.normalize_user_id(raw_user_id)
    
    storage = context.bot_data.get('storage')
    user_data = storage.get_user(user_id)
    balance = user_data.get("score_balance", 0)
    
    # Получаем текущие уровни артефактов
    artifact_upgrades = user_data.get("artifact_upgrades", {})
    
    msg = "🔮 *АРТЕФАКТЫ (ПРОКАЧИВАЕМЫЕ БОНУСЫ)*\n\n"
    msg += "Нажми на артефакт для покупки или улучшения!\n"
    msg += "Цена растёт с каждым уровнем.\n\n"
    
    for artifact_id, artifact in ARTIFACTS.items():
        current_level = artifact_upgrades.get(artifact_id, 0)
        
        # Рассчитываем цену следующего уровня
        if current_level == 0:
            price = artifact.get("base_price", 500)
            level_text = "❌ Не куплен"
        else:
            # Формула: base_price × multiplier^level
            price = int(artifact.get("base_price", 500) * (artifact.get("cost_multiplier", 1.4) ** current_level))
            level_text = f"✅ Уровень {current_level}"
        
        can_buy = "✅" if balance >= price else "❌"
        
        msg += f"{can_buy} {artifact['name']}\n"
        msg += f"   {level_text} | 💰 {price:,} золотых\n"
        msg += f"   _Эффект: {artifact['description']}_\n\n"
    
    msg += "💡 *Совет:* Улучшайте артефакты для увеличения бонусов!"
    
    rows = [[KeyboardButton(artifact["name"])] for artifact in ARTIFACTS.values()]
    rows.append(["⬅️ Назад"])
    
    keyboard = ReplyKeyboardMarkup(rows, resize_keyboard=True)
    
    await adapter.send_message(
        user_id=user_id,
        text=msg,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


async def buy_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Покупка предмета или улучшение артефакта.
    ✅ Артефакты: цена рассчитывается автоматически!
    ✅ Обычные предметы: через inventory
    ✅ Владимир комментирует покупки если замок открыт
    """
    adapter = context.bot_data.get('adapter')
    if not adapter:
        await update.message.reply_text("⚠️ Ошибка: адаптер не инициализирован.")
        return
    
    raw_text = update.message.text.strip() if update.message else "NO_TEXT"
    logger.info(f"🛒 buy_item вызван: text='{raw_text}'")
    
    raw_user_id = update.effective_user.id if update.effective_user else 0
    user_id = adapter.normalize_user_id(raw_user_id)
    
    item_name = update.message.text.strip()
    
    storage = context.bot_data.get('storage')
    user_data = storage.get_user(user_id)
    balance = user_data.get("score_balance", 0)
    
    item = None
    item_type = None
    
    # ✅ Ищем в обычных предметах (SHOP_ITEMS — это dict!)
    for item_id, item_data in SHOP_ITEMS.items():
        if item_data.get("name") == item_name:
            item = {"id": item_id, **item_data}
            item_type = "shop"
            break
    
    # ✅ Ищем в артефактах (ARTIFACTS — это dict)
    if not item:
        for artifact_id, artifact_data in ARTIFACTS.items():
            if artifact_data.get("name") == item_name:
                # Рассчитываем цену на основе текущего уровня!
                artifact_upgrades = user_data.get("artifact_upgrades", {})
                current_level = artifact_upgrades.get(artifact_id, 0)
                
                if current_level == 0:
                    price = artifact_data.get("base_price", 500)
                else:
                    # Формула: base_price × multiplier^level
                    price = int(artifact_data.get("base_price", 500) * (artifact_data.get("cost_multiplier", 1.4) ** current_level))
                
                item = {
                    "id": artifact_id,
                    "name": item_name,
                    "price": price,
                    "current_level": current_level
                }
                item_type = "artifact"
                break
    
    # ❌ Декорации больше не обрабатываются здесь — они в castle.py
    if not item:
        await adapter.send_message(user_id, "❌ Предмет не найден!\n\n💡 Декорации доступны в /castle → 🎨 Купить декорацию")
        return
    
    item_price = item.get("price", 0)
    if balance < item_price:
        await adapter.send_message(
            user_id,
            f"❌ Недостаточно золотых! Нужно {item_price:,}, есть {balance:,}"
        )
        return
    
    # ✅ ОБРАБОТКА АРТЕФАКТОВ — ЧЕРЕЗ upgrade_artifact()
    if item_type == "artifact":
        engine = context.bot_data.get('engine')
        if not engine:
            await adapter.send_message(user_id, "❌ Ошибка: ядро не инициализировано!")
            return
        
        # Вызываем upgrade_artifact (это и покупка, и улучшение)
        success, message = engine.upgrade_artifact(user_id, item["id"])
        
        if not success:
            await adapter.send_message(user_id, message)
            return
        
        # Обновляем user_data для отображения
        user_data = storage.get_user(user_id)
        
        # ✅ Владимир комментирует ТОЛЬКО если замок открыт
        if phrase_manager.is_castle_unlocked(user_data):
            new_level = item.get("current_level", 1)
            phrase = phrase_manager.get_vladimir_phrase(
                "artifact_upgraded",
                name=item["name"],
                level=new_level
            )
            phrase_clean = phrase.replace("🎩 ", "", 1)
            await send_character_message(
                update, context, "vladimir",
                f"{phrase_clean}\n\n✅ {item['name']} улучшен!\n💰 Списано: {item_price:,}",
                mood="approve"
            )
        else:
            await adapter.send_message(
                user_id,
                f"✅ *Покупка успешна!*\n\n"
                f"🔮 {item['name']}\n"
                f"💰 Списано: {item_price:,} золотых\n"
                f"💵 Остаток: {user_data['score_balance']:,}",
                parse_mode="Markdown"
            )
        
        log_user_action(user_id, "ARTIFACT_PURCHASED", f"artifact={item['id']}, price={item_price}")
        
        await asyncio.sleep(1)
        keyboard = get_persistent_keyboard(user_data, menu="main")
        await adapter.send_message(
            user_id,
            "Что делаем дальше?",
            reply_markup=keyboard
        )
        return
    
    # ✅ ОБРАБОТКА ОБЫЧНЫХ ПРЕДМЕТОВ — через inventory
    user_data["score_balance"] = balance - item_price
    
    if item_type == "shop":
        if "inventory" not in user_data:
            user_data["inventory"] = []
        user_data["inventory"].append(item["id"])
        storage.save_user(user_id, user_data)
    
    # ✅ Владимир комментирует ТОЛЬКО если замок открыт
    if phrase_manager.is_castle_unlocked(user_data):
        # Особые фразы для рискованных предметов
        if "Безум" in item["name"] or "Хаос" in item["name"]:
            phrase = "«Зелье Безумия?.. Я уже приготовил совок... и смирительную рубашку на ваш размер.»"
            mood = "relaxed"
        elif "Смел" in item["name"]:
            phrase = "«Зелье Смелости?.. Надеюсь, вы знаете что делаете, сударыня.»"
            mood = "approve"
        elif "Судьб" in item["name"]:
            phrase = "«Кубик Судьбы?.. Азарт — это интересно. Но помните: порядок не любит случайности.»"
            mood = "thinking"
        else:
            phrase = phrase_manager.get_vladimir_phrase("purchase_decoration").replace("🎩 ", "", 1)
            mood = "approve"
        
        await send_character_message(
            update, context, "vladimir",
            f"{phrase}\n\n✅ {item['name']} куплен!\n💰 Списано: {item_price:,}",
            mood=mood
        )
    else:
        await adapter.send_message(
            user_id,
            f"✅ *Покупка успешна!*\n\n"
            f"🛒 {item['name']}\n"
            f"💰 Списано: {item_price:,} золотых\n"
            f"💵 Остаток: {user_data['score_balance']:,}",
            parse_mode="Markdown"
        )
    
    log_user_action(user_id, "ITEM_PURCHASED", f"item={item['name']}, price={item_price}")
    
    await asyncio.sleep(1)
    keyboard = get_persistent_keyboard(user_data, menu="main")
    await adapter.send_message(
        user_id,
        "Что делаем дальше?",
        reply_markup=keyboard
    )


async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вернуться в главное меню"""
    adapter = context.bot_data.get('adapter')
    if not adapter:
        await update.message.reply_text("⚠️ Ошибка: адаптер не инициализирован.")
        return
    
    raw_user_id = update.effective_user.id if update.effective_user else 0
    user_id = adapter.normalize_user_id(raw_user_id)
    
    storage = context.bot_data.get('storage')
    user_data = storage.get_user(user_id) if storage else {}
    
    keyboard = get_persistent_keyboard(user_data, menu="main")
    
    await adapter.send_message(
        user_id,
        "🏰 *ГЛАВНОЕ МЕНЮ*\n\nВыберите действие:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


async def handle_shop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка callback-кнопок магазина (для inline-кнопок)"""
    query = update.callback_query
    if not query:
        return
    
    await query.answer()
    
    data = query.data
    user_id = str(query.from_user.id)
    
    logger.info(f"🛒 Shop callback: {data}")
    
    parts = data.split("|")
    item_data = {}
    for part in parts:
        if ":" in part:
            key, _, value = part.partition(":")
            item_data[key] = value
    
    item_id = item_data.get("id", "")
    qty = int(item_data.get("qty", 1))
    
    item = None
    for iid, i in SHOP_ITEMS.items():
        if iid == item_id:
            item = i
            break
    
    if not item:
        await query.edit_message_text("❌ Предмет не найден!")
        return
    
    storage = context.bot_data.get('storage')
    user_data = storage.get_user(user_id)
    balance = user_data.get("score_balance", 0)
    
    item_price = item.get("price", 0)
    if balance < item_price * qty:
        await query.edit_message_text(
            f"❌ Недостаточно золотых! Нужно {item_price * qty:,}, есть {balance:,}"
        )
        return
    
    user_data["score_balance"] = balance - (item_price * qty)
    if "inventory" not in user_data:
        user_data["inventory"] = []
    user_data["inventory"].append(item_id)
    storage.save_user(user_id, user_data)
    
    await query.edit_message_text(
        f"✅ *Покупка успешна!*\n\n"
        f"🛒 {item.get('name', item_id)} x{qty}\n"
        f"💰 Списано: {item_price * qty:,} золотых",
        parse_mode="Markdown"
    )
    
    log_user_action(user_id, "ITEM_PURCHASED_CALLBACK", f"item={item.get('name', item_id)}, qty={qty}")


def get_shop_handlers():
    """Возвращает список хендлеров магазина"""
    return [
        CommandHandler("shop", show_shop),
        MessageHandler(filters.Text("🧪 Зелья") & ~filters.COMMAND, show_potions),
        MessageHandler(filters.Text("⚡ Артефакты") & ~filters.COMMAND, show_artifacts),
        MessageHandler(filters.Text("⬅️ Назад") & ~filters.COMMAND, back_to_menu),
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & 
            (filters.Text("🧪 Зелье Здоровья") | filters.Text("🧪 Зелье Мудрости") |
             filters.Text("🍀 Артефакт Удачи") | filters.Text("⚡ Артефакт Силы") |
             filters.Text("🧠 Артефакт Мудрости")),
            buy_item
        ),
    ]