# handlers/message_router.py
"""
Обработчик всех входящих сообщений.
Версия: 3.5 (Fix: Remove duplicate get_user + Debug new users) 🎮✅
"""

import asyncio
import logging
import time
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from handlers.utils import send_character_message
from core.logger import log_user_action, log_error
from config import (
    SPAM_MIN_INTERVAL_SEC as CFG_SPAM_MIN_INTERVAL_SEC,
    SPAM_DUPLICATE_WINDOW_SEC as CFG_SPAM_DUPLICATE_WINDOW_SEC,
    SPAM_WARN_INTERVAL_SEC as CFG_SPAM_WARN_INTERVAL_SEC,
)

logger = logging.getLogger(__name__)

# === АНТИСПАМ НАСТРОЙКИ ===
# Минимальный интервал между сообщениями от одного пользователя.
MIN_MESSAGE_INTERVAL_SEC = CFG_SPAM_MIN_INTERVAL_SEC
# Окно, в котором одинаковый текст считается дубликатом.
DUPLICATE_WINDOW_SEC = CFG_SPAM_DUPLICATE_WINDOW_SEC
# Минимальный интервал между предупреждениями о спаме.
SPAM_WARN_INTERVAL_SEC = CFG_SPAM_WARN_INTERVAL_SEC


