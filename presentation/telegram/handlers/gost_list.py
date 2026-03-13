# presentation/telegram/handlers/gost_list.py
from aiogram import Router, types
from aiogram.filters import Command
from qdrant_client import QdrantClient

router = Router()
client = QdrantClient("localhost", port=6333)  # или укажи IP мощного компа
COLLECTION_NAME = "med_docs"

@router.message(Command("gosts"))
async def list_gosts(message: types.Message):
    # Получаем все точки с полем gost_number (ограничим 10 000)
    results = client.scroll(
        collection_name=COLLECTION_NAME,
        limit=10000,
        with_payload=["gost_number"]
    )[0]
    
    # Собираем уникальные номера
    unique_gosts = set()
    for point in results:
        gost = point.payload.get("gost_number")
        if gost:
            unique_gosts.add(gost)
    
    if unique_gosts:
        # Сортируем для красоты
        sorted_gosts = sorted(unique_gosts)
        answer = "📚 В базе найдены следующие ГОСТы:\n\n" + "\n".join(sorted_gosts)
    else:
        answer = "❌ В базе пока нет документов."
    
    await message.answer(answer)