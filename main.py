import asyncio
import logging
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from presentation.telegram.handlers.access_request import router as access_request_router
from presentation.telegram.handlers.admin import router as admin_router
from presentation.telegram.handlers.questions import router as questions_router
from presentation.telegram.middlewares.access import AccessMiddleware
from presentation.telegram.handlers.gost_list import router as gost_list_router


# Логирование
logging.basicConfig(level=logging.INFO)

async def main():
    # Загрузка переменных окружения
    load_dotenv()
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN не задан в .env")

    # Инициализация бота и диспетчера
    bot = Bot(token=bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Подключаем мидлварь для проверки доступа
    dp.update.middleware(AccessMiddleware())

    # Подключаем роутеры
    dp.include_router(access_request_router)
    dp.include_router(admin_router)
    dp.include_router(questions_router)
    dp.include_router(gost_list_router)
    # Запуск
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())