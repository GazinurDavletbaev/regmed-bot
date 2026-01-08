import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from presentation.telegram.handlers.access_request import router as access_request_router
from presentation.telegram.middlewares.access import AccessMiddleware
from presentation.telegram.handlers.access_request import router as access_request_router
from presentation.telegram.handlers.admin import router as admin_router


# Р›РѕРіРёСЂРѕРІР°РЅРёРµ
logging.basicConfig(level=logging.INFO)

async def main():
    # Р—Р°РіСЂСѓР·РєР° РїРµСЂРµРјРµРЅРЅС‹С… РѕРєСЂСѓР¶РµРЅРёСЏ (РїРѕР·Р¶Рµ Р·Р°РјРµРЅРёРј РЅР° pydantic-config)
    import os
    from dotenv import load_dotenv
    load_dotenv()
    print("TELEGRAM_BOT_TOKEN:", os.getenv("TELEGRAM_BOT_TOKEN"))
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN РЅРµ Р·Р°РґР°РЅ РІ .env")
    
    # РРЅРёС†РёР°Р»РёР·Р°С†РёСЏ Р±РѕС‚Р° Рё РґРёСЃРїРµС‚С‡РµСЂР°
    bot = Bot(token=bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.update.middleware(AccessMiddleware())


    dp.include_router(access_request_router)
    dp.include_router(admin_router)

    
    # Р—РґРµСЃСЊ РїРѕР·Р¶Рµ РїРѕРґРєР»СЋС‡РёРј С…РµРЅРґР»РµСЂС‹, РјРёРґР»РІР°СЂРё Рё С‚.Рґ.
    
    # Р—Р°РїСѓСЃРє
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

