import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from infrastructure.database.supabase_client import SupabaseClient

logger = logging.getLogger(__name__)
router = Router()

class AccessStates(StatesGroup):
    awaiting_approval = State()

@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    logger.info(f"Пользователь {user_id} вызвал /start")
    
    client = SupabaseClient.get_client()
    
    response = client.table("bot_users") \
        .select("*") \
        .eq("telegram_id", user_id) \
        .execute()
    
    logger.info(f"Результат запроса: {response.data}")
    
    if response.data:
        await message.answer(
            f"👋 Добро пожаловать, {message.from_user.full_name}!\n"
            f"Ваша роль: {response.data[0].get('role', 'user')}"
        )
    else:
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Запросить доступ", callback_data=f"req_access:{user_id}")
        await message.answer(
            "🔐 У вас нет доступа к боту.\n"
            "Нажмите кнопку ниже, чтобы отправить запрос руководителю.",
            reply_markup=builder.as_markup()
        )
        logger.info(f"Пользователь {user_id} не найден, предложена кнопка")

@router.callback_query(F.data.startswith("req_access:"))
async def process_access_request(callback: CallbackQuery):
    target_user_id = int(callback.data.split(":")[1])
    
    client = SupabaseClient.get_client()
    admins = client.table("bot_users") \
        .select("telegram_id") \
        .eq("role", "admin") \
        .eq("is_active", True) \
        .execute()
    
    if not admins.data:
        await callback.message.answer("⚠️ В системе нет активных администраторов.")
        await callback.answer()
        return
    
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Разрешить", callback_data=f"approve:{target_user_id}")
    builder.button(text="❌ Отклонить", callback_data=f"deny:{target_user_id}")
    
    for admin in admins.data:
        try:
            await callback.bot.send_message(
                admin["telegram_id"],
                f"🆕 Пользователь @{callback.from_user.username or callback.from_user.full_name} (ID: {target_user_id}) запрашивает доступ к боту.",
                reply_markup=builder.as_markup()
            )
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление админу {admin['telegram_id']}: {e}")
    
    await callback.answer("✅ Запрос отправлен администраторам.")

@router.callback_query(F.data.startswith("approve:"))
async def approve_user(callback: CallbackQuery):
    admin_id = callback.from_user.id
    target_user_id = int(callback.data.split(":")[1])
    
    client = SupabaseClient.get_client()
    
    admin_check = client.table("bot_users") \
        .select("*") \
        .eq("telegram_id", admin_id) \
        .eq("role", "admin") \
        .execute()
    
    if not admin_check.data:
        await callback.answer("⛔ У вас нет прав администратора.")
        return
    
    client.table("bot_users").insert({
        "telegram_id": target_user_id,
        "role": "user",
        "approved_by": admin_id,
        "is_active": True
    }).execute()
    
    await callback.message.edit_text(
        f"✅ Пользователь {target_user_id} добавлен."
    )
    
    try:
        await callback.bot.send_message(
            target_user_id,
            "🎉 Ваш доступ к боту подтверждён! Напишите /start."
        )
    except Exception as e:
        logger.error(f"Не удалось уведомить пользователя {target_user_id}: {e}")
    
    await callback.answer()

@router.callback_query(F.data.startswith("deny:"))
async def deny_user(callback: CallbackQuery):
    admin_id = callback.from_user.id
    target_user_id = int(callback.data.split(":")[1])
    
    client = SupabaseClient.get_client()
    
    admin_check = client.table("bot_users") \
        .select("*") \
        .eq("telegram_id", admin_id) \
        .eq("role", "admin") \
        .execute()
    
    if not admin_check.data:
        await callback.answer("⛔ У вас нет прав администратора.")
        return
    
    await callback.message.edit_text(
        f"❌ Запрос пользователя {target_user_id} отклонён."
    )
    
    try:
        await callback.bot.send_message(
            target_user_id,
            "⛔ Ваш запрос на доступ был отклонён администратором."
        )
    except Exception as e:
        logger.error(f"Не удалось уведомить пользователя {target_user_id}: {e}")
    
    await callback.answer()
