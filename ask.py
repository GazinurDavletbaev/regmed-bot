from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import requests
import json

# --- Конфигурация ---
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "med_docs"
DEEPSEEK_API_KEY = "sk-dbf930d6c22f43cda8f892a458d4e336"  # замени на свой ключ
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL_NAME = "intfloat/multilingual-e5-large"

# --- Подключения ---
client = QdrantClient(QDRANT_HOST, port=QDRANT_PORT)
model = SentenceTransformer(MODEL_NAME)

def search_docs(query, top_k=5):
    """Поиск похожих чанков в Qdrant"""
    query_vector = model.encode(query).tolist()
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=top_k
    ).points
    return [hit.payload['text'] for hit in results]

def ask_deepseek(query, context_chunks):
    """Отправка запроса в DeepSeek с контекстом"""
    context = "\n\n".join(context_chunks)
    prompt = f"""Ты ассистент, который отвечает на вопросы, используя только предоставленный контекст.
Контекст:
{context}

Вопрос: {query}

Ответь на вопрос на основе контекста. Если ответа нет в контексте, скажи, что не знаешь."""
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "Ты полезный ассистент, отвечающий на основе документов."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1  # низкая температура = меньше фантазий
    }
    
    response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data)
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content']

# --- Основной цикл ---
if __name__ == "__main__":
    query = input("Введите вопрос: ")
    print("Ищу в базе знаний...")
    chunks = search_docs(query)
    
    print(f"Найдено {len(chunks)} релевантных фрагментов.")
    print("=" * 50)
    
    print("Генерирую ответ...")
    answer = ask_deepseek(query, chunks)
    print("\nОтвет:\n", answer)