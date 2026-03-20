# platforms/max_adapter.py
"""
Адаптер платформы MAX (User API через wappi.pro).
Версия: 1.0 (Заглушка — готов к реализации) 🔄

Документация:
• https://wappi.pro/max-api-documentation
• https://dev.max.ru/docs/chatbots/bots-create
"""
import logging
from typing import Optional, Dict, Any
import httpx

from platforms.base_adapter import MessageAdapter

logger = logging.getLogger(__name__)


class MaxAdapter(MessageAdapter):
    """
    Адаптер для платформы MAX.
    
    Использует User API (wappi.pro) для отправки сообщений
    от имени личного аккаунта.
    
    ⚠️ ВНИМАНИЕ: Это заглушка. Реализация требует:
    1. Токен от wappi.pro
    2. Profile ID
    3. Настроенный webhook
    """
    
    def __init__(
        self,
        api_token: Optional[str] = None,
        profile_id: Optional[str] = None,
        webhook_url: Optional[str] = None
    ):
        """
        Инициализация адаптера MAX.
        
        Args:
            api_token: Токен API от wappi.pro
            profile_id: ID профиля в MAX
            webhook_url: URL для входящих вебхуков
        """
        self.api_token = api_token or ""
        self.profile_id = profile_id or ""
        self.webhook_url = webhook_url or ""
        self.base_url = "https://wappi.pro"
        
        # HTTP-клиент для запросов к API
        self.client = httpx.AsyncClient(timeout=30)
        
        logger.info(f"🔄 MaxAdapter инициализирован (заглушка)")
    
    @property
    def headers(self) -> Dict[str, str]:
        """Заголовки для API запросов"""
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
    
    async def send_message(
        self,
        user_id: str,
        text: str,
        reply_markup: Optional[Any] = None,
        photo: Optional[str] = None,
        parse_mode: str = "Markdown"
    ) -> bool:
        """
        Отправить сообщение в MAX.
        
        ⚠️ ЗАГЛУШКА: Возвращает False, пока не реализовано
        
        Args:
            user_id: Номер телефона (например, "79115576368")
            text: Текст сообщения
            reply_markup: Кнопки (формат MAX: [{text, action}])
            photo: URL изображения (не file_id!)
            parse_mode: "Markdown", "HTML", или "plain"
            
        Returns:
            bool: False (пока не реализовано)
        """
        logger.warning(f"⚠️ MaxAdapter.send_message() вызван, но не реализован")
        logger.warning(f"   user_id={user_id}, text={text[:50]}...")
        
        # TODO: Реализовать отправку через API MAX
        # Пример:
        # response = await self.client.post(
        #     f"{self.base_url}/maxapi/sync/message/send",
        #     headers=self.headers,
        #     json={
        #         "profile_id": self.profile_id,
        #         "phone": user_id,
        #         "body": text,
        #         "type": "text"
        #     }
        # )
        # return response.status_code == 200
        
        return False
    
    async def edit_message(
        self,
        chat_id: str,
        message_id: int,
        text: str,
        reply_markup: Optional[Any] = None
    ) -> bool:
        """
        Редактировать сообщение в MAX.
        
        ⚠️ ЗАГЛУШКА: Возвращает False
        """
        logger.warning(f"⚠️ MaxAdapter.edit_message() вызван, но не реализован")
        return False
    
    def parse_callback_data(self,  str) -> Dict[str, str]:
        """
        Распарсить callback_data от MAX.
        
        Формат MAX: кнопки имеют action.data
        Пример: "action:buy_item|id:potion|qty:1"
        
        Args:
            data: Сырая строка от платформы
            
        Returns:
            Dict: {параметр: значение}
        """
        result = {}
        
        # Разбиваем по |
        parts = data.split("|")
        for part in parts:
            if ":" in part:
                key, _, value = part.partition(":")
                result[key.strip()] = value.strip()
        
        # Если нет : — считаем всю строку действием
        if not result and data:
            result["action"] = data
        
        return result
    
    def normalize_user_id(self, raw_id: Any) -> str:
        """
        Привести ID пользователя к строковому формату.
        
        MAX использует номер телефона как ID:
        • Вход: "79115576368" или "+79115576368" или 79115576368
        • Выход: "79115576368" (строка без +)
        
        Args:
            raw_id: int или str
            
        Returns:
            str: Универсальный ID
        """
        phone = str(raw_id).replace("+", "").replace("-", "").replace(" ", "")
        return phone
    
    @property
    def platform_name(self) -> str:
        """Название платформы"""
        return "max"
    
    async def close(self):
        """Закрыть HTTP-соединения"""
        await self.client.aclose()
        logger.info("🔌 MaxAdapter closed")
    
    # ============================================
    # ✅ ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ (для будущей реализации)
    # ============================================
    
    async def handle_webhook(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Обработка входящего вебхука от MAX.
        
        Args:
            request: JSON от MAX API
            
        Returns:
            Dict: Распарсенные сообщения или None
        """
        messages = request.get("messages", [])
        results = []
        
        for msg in messages:
            if msg.get("wh_type") == "incoming_message":
                parsed = {
                    "user_id": self.normalize_user_id(msg.get("phone")),
                    "text": msg.get("body"),
                    "type": msg.get("type"),
                    "chat_id": msg.get("chatId"),
                    "timestamp": msg.get("time")
                }
                
                # Если это нажатие кнопки (callback)
                if msg.get("type") == "callback":
                    parsed["callback_data"] = msg.get("data")
                    parsed["is_callback"] = True
                
                results.append(parsed)
        
        return {"results": results} if results else None
    
    def _normalize_phone(self, user_id: str) -> str:
        """Приводит номер к формату 79115576368"""
        return self.normalize_user_id(user_id)