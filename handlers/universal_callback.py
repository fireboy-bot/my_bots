from handlers.shop import handle_shop_callback
from handlers.alchemy import handle_alchemy_callback

async def universal_callback_handler(update, context):
    data = update.callback_query.data
    
    if data.startswith("buy_"):
        await handle_shop_callback(update, context)
    elif data.startswith("craft_"):
        await handle_alchemy_callback(update, context)
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
    else:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("❌ Неизвестная команда")