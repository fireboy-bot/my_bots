# core/avatar_cache.py
"""
Кэш аватарок персонажей (file_id).
Версия: 2.0 (Vladimir Mood Avatars Support) 🗄️⚡🎩
"""

from telegram import Bot
from typing import Dict, Optional
import os
import json
import asyncio
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_FILE = os.path.join(BASE_DIR, "data", "avatar_cache.json")

class AvatarCache:
    def __init__(self, bot: Bot):
        self.bot = bot
        self._cache: Dict[str, str] = {}
        self._loading = False
        
        # ✅ ОБНОВЛЁННЫЙ СПИСОК АВАТАРОК
        self.avatar_paths = {
            # === ГЕРОИ ===
            "manunya": "images/manunya.jpg",
            "georgy": "images/georgy.jpg",
            
            # === ТОРГОВЕЦ И АЛХИМИК ===
            "shop_keeper": "images/shop_keeper.jpg",
            "alchemist_mad": "images/alchemist_mad.jpg",
            
            # === ВЛАДИМИР (6 настроений) ===
            "vladimir_calm": "images/vladimir_calm.jpg",
            "vladimir_approve": "images/vladimir_approve.jpg",
            "vladimir_disappointed": "images/vladimir_disappointed.jpg",
            "vladimir_proud": "images/vladimir_proud.jpg",
            "vladimir_thinking": "images/vladimir_thinking.jpg",
            "vladimir_relaxed": "images/vladimir_relaxed.jpg",
            
            # === БОССЫ ===
            "null_void": "images/null_void.jpg",
            "minus_shadow": "images/minus_shadow.jpg",
            "evil_multiplier": "images/evil_multiplier.jpg",
            "fracosaur": "images/fracosaur.jpg",
            "final_boss": "images/final_boss.jpg",
            
            # === ИСТИННЫЙ ВЛАДЫКА (3 фазы) ===
            "true_lord_calm": "images/true_lord_calm.jpg",
            "true_lord_angry": "images/true_lord_angry.jpg",
            "true_lord_desperate": "images/true_lord_desperate.jpg",
            
            # === ХРАНИТЕЛИ МИРОВ ===
            "time_keeper": "images/time_keeper.jpg",
            "measure_keeper": "images/measure_keeper.jpg",
            "logic_keeper": "images/logic_keeper.jpg",
        }
    
    async def load_avatars(self) -> Dict[str, str]:
        if self._loading:
            return self._cache
        
        self._loading = True
        
        print(f"🔍 Проверка кэша: {CACHE_FILE}")
        if self._load_from_file():
            loaded_count = sum(1 for v in self._cache.values() if v is not None)
            if loaded_count == len(self.avatar_paths):
                print(f"✅ Все аватарки загружены из кэша ({loaded_count}/{len(self.avatar_paths)})")
                self._loading = False
                return self._cache
            else:
                print(f"⚠️ Частичный кэш: {loaded_count}/{len(self.avatar_paths)}. До загружаем...")
        
        print("🖼️ Загружаем аватарки...")
        
        admin_ids_str = os.getenv("ADMIN_IDS", "")
        admin_chat_id = None
        if admin_ids_str:
            admin_ids_str = admin_ids_str.strip("[] ").replace(" ", "")
            try:
                admin_chat_id = int(admin_ids_str.split(",")[0])
            except ValueError:
                pass
        
        loaded_count = 0
        missing_count = 0
        total_count = len(self.avatar_paths)
        
        for i, (character, path) in enumerate(self.avatar_paths.items(), 1):
            if character in self._cache and self._cache[character] is not None:
                print(f"⏭️ Пропускаем {character} (уже в кэше)")
                continue
            
            print(f"📊 [{i}/{total_count}] {character}...")
            
            try:
                full_path = os.path.join(BASE_DIR, path)
                
                if not os.path.exists(full_path):
                    print(f"⚠️ Файл не найден: {full_path}")
                    missing_count += 1
                    self._cache[character] = None
                    continue
                
                with open(full_path, 'rb') as f:
                    message = await asyncio.wait_for(
                        self.bot.send_photo(
                            chat_id=admin_chat_id,
                            photo=f,
                            caption=f"🖼️ {character} ({i}/{total_count})"
                        ),
                        timeout=10
                    )
                    
                    file_id = message.photo[-1].file_id
                    self._cache[character] = file_id
                    loaded_count += 1
                    
                    print(f"✅ {character}: {file_id[:20]}...")
                
                # ✅ СОХРАНЯЕМ ПОСЛЕ КАЖДОЙ АВАТАРКИ
                self._save_to_file()
                await asyncio.sleep(0.1)
                
            except asyncio.TimeoutError:
                print(f"⏰ Таймаут: {character}")
                self._cache[character] = None
                missing_count += 1
                self._save_to_file()
                
            except Exception as e:
                print(f"❌ Ошибка {character}: {e}")
                self._cache[character] = None
                missing_count += 1
                self._save_to_file()
        
        self._loading = False
        print(f"\n📊 ИТОГИ: ✅ {loaded_count} | ⚠️ {missing_count} | 📦 {total_count}")
        
        return self._cache
    
    def _load_from_file(self) -> bool:
        try:
            if os.path.exists(CACHE_FILE):
                print(f"📂 Читаю кэш из: {CACHE_FILE}")
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    self._cache = loaded
                    print(f"✅ Загружено {len(loaded)} записей")
                return True
        except Exception as e:
            print(f"❌ Ошибка загрузки кэша: {e}")
        return False
    
    def _save_to_file(self):
        try:
            os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ Ошибка сохранения кэша: {e}")
    
    def get_avatar(self, character: str) -> Optional[str]:
        return self._cache.get(character)
    
    def is_loaded(self, character: str) -> bool:
        return character in self._cache and self._cache[character] is not None
    
    def is_loading(self) -> bool:
        return self._loading
    
    def check_heroes_loaded(self) -> bool:
        """Проверяет, загружены ли Манюня и Георгий."""
        try:
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                    manunya_loaded = cache.get("manunya") is not None
                    georgy_loaded = cache.get("georgy") is not None
                    return manunya_loaded and georgy_loaded
        except Exception as e:
            print(f"⚠️ Ошибка проверки кэша героев: {e}")
        return False
    
    def clear_cache(self):
        self._cache = {}
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)
        print("🗑️ Кэш аватарок очищен")


_avatar_cache: Optional[AvatarCache] = None

def init_avatar_cache(bot: Bot) -> AvatarCache:
    global _avatar_cache
    _avatar_cache = AvatarCache(bot)
    return _avatar_cache

def get_avatar_cache() -> Optional[AvatarCache]:
    return _avatar_cache