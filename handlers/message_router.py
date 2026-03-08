# handlers/message_router.py
"""
Обработчик всех входящих сообщений.
Версия: 2.6 (Кнопка Помощь + 3 уровня + Игровая клавиатура) 🎮❓🏝️
"""

import asyncio
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from handlers.utils import send_character_message
from core.logger import log_user_action, log_error

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает все входящие сообщения"""
    try:
        text = update.message.text.strip()
        user_id = update.effective_user.id if update.effective_user else 0
        first_name = update.effective_user.first_name if update.effective_user else "Unknown"
        
        log_user_action(user_id, "MESSAGE", f"text='{text}' | name='{first_name}'")
        
        storage = context.bot_data.get('storage')
        if not storage:
            await update.message.reply_text("⚠️ Ошибка: хранилище данных не инициализировано.")
            return False
        
        user_data = storage.get_user(user_id) or {}
        text_lower = text.lower()
        
        # === УНИВЕРСАЛЬНАЯ ОБРАБОТКА ВЫХОДА ===
        if text_lower in ["назад", "выйти", "выход", "назад в игру", "⬅️ назад"]:
            if user_data.get("in_boss_battle"):
                user_data.update({
                    "in_boss_battle": False,
                    "current_boss": None,
                    "selected_boss_tasks": [],
                    "boss_task_index": 0,
                    "boss_health": 5,
                    "boss_abilities_used": [],
                    "boss_turn": 0
                })
                storage.save_user(user_id, user_data)
                from core.ui_helpers import get_persistent_keyboard
                await update.message.reply_text("↩️ Вышла из боя!", reply_markup=get_persistent_keyboard(user_data))
                return True
                
            elif user_data.get("current_level"):
                user_data.update({
                    "current_level": None,
                    "selected_tasks": [],
                    "current_task_index": 0,
                    "mistakes_in_level": 0
                })
                storage.save_user(user_id, user_data)
                from core.ui_helpers import get_persistent_keyboard
                await update.message.reply_text("↩️ Вышла из уровня!", reply_markup=get_persistent_keyboard(user_data))
                return True
            
            else:
                from core.ui_helpers import get_persistent_keyboard
                await update.message.reply_text("↩️ Возвращаюсь в меню", reply_markup=get_persistent_keyboard(user_data))
                return True

        # === ОБРАБОТКА БОЯ ===
        if user_data.get("in_boss_battle"):
            from handlers.bosses import handle_boss_answer
            boss_handled = await handle_boss_answer(update, context)
            return True

        # === ОБРАБОТКА УРОВНЯ ===
        if user_data.get("current_level"):
            from handlers.levels import handle_level_answer
            level_handled = await handle_level_answer(update, context)
            return True

        # === ✅ УРОВЕНЬ 1: КНОПКА «ИГРАТЬ» ===
        if text_lower in ["🎮 играть", "играть", "начать игру", "игра"]:
            keyboard = ReplyKeyboardMarkup([
                [KeyboardButton("🏝️ Острова"), KeyboardButton("⚔️ Боссы")],
                [KeyboardButton("🗺️ Миры"), KeyboardButton("⬅️ Назад")],
            ], resize_keyboard=True, one_time_keyboard=False)
            
            await update.message.reply_text(
                "🎮 <b>Выбери, куда хочешь отправиться:</b>\n\n"
                "🏝️ <b>Острова</b> — решай задачки\n"
                "⚔️ <b>Боссы</b> — сражайся с злодеями\n"
                "🗺️ <b>Миры</b> — исследуй новое",
                parse_mode="HTML",
                reply_markup=keyboard
            )
            return True

        # === ✅ УРОВЕНЬ 2: КНОПКИ ИЗ МЕНЮ «ИГРАТЬ» ===
        
        # 🏝️ ОСТРОВА
        if text_lower in ["🏝️ острова", "острова", "остров", "выбрать остров"]:
            keyboard = ReplyKeyboardMarkup([
                [KeyboardButton("➕ Сложение"), KeyboardButton("➖ Вычитание")],
                [KeyboardButton("✖️ Умножение"), KeyboardButton("➗ Деление")],
                [KeyboardButton("⬅️ Назад")],
            ], resize_keyboard=True, one_time_keyboard=False)
            
            await update.message.reply_text(
                "🏝️ <b>ВЫБЕРИ ОСТРОВ:</b>\n\n"
                "➕ Сложение\n"
                "➖ Вычитание\n"
                "✖️ Умножение\n"
                "➗ Деление",
                parse_mode="HTML",
                reply_markup=keyboard
            )
            return True

        # ⚔️ БОССЫ
        if text_lower in ["⚔️ боссы", "боссы", "бой с боссом", "выбрать босса"]:
            keyboard = ReplyKeyboardMarkup([
                [KeyboardButton("🌑 Нуль-Пустота"), KeyboardButton("🌑 Минус-Тень")],
                [KeyboardButton("🌀 Злой Умножитель"), KeyboardButton("🌊 Дробозавр")],
                [KeyboardButton("👑 Финальный Владыка"), KeyboardButton("⬅️ Назад")],
            ], resize_keyboard=True, one_time_keyboard=False)
            
            await update.message.reply_text(
                "⚔️ <b>ВЫБЕРИ БОССА:</b>\n\n"
                "🌑 Нуль-Пустота\n"
                "🌑 Минус-Тень\n"
                "🌀 Злой Умножитель\n"
                "🌊 Дробозавр\n"
                "👑 Финальный Владыка",
                parse_mode="HTML",
                reply_markup=keyboard
            )
            return True

        # 🗺️ МИРЫ
        if text_lower in ["🗺️ миры", "миры", "выбрать мир"]:
            keyboard = ReplyKeyboardMarkup([
                [KeyboardButton("🕒 Хронопия"), KeyboardButton("📏 Мир Мер")],
                [KeyboardButton("🧠 Мир Логики"), KeyboardButton("⬅️ Назад")],
            ], resize_keyboard=True, one_time_keyboard=False)
            
            await update.message.reply_text(
                "🗺️ <b>ВЫБЕРИ МИР:</b>\n\n"
                "🕒 Хронопия\n"
                "📏 Мир Мер\n"
                "🧠 Мир Логики",
                parse_mode="HTML",
                reply_markup=keyboard
            )
            return True

        # === ✅ УРОВЕНЬ 3: ЗАПУСК УРОВНЕЙ (ОСТРОВА) ===
        
        # ➕ СЛОЖЕНИЕ
        if text_lower in ["➕ сложение", "сложение", "остров сложения"]:
            from handlers.levels import enter_level
            await enter_level(update, context, "addition")
            log_user_action(user_id, "ENTER_LEVEL", "level=addition")
            return True

        # ➖ ВЫЧИТАНИЕ
        if text_lower in ["➖ вычитание", "вычитание", "пещера вычитания"]:
            from handlers.levels import enter_level
            await enter_level(update, context, "subtraction")
            log_user_action(user_id, "ENTER_LEVEL", "level=subtraction")
            return True

        # ✖️ УМНОЖЕНИЕ
        if text_lower in ["✖️ умножение", "умножение", "лес умножения"]:
            from handlers.levels import enter_level
            await enter_level(update, context, "multiplication")
            log_user_action(user_id, "ENTER_LEVEL", "level=multiplication")
            return True

        # ➗ ДЕЛЕНИЕ
        if text_lower in ["➗ деление", "деление", "река деления"]:
            from handlers.levels import enter_level
            await enter_level(update, context, "division")
            log_user_action(user_id, "ENTER_LEVEL", "level=division")
            return True

        # === ✅ УРОВЕНЬ 3: ЗАПУСК БОССОВ ===
        
        boss_map = {
            "🌑 нуль-пустота": "null_void",
            "🌑 минус-тень": "minus_shadow",
            "🌀 злой умножитель": "evil_multiplier",
            "🌊 дробозавр": "fracosaur",
            "👑 финальный владыка": "final_boss",
            "👑 владыка": "final_boss",
            "владыка": "final_boss",
        }
        
        for boss_text, boss_id in boss_map.items():
            if boss_text in text_lower or boss_id.replace("_", " ") in text_lower:
                from handlers.bosses import start_boss_battle
                await start_boss_battle(update, context, boss_id)
                log_user_action(user_id, "START_BOSS", f"boss={boss_id}")
                return True

        # === ✅ УРОВЕНЬ 3: ЗАПУСК МИРОВ ===
        
        world_map = {
            "🕒 хронопия": "time_world",
            "📏 мир мер": "measure_world",
            "🧠 мир логики": "logic_world",
        }
        
        for world_text, world_id in world_map.items():
            if world_text in text_lower or world_id.replace("_", " ") in text_lower:
                from handlers.levels import enter_level
                await enter_level(update, context, world_id)
                log_user_action(user_id, "ENTER_LEVEL", f"level={world_id}")
                return True

        # === ✅ ОБРАБОТКА КНОПОК БАНКА (ЗЛАТОЧЁТ) ===
        if text_lower in ["🏦 златочёт", "златочёт", "банк", "🏦 банк"]:
            from handlers.bank import show_bank
            await show_bank(update, context)
            return True
        
        if text_lower in ["💰 положить 100", "положить 100"]:
            from handlers.bank import bank_deposit_100
            await bank_deposit_100(update, context)
            return True
        
        if text_lower in ["💰 положить 500", "положить 500"]:
            from handlers.bank import bank_deposit_500
            await bank_deposit_500(update, context)
            return True
        
        if text_lower in ["💰 положить 1000", "положить 1000"]:
            from handlers.bank import bank_deposit_1000
            await bank_deposit_1000(update, context)
            return True
        
        if text_lower in ["💰 другая сумма", "другая сумма"]:
            from handlers.bank import bank_deposit_custom
            await bank_deposit_custom(update, context)
            return True
        
        if text_lower in ["💸 забрать всё", "забрать всё", "забрать вклад"]:
            from handlers.bank import bank_withdraw_all
            await bank_withdraw_all(update, context)
            return True

        # === ✅ ОБРАБОТКА КНОПОК ЗАМКА ===
        if text_lower in ["🏰 замок", "замок", "🏰 мой замок", "мой замок"]:
            from handlers.castle import show_castle
            await show_castle(update, context)
            return True
        
        if text_lower in ["💰 оплатить 1 день", "оплатить 1 день"]:
            from handlers.castle import castle_pay_1_day
            await castle_pay_1_day(update, context)
            return True
        
        if text_lower in ["💰 оплатить 7 дней", "оплатить 7 дней"]:
            from handlers.castle import castle_pay_7_days
            await castle_pay_7_days(update, context)
            return True
        
        if text_lower in ["💰 оплатить 30 дней", "оплатить 30 дней"]:
            from handlers.castle import castle_pay_30_days
            await castle_pay_30_days(update, context)
            return True

        # === ОБРАБОТКА КНОПОК ПРОФИЛЯ ===
        if text_lower in ["🏆 достижения", "достижения", "🏅 достижения"]:
            from handlers.profile import show_achievements
            await show_achievements(update, context)
            return True
        
        if text_lower in ["👤 профиль", "профиль", "📊 прогресс", "прогресс"]:
            from handlers.profile import show_profile_and_rewards
            await show_profile_and_rewards(update, context)
            return True
        
        if text_lower in ["🎒 инвентарь", "инвентарь", "🎒 рюкзак", "рюкзак", "предметы"]:
            from handlers.profile import show_inventory
            await show_inventory(update, context)
            return True

        # === ✅ ОБРАБОТКА КНОПКИ «ПОМОЩЬ» ===
        if text_lower in ["❓ помощь", "помощь", "help", "справка"]:
            help_text = (
                "📚 <b>СПРАВКА ПО ЧИСЛЯНДИИ</b>\n\n"
                "🎮 <b>Игровые команды:</b>\n"
                "  /start — Главное меню\n"
                "  /reset — Сбросить уровень (если застрял)\n\n"
                "🏦 <b>Златочёт (Банк):</b>\n"
                "  💰 Положить 100/500/1000 — Вклад в банк\n"
                "  💸 Забрать всё — Снять вклад с процентами\n"
                "  Ставка: 10% в день!\n\n"
                "🏰 <b>Замок:</b>\n"
                "  💰 Оплатить 1/7/30 дней — Upkeep замка\n"
                "  Бонус: +5% к очкам за декорацию!\n\n"
                "💡 <b>Советы:</b>\n"
                "  • Решай задачи → получай золотые\n"
                "  • Копи в Златочёте → расти проценты\n"
                "  • Укрась Замок → получай бонусы\n"
                "  • ⬅️ Назад — выход из уровня/боя"
            )
            await update.message.reply_text(help_text, parse_mode="HTML")
            return True

        # === ОСТАЛЬНЫЕ КОМАНДЫ ===
        btn = text_lower
        
        if btn in ("🛒 магазин", "магаз"):
            from handlers.shop import show_shop
            await show_shop(update, context)
            return True

        if btn in ("⚗️ алхимия", "алхим"):
            from handlers.alchemy import show_alchemy
            await show_alchemy(update, context)
            return True

        if btn in ("⚙️ мастерская", "мастерская"):
            from core.ui_helpers import get_persistent_keyboard
            await update.message.reply_text(
                "Выбери действие:",
                reply_markup=get_persistent_keyboard(user_data, menu="workshop")
            )
            return True

        # === КЛЮЧЕВЫЕ СЛОВА (ОСТРОВА) ===
        ISLAND_KEYWORDS = {
            "остров сложения": "addition",
            "пещера вычитания": "subtraction", 
            "лес умножения": "multiplication",
            "река деления": "division",
            "хронопия": "time_world",
            "мир мер": "measure_world",
            "мир логики": "logic_world"
        }
        
        for keyword, level_id in ISLAND_KEYWORDS.items():
            if keyword in text_lower:
                from handlers.levels import enter_level
                await enter_level(update, context, level_id)
                log_user_action(user_id, "ENTER_LEVEL", f"level={level_id}")
                return True

        # === КЛЮЧЕВЫЕ СЛОВА (БОССЫ) ===
        BOSS_KEYWORDS = {
            "нуль-пустота": "null_void",
            "минус-тень": "minus_shadow",
            "злой умножитель": "evil_multiplier",
            "дробозавр": "fracosaur",
            "владыка числяндии": "final_boss",
            "владыка": "final_boss",
        }
        
        for keyword, boss_id in BOSS_KEYWORDS.items():
            if keyword in text_lower:
                from handlers.bosses import start_boss_battle
                await start_boss_battle(update, context, boss_id)
                log_user_action(user_id, "START_BOSS", f"boss={boss_id}")
                return True
        
        # Неизвестная команда
        await update.message.reply_text(
            "Не понимаю эту команду. Выбери действие из меню!\n"
            "💡 Напиши *назад* чтобы выйти из боя/уровня",
            parse_mode="Markdown"
        )
        return False
    
    except Exception as e:
        user_id = update.effective_user.id if update.effective_user else 0
        log_error(user_id, str(e), exc_info=True)
        
        await update.message.reply_text(
            "⚠️ Ой! Что-то пошло не так. Попробуй снова или напиши /start"
        )
        return True