def _normalize_text(text: str) -> str:
    """
    Нормализует текст для надёжного сравнения:
    - Удаляет лишние пробелы
    - Приводит к нижнему регистру
    - Удаляет невидимые символы
    """
    if not text:
        return ""
    # Удаляем невидимые символы и лишние пробелы
    cleaned = ''.join(c for c in text if c.isprintable()).strip()
    return cleaned.lower()


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает все входящие сообщения.
    ✅ ГИБКОЕ СРАВНЕНИЕ КНОПОК + ДЕБАГ-ЛОГИ + ФИКС ПРИОРИТЕТА ОТВЕТОВ
    """
    try:
        if not update.message or not update.message.text:
            logger.debug(f"⚠️ Пустое сообщение от user_id={update.effective_user.id if update.effective_user else 'unknown'}")
            return False
        
        raw_text = update.message.text.strip()
        text = _normalize_text(raw_text)
        user_id = update.effective_user.id if update.effective_user else 0
        first_name = update.effective_user.first_name if update.effective_user else "Unknown"
        
        logger.debug(f"📨 Получено: raw='{raw_text}' | normalized='{text}' | user={first_name}")
        
        log_user_action(user_id, "MESSAGE", f"text_len={len(raw_text)}")

        # === ✅ АНТИСПАМ: защита от флуда и дубликатов ===
        now = time.monotonic()
        anti_spam = context.bot_data.setdefault("_anti_spam", {})
        state = anti_spam.get(user_id, {
            "last_ts": 0.0,
            "last_text": "",
            "last_warn_ts": 0.0,
        })

        is_too_fast = (now - state["last_ts"]) < MIN_MESSAGE_INTERVAL_SEC
        is_duplicate = (
            text
            and text == state["last_text"]
            and (now - state["last_ts"]) < DUPLICATE_WINDOW_SEC
        )

        if is_too_fast or is_duplicate:
            # Обновляем таймстамп, чтобы удерживать флудера в окне.
            state["last_ts"] = now
            anti_spam[user_id] = state

            if (now - state["last_warn_ts"]) >= SPAM_WARN_INTERVAL_SEC:
                state["last_warn_ts"] = now
                anti_spam[user_id] = state
                await update.message.reply_text("⏳ Чуть медленнее, пожалуйста.")
            return True

        state["last_ts"] = now
        state["last_text"] = text
        anti_spam[user_id] = state
        
        # === ✅ ЭКСТРЕННЫЙ ВЫХОД: ГИБКОЕ СРАВНЕНИЕ ===
        exit_keywords = ["назад", "выйти", "выход", "меню", "back", "exit", "⬅️"]
        if any(kw in text for kw in exit_keywords):
            logger.info(f"🚨 EMERGENCY EXIT: '{raw_text}' от user_id={user_id}")
            
            storage = context.bot_data.get('storage')
            if storage:
                user_data = storage.get_user(user_id) or {}
                if user_data.get("current_level") or user_data.get("in_boss_battle"):
                    user_data.update({
                        "current_level": None, "selected_tasks": [], "current_task_index": 0,
                        "mistakes_in_level": 0, "in_boss_battle": False, "current_boss": None,
                        "selected_boss_tasks": [], "boss_task_index": 0, "boss_health": 5,
                        "boss_abilities_used": [], "boss_turn": 0
                    })
                    storage.save_user(user_id, user_data)
                    logger.info(f"✅ Emergency exit: сброшены флаги для user_id={user_id}")
            
            adapter = context.bot_data.get('adapter')
            if adapter:
                from core.ui_helpers import get_persistent_keyboard
                storage = context.bot_data.get('storage')
                user_data = storage.get_user(user_id) if storage else {}
                keyboard = get_persistent_keyboard(user_data, menu="main")
                await update.message.reply_text(
                    f"↩️ **Экстренный выход!**\n\n🏰 **ГЛАВНОЕ МЕНЮ**",
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
            return True
        
        storage = context.bot_data.get('storage')
        if not storage:
            await update.message.reply_text("⚠️ Ошибка: хранилище данных не инициализировано.")
            return False
        
        # ✅ ЗАГРУЖАЕМ ДАННЫЕ ПОЛЬЗОВАТЕЛЯ ОДИН РАЗ В НАЧАЛЕ
        user_data = storage.get_user(user_id) or {}
        
        # === 🔥 ПРИОРИТЕТ 1: ОБРАБОТКА БОЯ (если в бою — только ответы) ===
        if user_data.get("in_boss_battle"):
            logger.debug(f"⚔️ В бою: обрабатываем через handle_boss_answer")
            from handlers.bosses import handle_boss_answer
            boss_handled = await handle_boss_answer(update, context)
            if boss_handled:
                return True
            # Если False — продолжаем (на случай ошибки в обработчике)
            logger.warning(f"⚠️ handle_boss_answer вернул False для user_id={user_id}")

        # === 🔥 ПРИОРИТЕТ 2: ОБРАБОТКА УРОВНЯ (если в уровне — только ответы) ===
        # ✅ ФИКС: убрали дублирующий storage.get_user() — используем user_data из начала функции
        # ✅ ФИКС: добавили дебаг-лог для отладки новых пользователей
        if user_data.get("current_level"):
            logger.debug(f"🎮 Level check: current_level='{user_data['current_level']}', user_id={user_id}, keys={list(user_data.keys())[:8]}")
            from handlers.levels import handle_level_answer
            level_handled = await handle_level_answer(update, context)
            if level_handled:
                return True
            # Если False — продолжаем
            logger.warning(f"⚠️ handle_level_answer вернул False для user_id={user_id}")
        else:
            # 🔥 DEBUG: если не в уровне, но пользователь только что вошёл — логируем состояние
            logger.debug(f"🔍 DEBUG: NOT in level. current_level={user_data.get('current_level')}, in_boss={user_data.get('in_boss_battle')}, unlocked={user_data.get('unlocked_zones')}")

        # === 🔥 ПРИОРИТЕТ 2.5: ОБРАБОТКА ТАЙНОЙ КОМНАТЫ ===
        if user_data.get("in_secret_level"):
            logger.debug(f"🔐 В тайной комнате: обрабатываем ответ")
            from handlers.secret_room import handle_secret_answer
            secret_handled = await handle_secret_answer(update, context)
            if secret_handled:
                return True
            logger.warning(f"⚠️ handle_secret_answer вернул False для user_id={user_id}")

        # === ✅ ОБРАБОТКА КОМАНД МЕНЮ (только если НЕ в игре) ===
        
        # 🎮 Играть
        if "играть" in text or "начать" in text or text in ["игра", "🎮"]:
            logger.info(f"🎮 Запуск игры: user_id={user_id}")
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

        # 🏝️ Острова
        if "остров" in text or text in ["🏝️"]:
            logger.info(f"🏝️ Выбор острова: user_id={user_id}")
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

        # ⚔️ Боссы
        if "босс" in text or text in ["⚔️", "бой"]:
            logger.info(f"⚔️ Выбор босса: user_id={user_id}")
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

        # 🗺️ Миры
        if "мир" in text or text in ["🗺️"]:
            logger.info(f"🗺️ Выбор мира: user_id={user_id}")
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

        # === ✅ ЗАПУСК УРОВНЕЙ (ОСТРОВА) — ТОЛЬКО ЕСЛИ НЕ В УРОВНЕ ===
        if not user_data.get("current_level"):
            if "слож" in text or "addition" in text:
                logger.info(f"➕ Запуск уровня: addition, user_id={user_id}")
                from handlers.levels import enter_level
                await enter_level(update, context, "addition")
                log_user_action(user_id, "ENTER_LEVEL", "level=addition")
                return True

            if "вычит" in text or "subtraction" in text:
                logger.info(f"➖ Запуск уровня: subtraction, user_id={user_id}")
                from handlers.levels import enter_level
                await enter_level(update, context, "subtraction")
                log_user_action(user_id, "ENTER_LEVEL", "level=subtraction")
                return True

            if "умнож" in text or "multiplication" in text:
                logger.info(f"✖️ Запуск уровня: multiplication, user_id={user_id}")
                from handlers.levels import enter_level
                await enter_level(update, context, "multiplication")
                log_user_action(user_id, "ENTER_LEVEL", "level=multiplication")
                return True

            if "делен" in text or "division" in text:
                logger.info(f"➗ Запуск уровня: division, user_id={user_id}")
                from handlers.levels import enter_level
                await enter_level(update, context, "division")
                log_user_action(user_id, "ENTER_LEVEL", "level=division")
                return True

        # === ✅ ЗАПУСК БОССОВ — ТОЛЬКО ЕСЛИ НЕ В БОЮ ===
        if not user_data.get("in_boss_battle"):
            boss_map = {
                "нуль": "null_void", "пустот": "null_void",
                "минус": "minus_shadow", "тен": "minus_shadow",
                "умножител": "evil_multiplier", "злой": "evil_multiplier",
                "дробозавр": "fracosaur", "дроб": "fracosaur",
                "владык": "final_boss", "финальн": "final_boss",
            }
            
            for keyword, boss_id in boss_map.items():
                if keyword in text:
                    logger.info(f"👑 Запуск босса: {boss_id}, user_id={user_id}")
                    from handlers.bosses import start_boss_battle
                    await start_boss_battle(update, context, boss_id)
                    log_user_action(user_id, "START_BOSS", f"boss={boss_id}")
                    return True

        # === ✅ ЗАПУСК МИРОВ — ТОЛЬКО ЕСЛИ НЕ В УРОВНЕ ===
        if not user_data.get("current_level"):
            world_map = {
                "хроноп": "time_world", "врем": "time_world",
                "мер": "measure_world", "измер": "measure_world",
                "логик": "logic_world", "разум": "logic_world",
            }
            
            for keyword, world_id in world_map.items():
                if keyword in text:
                    logger.info(f"🌍 Запуск мира: {world_id}, user_id={user_id}")
                    from handlers.levels import enter_level
                    await enter_level(update, context, world_id)
                    log_user_action(user_id, "ENTER_LEVEL", f"level={world_id}")
                    return True

        # === ✅ ОБРАБОТКА КНОПОК БАНКА (ЗЛАТОЧЁТ) ===
        if "златочёт" in text or "банк" in text or "🏦" in raw_text:
            logger.info(f"🏦 Открытие банка: user_id={user_id}")
            from handlers.bank import show_bank
            await show_bank(update, context)
            return True
        
        if "положить 100" in text or ("100" in text and "полож" in text):
            from handlers.bank import bank_deposit_100
            await bank_deposit_100(update, context)
            return True
        
        if "положить 500" in text or ("500" in text and "полож" in text):
            from handlers.bank import bank_deposit_500
            await bank_deposit_500(update, context)
            return True
        
        if "положить 1000" in text or ("1000" in text and "полож" in text):
            from handlers.bank import bank_deposit_1000
            await bank_deposit_1000(update, context)
            return True
        
        if "другая сумма" in text or ("сумма" in text and "полож" in text):
            from handlers.bank import bank_deposit_custom
            await bank_deposit_custom(update, context)
            return True
        
        if ("забрать" in text and "всё" in text) or "забрать вклад" in text:
            from handlers.bank import bank_withdraw_all
            await bank_withdraw_all(update, context)
            return True

        # === ✅ ОБРАБОТКА КНОПОК ЗАМКА ===
        if "замок" in text or "🏰" in raw_text:
            logger.info(f"🏰 Открытие замка: user_id={user_id}")
            from handlers.castle import show_castle
            await show_castle(update, context)
            return True
        
        if "оплатить" in text and "1 день" in text:
            from handlers.castle import castle_pay_1_day
            await castle_pay_1_day(update, context)
            return True
        
        if "оплатить" in text and "7 дней" in text:
            from handlers.castle import castle_pay_7_days
            await castle_pay_7_days(update, context)
            return True
        
        if "оплатить" in text and "30 дней" in text:
            from handlers.castle import castle_pay_30_days
            await castle_pay_30_days(update, context)
            return True

        # === ОБРАБОТКА КНОПОК ПРОФИЛЯ ===
        if "достиж" in text or "🏆" in raw_text:
            from handlers.profile import show_achievements
            await show_achievements(update, context)
            return True
        
        if "профил" in text or "прогресс" in text or "👤" in raw_text:
            from handlers.profile import show_profile_and_rewards
            await show_profile_and_rewards(update, context)
            return True
        
        if "инвентар" in text or "рюкзак" in text or "🎒" in raw_text:
            from handlers.profile import show_inventory
            await show_inventory(update, context)
            return True

        # === ✅ ОБРАБОТКА КНОПКИ «ПОМОЩЬ» ===
        if "помощ" in text or "help" in text or "справк" in text or "❓" in raw_text:
            help_text = (
                "📚 <b>СПРАВКА ПО ЧИСЛЯНДИИ</b>\n\n"
                "🎮 <b>Игровые команды:</b>\n"
                "  /start — Главное меню\n"
                "  /back — Выйти из уровня/боя\n"
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
        
        if "магазин" in text or "🛒" in raw_text:
            logger.info(f"🛒 Открытие магазина: user_id={user_id}")
            from handlers.shop import show_shop
            await show_shop(update, context)
            return True

        if "алхим" in text or "⚗️" in raw_text:
            logger.info(f"⚗️ Открытие алхимии: user_id={user_id}")
            from handlers.alchemy import show_alchemy
            await show_alchemy(update, context)
            return True

        if "мастерск" in text or "⚙️" in raw_text:
            from core.ui_helpers import get_persistent_keyboard
            await update.message.reply_text(
                "Выбери действие:",
                reply_markup=get_persistent_keyboard(user_data, menu="workshop")
            )
            return True

        # === КЛЮЧЕВЫЕ СЛОВА (ОСТРОВА) — ДОПОЛНИТЕЛЬНЫЕ ===
        island_keywords = {
            "слож": "addition", "плюс": "addition", "+": "addition",
            "вычит": "subtraction", "минус": "subtraction", "-": "subtraction",
            "умнож": "multiplication", "умно": "multiplication", "*": "multiplication", "x": "multiplication",
            "делен": "division", "делить": "division", "/": "division", "÷": "division",
            "хроноп": "time_world", "врем": "time_world", "час": "time_world",
            "мер": "measure_world", "измер": "measure_world", "метр": "measure_world",
            "логик": "logic_world", "разум": "logic_world", "мысл": "logic_world",
        }
        
        for keyword, level_id in island_keywords.items():
            if keyword in text and not user_data.get("current_level"):
                logger.info(f"🏝️ Запуск уровня по ключевому слову: {level_id}, user_id={user_id}")
                from handlers.levels import enter_level
                await enter_level(update, context, level_id)
                log_user_action(user_id, "ENTER_LEVEL", f"level={level_id}")
                return True

        # === КЛЮЧЕВЫЕ СЛОВА (БОССЫ) — ДОПОЛНИТЕЛЬНЫЕ ===
        boss_keywords = {
            "нуль": "null_void", "пустот": "null_void", "0": "null_void",
            "минус": "minus_shadow", "тен": "minus_shadow", "тень": "minus_shadow",
            "умножител": "evil_multiplier", "злой": "evil_multiplier",
            "дробозавр": "fracosaur", "дроб": "fracosaur", "ящер": "fracosaur",
            "владык": "final_boss", "финальн": "final_boss", "корона": "final_boss",
        }
        
        for keyword, boss_id in boss_keywords.items():
            if keyword in text and not user_data.get("in_boss_battle"):
                logger.info(f"⚔️ Запуск босса по ключевому слову: {boss_id}, user_id={user_id}")
                from handlers.bosses import start_boss_battle
                await start_boss_battle(update, context, boss_id)
                log_user_action(user_id, "START_BOSS", f"boss={boss_id}")
                return True
        
        # === ❌ НЕИЗВЕСТНАЯ КОМАНДА ===
        logger.warning(f"❓ Не распознана команда: '{raw_text}' от user_id={user_id}")
        
        # 🔥 ПОДСКАЗКА: если похоже на число — возможно это ответ на задачу
        if raw_text.lstrip('-').isdigit() or (raw_text.replace('.', '', 1).lstrip('-').isdigit() and raw_text.count('.') <= 1):
            await update.message.reply_text(
                "🤔 Это похоже на ответ на задачу!\n\n"
                "Если ты в уровне — проверь что уровень активен.\n"
                "Если нет — нажми 🎮 Играть → 🏝️ Острова → ➕ Сложение",
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(
                "💡 <b>Не понимаю эту команду.</b>\n\n"
                "Выбери действие из меню или напиши:\n"
                "• 🎮 Играть — начать игру\n"
                "• 🏰 Замок — твой замок с Владимиром\n"
                "• 🏦 Златочёт — банк с процентами\n"
                "• ⬅️ Назад — выйти из уровня/боя",
                parse_mode="HTML"
            )
        return False
    
    except Exception as e:
        user_id = update.effective_user.id if update.effective_user else 0
        log_error(user_id, str(e), exc_info=True)
        logger.error(f"❌ Ошибка в handle_message: {e}", exc_info=True)
        
        await update.message.reply_text(
            "⚠️ Ой! Что-то пошло не так.\n\n"
            "Попробуй:\n"
            "• Написать /start\n"
            "• Нажать ⬅️ Назад\n"
            "• Перезапустить бота"
        )
        return True