# platforms/max_adapter.py
"""
Адаптер MAX (VK Mini Apps / VK Мессенджер) для бота «Числяндия».
Оборачивает VK API в универсальный интерфейс MessageAdapter.

Версия: 1.0 (MVP) 🟣
"""
import logging
import json
import requests
from typing import Optional, Dict, Any
from platforms.base_adapter import MessageAdapter

logger = logging.getLogger(__name__)


class MaxAdapter(MessageAdapter):
    """
    Адаптер для платформы MAX (VK).
    
    Реализует интерфейс MessageAdapter через VK API,
    предоставляя единый способ отправки сообщений.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Инициализация адаптера.
        
        Args:
            config: Словарь с настройками:
                - vk_token: токен сообщества (обязательно)
                - vk_version: версия API (по умолчанию "5.131")
                - group_id: ID сообщества (для отправки от имени группы)
                - api_url: базовый URL API (по умолчанию "https://api.vk.com/method")
        """
        self.vk_token = config.get('vk_token')
        self.vk_version = config.get('vk_version', '5.131')
        self.group_id = config.get('group_id')
        self.api_url = config.get('api_url', 'https://api.vk.com/method')
        
        if not self.vk_token:
            raise ValueError("vk_token is required for MaxAdapter")
        
        logger.info(f"✅ MaxAdapter инициализирован (VK API v{self.vk_version})")
    
    def _make_api_request(self, method: str, params: Dict[str, Any]) -> Optional[Dict]:
        """
        Делает запрос к VK API.
        
        Returns:
            dict с ответом или None при ошибке
        """
        url = f"{self.api_url}/{method}"
        params.update({
            'access_token': self.vk_token,
            'v': self.vk_version
        })
        
        try:
            response = requests.post(url, data=params, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if 'error' in result:
                error = result['error']
                logger.error(f"❌ VK API error: {error.get('error_code')} - {error.get('error_msg')}")
                return None
            
            return result.get('response')
            
        except requests.exceptions.Timeout:
            logger.error(f"❌ VK API timeout: {method}")
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка запроса к VK API: {e}")
            return None
    
    async def send_message(
        self,
        user_id: str,
        text: str,
        reply_markup: Optional[Any] = None,
        photo: Optional[str] = None,
        parse_mode: str = "Markdown"
    ) -> bool:
        """
        Отправить сообщение в MAX (VK).
        
        Поддерживает:
        - Текст с базовым форматированием
        - Кнопки (через keyboard VK формата)
        - Фото (упрощённо — через ссылку в тексте)
        
        Args:
            user_id: ID пользователя (формат "vk_123456" или "123456")
            text: Текст сообщения
            reply_markup: Клавиатура (Telegram format → конвертируется)
            photo: URL изображения (VK требует загрузку, поэтому пока ссылка в тексте)
            parse_mode: "Markdown", "HTML" или "plain"
            
        Returns:
            bool: True если отправлено успешно
        """
        try:
            # Извлекаем числовой VK ID
            vk_id = self._extract_vk_id(user_id)
            
            # Формируем базовые параметры
            params = {
                'user_id': vk_id,
                'message': text,
                'random_id': 0  # VK требует, 0 = автогенерация
            }
            
            # Добавляем parse_mode если поддерживается
            if parse_mode in ('HTML', 'Markdown', 'MarkdownV2'):
                params['parse_mode'] = parse_mode
            
            # Добавляем клавиатуру если есть
            if reply_markup:
                keyboard = self._convert_keyboard(reply_markup)
                if keyboard:
                    params['keyboard'] = json.dumps(keyboard, ensure_ascii=False)
                    params['one_time'] = False
            
            # 🔹 УПРОЩЁННАЯ ОБРАБОТКА ФОТО:
            # Полная реализация требует загрузки через photos.getMessagesUploadServer
            if photo:
                # Если photo это URL — добавляем в текст
                if photo.startswith('http'):
                    params['message'] = f"{text}\n\n🖼️ {photo}"
                # Если photo это file_id от ТГ — пока игнорируем (нужна конвертация)
            
            # Делаем запрос к API
            result = self._make_api_request('messages.send', params)
            
            if result is not None:
                logger.debug(f"✅ MAX: сообщение отправлено {user_id}")
                return True
            else:
                logger.error(f"❌ MAX: не удалось отправить сообщение {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ MAX send error: {e}", exc_info=True)
            return False
    
    async def edit_message(
        self,
        chat_id: str,
        message_id: int,
        text: str,
        reply_markup: Optional[Any] = None
    ) -> bool:
        """
        Редактировать сообщение в VK.
        
        ⚠️ Примечание: VK позволяет редактировать только сообщения бота
        и только в течение короткого времени после отправки.
        """
        try:
            vk_id = self._extract_vk_id(chat_id)
            
            params = {
                'peer_id': vk_id,
                'message_id': message_id,
                'message': text,
            }
            
            if reply_markup:
                keyboard = self._convert_keyboard(reply_markup)
                if keyboard:
                    params['keyboard'] = json.dumps(keyboard, ensure_ascii=False)
            
            result = self._make_api_request('messages.edit', params)
            
            if result is not None:
                logger.debug(f"✅ MAX: сообщение отредактировано {chat_id}:{message_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"❌ MAX edit error: {e}")
            return False
    
    def _convert_keyboard(self, keyboard_data: Any) -> Optional[Dict]:
        """
        Конвертирует клавиатуру из формата бота в формат VK keyboard.
        
        Вход: ReplyKeyboardMarkup или InlineKeyboardMarkup из telegram
        Выход: dict в формате VK API keyboard
        
        Формат VK keyboard:
        {
            "one_time": false,
            "inline": false,
            "buttons": [
                [
                    {
                        "action": {
                            "type": "text",
                            "payload": "{\"command\":\"btn_text\"}",
                            "label": "Текст кнопки"
                        }
                    }
                ]
            ]
        }
        """
        if not keyboard_data:
            return None
        
        # Если уже в формате VK — возвращаем как есть
        if isinstance(keyboard_data, dict) and 'buttons' in keyboard_data:
            return keyboard_data
        
        buttons = []
        
        # Извлекаем строки кнопок из разных форматов
        if hasattr(keyboard_data, 'keyboard'):
            # ReplyKeyboardMarkup
            rows = keyboard_data.keyboard
        elif hasattr(keyboard_data, 'inline_keyboard'):
            # InlineKeyboardMarkup
            rows = keyboard_data.inline_keyboard
        elif isinstance(keyboard_data, list):
            rows = keyboard_data
        else:
            return None
        
        for row in rows:
            vk_row = []
            for btn in row:
                # Определяем текст кнопки
                label = None
                if hasattr(btn, 'text'):
                    label = btn.text
                elif isinstance(btn, dict) and 'text' in btn:
                    label = btn['text']
                elif isinstance(btn, str):
                    label = btn
                
                if label:
                    # Создаем payload для VK (строка до 255 байт)
                    payload_data = {'command': f'btn_{label}'}
                    payload_str = json.dumps(payload_data, ensure_ascii=False)[:255]
                    
                    vk_row.append({
                        'action': {
                            'type': 'text',
                            'payload': payload_str,
                            'label': label
                        }
                    })
            
            if vk_row:
                buttons.append(vk_row)
        
        if not buttons:
            return None
        
        return {
            'one_time': False,
            'inline': False,
            'buttons': buttons
        }
    
    def parse_callback_data(self, data: str) -> Dict[str, str]:
        """
        Распарсить callback_data от VK.
        
        VK использует JSON payload в кнопках.
        Формат: {"command": "btn_action:param:value"}
        
        Args:
            data: Сырая строка из VK callback
            
        Returns:
            Dict: {параметр: значение}
        """
        result = {}
        
        try:
            # Пытаемся распарсить как JSON (VK payload)
            payload = json.loads(data)
            if isinstance(payload, dict):
                return payload
        except json.JSONDecodeError:
            pass
        
        # Фоллбэк: парсим как "key:value|key2:value2"
        parts = data.split("|")
        for part in parts:
            if ":" in part:
                key, _, value = part.partition(":")
                result[key.strip()] = value.strip()
        
        # Если нет : — считаем всю строку действием
        if not result and data:
            result["action"] = data
        
        return result
    
    def _extract_vk_id(self, user_id: str) -> int:
        """
        Извлекает числовой VK ID из строки.
        
        Поддерживает форматы:
        - "123456" → 123456
        - "vk_123456" → 123456
        - "-123456" (группа) → -123456
        """
        if isinstance(user_id, int):
            return user_id
        
        user_id = str(user_id).strip()
        
        if user_id.startswith('vk_'):
            user_id = user_id[3:]
        
        try:
            return int(user_id)
        except ValueError:
            logger.error(f"❌ Не удалось извлечь VK ID из: {user_id}")
            return 0
    
    def normalize_user_id(self, raw_id: Any) -> str:
        """
        Привести VK user_id к универсальному строковому формату.
        
        Формат: "vk_<число>" для однозначности.
        
        Args:
            raw_id: int или str
            
        Returns:
            str: Универсальный ID (например "vk_123456")
        """
        if isinstance(raw_id, str) and raw_id.startswith('vk_'):
            return raw_id
        
        numeric_id = self._extract_vk_id(raw_id)
        return f"vk_{numeric_id}"
    
    @property
    def platform_name(self) -> str:
        """Название платформы"""
        return "max"
    
    async def close(self):
        """Закрыть соединения (для requests не требуется)"""
        logger.info("🔌 MaxAdapter closed")
        pass