import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from infrastructure.database.supabase_client import SupabaseClient

logger = logging.getLogger(__name__)
router = Router()

# Фильтр "только админ" (будем проверять через data['user_role'])
def admin_only(handler):
    async def wrapper(message: Message, *args, **kwargs):
        if kwargs.get("user_role") != "admin":
            await message.answer("⛔ Только администратор может использовать эту команду.")
            return
        return await handler(message, *args, **kwargs)
    return wrapper

@router.message(Command("add_user"))
@admin_only
async def cmd_add_user(message: Message, user_id: int):
    """Добавить пользователя (формат: /add_user <telegram_id> <role>)"""
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("Использование: /add_user <telegram_id> <role>\nРоли: admin, manager, user")
        return
    
    try:
        target_id = int(parts[1])
        role = parts[2].lower()
        if role not in ("admin", "manager", "user"):
            await message.answer("Роль должна быть: admin, manager или user")
            return
        
        client = SupabaseClient.get_client()
        
        # Проверяем, не существует ли уже пользователь
        existing = client.table("bot_users") \
            .select("*") \
            .eq("telegram_id", target_id) \
            .execute()
        
        if existing.data:
            await message.answer(f"⚠️ Пользователь {target_id} уже есть в базе.")
            return
        
        # Добавляем
        client.table("bot_users").insert({
            "telegram_id": target_id,
            "role": role,
            "approved_by": user_id,
            "is_active": True
        }).execute()
        
        await message.answer(f"✅ Пользователь {target_id} добавлен с ролью '{role}'.")
        logger.info(f"Админ {user_id} добавил пользователя {target_id} как {role}")
        
    except ValueError:
        await message.answer("❌ Неверный формат ID. ID должен быть числом.")
    except Exception as e:
        logger.error(f"Ошибка при добавлении пользователя: {e}")
        await message.answer("❌ Ошибка базы данных.")

@router.message(Command("list_users"))
@admin_only
async def cmd_list_users(message: Message):
    """Показать всех пользователей"""
    try:
        client = SupabaseClient.get_client()
        response = client.table("bot_users") \
            .select("telegram_id, role, is_active, approved_at") \
            .execute()
        
        if not response.data:
            await message.answer("📭 В базе пока нет пользователей.")
            return
        
        lines = ["📋 Список пользователей:"]
        for user in response.data:
            status = "✅" if user["is_active"] else "❌"
            lines.append(f"{status} ID: {user['telegram_id']} — {user['role']} ({user['approved_at']})")
        
        await message.answer("\n".join(lines))
    except Exception as e:
        logger.error(f"Ошибка при получении списка пользователей: {e}")
        await message.answer("❌ Ошибка базы данных.")