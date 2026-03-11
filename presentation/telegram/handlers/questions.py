# presentation/telegram/handlers/questions.py

from aiogram import Router, types
from aiogram.filters import Command
from domain.rag_service import RAGService

router = Router()

# Инициализируем сервис один раз (можно вынести в dependency injection, но для простоты пока так)
rag = RAGService()

@router.message()
async def handle_question(message: types.Message):
    """
    Обрабатывает все текстовые сообщения (кроме команд).
    Предполагается, что AccessMiddleware уже проверил доступ.
    """
    # Игнорируем команды (они уже обработаны другими роутерами)
    if message.text.startswith('/'):
        return

    question = message.text
    await message.answer("🔍 Ищу информацию в базе знаний...")

    # Получаем ответ от RAGService
    answer = rag.answer_question(question)

    # Отправляем результат
    await message.answer(answer)