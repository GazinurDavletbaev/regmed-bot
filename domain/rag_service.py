import os
import requests
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
load_dotenv()  # Загружаем переменные окружения из .env

class RAGService:
    """Сервис для поиска по документам (RAG) и генерации ответов через LLM."""

    def __init__(
        self,
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        collection_name: str = "med_docs",
        embedding_model_name: str = "intfloat/multilingual-e5-large",
    ):
        """
        Инициализация подключений.
        Модель SentenceTransformer загружается один раз и сохраняется в памяти.
        """
        self.qdrant_client = QdrantClient(qdrant_host, port=qdrant_port)
        self.collection_name = collection_name
        self.embedding_model = SentenceTransformer(embedding_model_name)
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.deepseek_api_key:
            print("⚠️  ВНИМАНИЕ: DEEPSEEK_API_KEY не задан в .env")

    def search_docs(self, query: str, top_k: int = 5) -> list[str]:
        """
        Преобразует запрос в вектор, ищет похожие чанки в Qdrant,
        возвращает список текстов найденных чанков.
        """
        # Создаём эмбеддинг запроса
        query_vector = self.embedding_model.encode(query).tolist()

        # Выполняем поиск
        results = self.qdrant_client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k,
        ).points

        # Извлекаем текст из payload'а (в наших данных поле называется 'text')
        chunks = [hit.payload.get("text", "") for hit in results if hit.payload]
        return chunks

    def ask_deepseek(self, question: str, context_chunks: list[str]) -> str:
        """
        Формирует промпт из контекста и вопроса, отправляет в DeepSeek API,
        возвращает ответ.
        """
        if not self.deepseek_api_key:
            return "❌ API-ключ DeepSeek не настроен. Обратитесь к администратору."

        if not context_chunks:
            return "🤷‍♂️ Не удалось найти информацию по вашему запросу в базе знаний."

        # Склеиваем чанки в один контекст
        context = "\n\n---\n\n".join(context_chunks)

        # Формируем промпт
        prompt = f"""Ты — ассистент, который отвечает на вопросы, используя только предоставленные документы.
Отвечай строго по фактам из документов. Если ответа в документах нет — так и скажи.

Документы:
{context}

Вопрос пользователя: {question}

Ответ:"""

        headers = {
            "Authorization": f"Bearer {self.deepseek_api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "Ты полезный ассистент, отвечающий строго по документам."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,   # минимум творчества, чтобы не выдумывал
            "max_tokens": 1000,
        }

        try:
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=60,
            )
            response.raise_for_status()
            answer = response.json()["choices"][0]["message"]["content"]
            return answer.strip()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при вызове DeepSeek API: {e}")
            return f"⚠️ Ошибка при обращении к AI: {e}"
        except (KeyError, IndexError) as e:
            print(f"Неожиданный формат ответа от DeepSeek API: {e}")
            return "⚠️ Получен некорректный ответ от AI."

    # Для удобства можно объединить поиск и генерацию
    def answer_question(self, question: str, top_k: int = 5) -> str:
        """Полный пайплайн: поиск + генерация ответа."""
        chunks = self.search_docs(question, top_k=top_k)
        return self.ask_deepseek(question, chunks)