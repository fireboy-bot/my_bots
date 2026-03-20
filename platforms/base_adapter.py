# platforms/base_adapter.py
"""
Базовый интерфейс адаптера платформы.
Все адаптеры (Telegram, MAX, etc.) должны наследовать этот класс.

Версия: 1.0 (MVP) 🔄
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class MessageAdapter(ABC):
    """
    Абстрактный базовый класс для всех платформ.
    
    Определяет единый интерфейс для отправки сообщений,
    чтобы ядро (core/) не зависело от конкретной платформы.
    """
    
    @abstractmethod
    async def send_message(
        self,
        user_id: str,
        text: str,
        reply_markup: Optional[Any] = None,
        photo: Optional[str] = None,
        parse_mode: str = "Markdown"
    ) -> bool:
        """
        Отправить сообщение пользователю.
        
        Args:
            user_id: ID пользователя (универсальный строковый формат)
            text: Текст сообщения
            reply_markup: Клавиатура/кнопки (нативный формат платформы)
            photo: Ссылка на изображение (опционально)
            parse_mode: Режим парсинга ("Markdown", "HTML", "plain")
            
        Returns:
            bool: True если отправлено успешно, False если ошибка
        """
        pass
    
    @abstractmethod
    async def edit_message(
        self,
        chat_id: str,
        message_id: int,
        text: str,
        reply_markup: Optional[Any] = None
    ) -> bool:
        """
        Редактировать существующее сообщение.
        
        Args:
            chat_id: ID чата
            message_id: ID сообщения для редактирования
            text: Новый текст
            reply_markup: Новая клавиатура (опционально)
            
        Returns:
            bool: True если успешно
        """
        pass
    
    @abstractmethod
    def parse_callback_data(self,  str) -> Dict[str, str]:
        """
        Распарсить данные обратного вызова (нажатие кнопки).
        
        Args:
            data: Сырые данные от платформы
            
        Returns:
            Dict: Словарь {параметр: значение}
        """
        pass
    
    @abstractmethod
    def normalize_user_id(self, raw_id: Any) -> str:
        """
        Привести ID пользователя к универсальному строковому формату.
        
        Args:
            raw_id: ID в формате платформы (int для TG, phone для MAX)
            
        Returns:
            str: Универсальный ID для хранения в БД
        """
        pass
    
    @property
    @abstractmethod
    def platform_name(self) -> str:
        """
        Название платформы.
        
        Returns:
            str: 'telegram', 'max', 'web', etc.
        """
        pass
    
    async def close(self):
        """
        Закрыть соединения и освободить ресурсы.
        Вызывается при завершении работы бота.
        """
        pass