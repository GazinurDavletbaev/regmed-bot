from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, Update
from typing import Callable, Dict, Any, Awaitable, Union
import logging
from infrastructure.database.supabase_client import SupabaseClient

logger = logging.getLogger(__name__)

class AccessMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,  # Теперь принимаем Update
        data: Dict[str, Any]
    ) -> Any:
        # Извлекаем user_id в зависимости от типа события
        user_id = None
        # Добавить в начало метода __call__:
        if event.message and event.message.text and event.message.text.startswith("/start"):
            return await handler(event, data)
        if event.callback_query and event.callback_query.data and event.callback_query.data.startswith("req_access:"):
            return await handler(event, data)
        if event.message:
            user_id = event.message.from_user.id
        elif event.callback_query:
            user_id = event.callback_query.from_user.id
        else:
            # Если нет ни message, ни callback_query — пропускаем проверку
            return await handler(event, data)
        
        if not user_id:
            return await handler(event, data)
        
        client = SupabaseClient.get_client()
        
        try:
            response = client.table("bot_users") \
                .select("*") \
                .eq("telegram_id", user_id) \
                .eq("is_active", True) \
                .execute()
            
            if response.data:
                data["user_allowed"] = True
                data["user_role"] = response.data[0].get("role", "user")
                data["user_id"] = user_id
                logger.info(f"✅ Пользователь {user_id} допущен (роль: {data['user_role']})")
            else:
                data["user_allowed"] = False
                data["user_id"] = user_id
                logger.warning(f"❌ Пользователь {user_id} не допущен")
                # Отправляем сообщение, если событие — Message
                if event.message:
                    await event.message.answer(
                        "⛔ Доступ запрещён. Обратитесь к руководителю для получения доступа."
                    )
                return
                
        except Exception as e:
            logger.error(f"Ошибка при проверке доступа пользователя {user_id}: {e}")
            data["user_allowed"] = False
            if event.message:
                await event.message.answer("⚠️ Ошибка проверки доступа. Попробуйте позже.")
            return
        
        return await handler(event, data)