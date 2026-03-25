import os
import re
import json
import requests
from pathlib import Path
import pdfplumber
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from qdrant_client.http import models
import uuid

# === Конфигурация ===
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "med_docs"
GOST_PDFS = Path("C:/Users/user/gost_pdfs")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-8532345d813c4b01aac9955dc2303548")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
BATCH_SIZE = 100

# === Подключения ===
client = QdrantClient(QDRANT_HOST, port=QDRANT_PORT)
model = SentenceTransformer('intfloat/multilingual-e5-large')

# === Извлечение метаданных из первой страницы через DeepSeek ===
def extract_metadata_from_first_page(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if not pdf.pages:
                return {}
            first_page_text = pdf.pages[0].extract_text() or ""
            if not first_page_text:
                return {}
    except Exception as e:
        print(f"  ❌ Ошибка чтения первой страницы: {e}")
        return {}
    
    prompt = f"""Ты — ассистент, который извлекает метаданные из текста первой страницы ГОСТа.
Верни только JSON без пояснений. Если какое-то поле не найдено, оставь пустую строку.

Извлеки:
- gost_number (полный номер, например "ГОСТ 31336-2006")
- title (полное название стандарта)
- year (год принятия, только число)
- status (действует / заменён, если понятно из текста)
- iso_reference (ISO-ссылка, например "ИСО 2151:2004")

Текст страницы:
{first_page_text[:2000]}
"""
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "Ты — помощник для извлечения метаданных из ГОСТов. Отвечай только JSON."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1
    }
    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        start = content.find('{')
        end = content.rfind('}') + 1
        if start != -1 and end != 0:
            content = content[start:end]
        return json.loads(content)
    except Exception as e:
        print(f"  ❌ Ошибка DeepSeek: {e}")
        return {}

# === Нормализация текста ===
def normalize_text(text):
    if not text:
        return ""
    text = re.sub(r'[^\x20-\x7E\u0400-\u04FF\n\r\s\.\,\:\;\(\)\[\]\-]', '', text)
    text = re.sub(r'[–—]', '-', text)
    text = re.sub(r'\s+', ' ', text)
    return text

# === Извлечение всего текста из PDF ===
def extract_full_text(pdf_path):
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"  ❌ Ошибка чтения PDF: {e}")
    return normalize_text(text)

# === Разбивка на чанки ===
def split_into_chunks(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    words = text.split()
    if not words:
        return []
    chunks = []
    step = size - overlap
    for i in range(0, len(words), step):
        chunk = " ".join(words[i:i+size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks

# === Создание коллекции ===
def ensure_collection():
    collections = client.get_collections().collections
    exists = any(c.name == COLLECTION_NAME for c in collections)
    if not exists:
        print(f"Создаю коллекцию {COLLECTION_NAME}...")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=1024,
                distance=models.Distance.COSINE
            )
        )
        print("✅ Коллекция создана")
    else:
        print("✅ Коллекция уже существует")

# === Основной процесс (один файл за раз) ===
def process_one_file(file_path):
    print(f"\n📄 Обрабатываю: {file_path.name}")
    
    # Шаг 1: извлекаем метаданные из первой страницы
    print("  🔍 Извлекаю метаданные...")
    metadata = extract_metadata_from_first_page(file_path)
    gost_number = metadata.get("gost_number", "")
    
    # Если номер не нашёлся — пробуем из имени файла
    if not gost_number:
        match = re.search(r'ГОСТ\s*(\d{4,5})-(\d{4})', file_path.stem)
        if match:
            gost_number = f"{match.group(1)}-{match.group(2)}"
        else:
            gost_number = file_path.stem
    
    print(f"  📌 Номер ГОСТа: {gost_number}")
    print(f"  📌 Название: {metadata.get('title', 'не указано')}")
    
    # Шаг 2: извлекаем весь текст PDF
    print("  📖 Извлекаю текст...")
    full_text = extract_full_text(file_path)
    if not full_text.strip():
        print("  ❌ Текст не извлечён, пропускаю файл")
        return False
    
    # Шаг 3: разбиваем на чанки
    print("  ✂️ Разбиваю на чанки...")
    chunks = split_into_chunks(full_text)
    print(f"  📦 Получено чанков: {len(chunks)}")
    
    if not chunks:
        print("  ❌ Нет чанков для загрузки")
        return False
    
    # Шаг 4: генерируем эмбеддинги
    print("  🧠 Генерирую эмбеддинги...")
    vectors = model.encode(chunks).tolist()
    
    # Шаг 5: загружаем в Qdrant
    print("  💾 Загружаю в Qdrant...")
    points = []
    for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
        points.append(
            models.PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "text": chunk,
                    "source": file_path.name,
                    "gost_number": gost_number,
                    "title": metadata.get("title", ""),
                    "year": metadata.get("year", ""),
                    "status": metadata.get("status", ""),
                    "iso_reference": metadata.get("iso_reference", ""),
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
            )
        )
    
    # Загружаем батчами
    for batch_start in range(0, len(points), BATCH_SIZE):
        batch = points[batch_start:batch_start+BATCH_SIZE]
        client.upsert(collection_name=COLLECTION_NAME, points=batch)
        print(f"    Загружено {batch_start + len(batch)} / {len(points)}")
    
    print(f"  ✅ {file_path.name} успешно обработан")
    return True

# === Главная функция ===
def main():
    ensure_collection()
    
    files = sorted(GOST_PDFS.glob("*.pdf"))
    if not files:
        print("❌ В папке нет PDF файлов")
        return
    
    print(f"Найдено PDF: {len(files)}")
    
    for file_path in files:
        try:
            process_one_file(file_path)
        except Exception as e:
            print(f"  ❌ Ошибка при обработке {file_path.name}: {e}")
            continue
    
    print("\n🎉 Все файлы обработаны!")

if __name__ == "__main__":
    main()