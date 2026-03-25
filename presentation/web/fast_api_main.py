from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
import logging
import os
import jinja2

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from domain.rag_service import RAGService


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="GOST Assistant Web")

# Подключаем статику
app.mount("/static", StaticFiles(directory="presentation/web/static"), name="static")

# Подключаем шаблоны с отключенным кэшем
templates = Jinja2Templates(directory="presentation/web/templates")
templates.env = jinja2.Environment(
    loader=jinja2.FileSystemLoader("presentation/web/templates"),
    autoescape=True,
    cache_size=0
)

# Инициализируем RAGService один раз при старте
rag_service = RAGService()

# Модели данных
class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime

class ChatSession(BaseModel):
    id: str
    title: str
    lab_name: Optional[str] = None
    messages: List[ChatMessage] = []
    created_at: datetime

class Question(BaseModel):
    chat_id: str
    message: str
    lab_name: Optional[str] = None

class Answer(BaseModel):
    response: str
    sources: List[str] = []

sessions = {}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Главная страница"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/chats")
async def get_chats():
    return list(sessions.values())

@app.post("/api/chats")
async def create_chat(lab_name: Optional[str] = None):
    chat_id = str(uuid.uuid4())
    session = ChatSession(
        id=chat_id,
        title=f"Чат {len(sessions) + 1}",
        lab_name=lab_name,
        created_at=datetime.now()
    )
    sessions[chat_id] = session
    return session

@app.post("/api/chats/{chat_id}/ask")
async def ask_question(chat_id: str, question: Question):
    """Задать вопрос в чате с использованием RAG"""
    if chat_id not in sessions:
        raise HTTPException(status_code=404, detail="Чат не найден")
    
    chat = sessions[chat_id]
    
    # Добавляем вопрос пользователя
    user_message = ChatMessage(
        role="user",
        content=question.message,
        timestamp=datetime.now()
    )
    chat.messages.append(user_message)
    
    logger.info(f"Вопрос в чате {chat_id}: {question.message}")
    logger.info(f"Лаборатория: {question.lab_name or chat.lab_name or 'общая'}")
    
    # Используем RAGService для получения ответа
    try:
        answer_text = rag_service.answer_question(question.message)
    except Exception as e:
        logger.error(f"Ошибка RAG: {e}")
        answer_text = f"⚠️ Ошибка при генерации ответа: {str(e)}"
    
    assistant_message = ChatMessage(
        role="assistant",
        content=answer_text,
        timestamp=datetime.now()
    )
    chat.messages.append(assistant_message)
    
    return Answer(
        response=answer_text,
        sources=["Источники будут добавлены позже"]
    )

@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    lab_name: str = Form(...)
):
    """Загрузить PDF файл для лаборатории"""
    logger.info(f"Файл: {file.filename}, размер: {file.size}, лаборатория: {lab_name}")
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Только PDF")
    
    upload_dir = f"data/uploads/{lab_name}"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = f"{upload_dir}/{file.filename}"
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    logger.info(f"Файл сохранён: {file_path}")
    
    # TODO: здесь будет индексация файла в Qdrant
    
    return {
        "message": "Файл успешно загружен",
        "filename": file.filename,
        "lab_name": lab_name,
        "status": "готов к обработке"
    }

@app.delete("/api/chats/{chat_id}")
async def delete_chat(chat_id: str):
    if chat_id in sessions:
        del sessions[chat_id]
        return {"message": "Чат удалён"}
    raise HTTPException(status_code=404, detail="Чат не найден")