# test_env.py
import os
from dotenv import load_dotenv

# Загружаем .env
load_dotenv()

# Проверяем переменные
bot_token = os.getenv("BOT_TOKEN")
encrypt_key = os.getenv("PARENT_DATA_ENCRYPTION_KEY")

print(f"🔹 BOT_TOKEN: {'✅ Есть' if bot_token else '❌ Пустой'}")
print(f"🔹 PARENT_DATA_ENCRYPTION_KEY: {'✅ Есть' if encrypt_key else '❌ Пустой'}")

# Проверка длины ключа
if encrypt_key:
    print(f"🔹 Длина ключа: {len(encrypt_key)} (должно быть 44)")
    print(f"🔹 Заканчивается на ==: {encrypt_key.endswith('==')}")