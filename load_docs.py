import os
import re
from pathlib import Path
import pdfplumber
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from qdrant_client.http import models

# === Конфигурация ===
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "med_docs"
DOCS_FOLDER = "./gost_pdfs"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
BATCH_SIZE = 100

# === Подключения ===
client = QdrantClient(QDRANT_HOST, port=QDRANT_PORT)
model = SentenceTransformer('intfloat/multilingual-e5-large')

# === Проверка/создание коллекции ===
def ensure_collection():
    """Создаёт коллекцию, если она не существует."""
    collections = client.get_collections().collections
    exists = any(c.name == COLLECTION_NAME for c in collections)
    if not exists:
        print(f"Коллекция {COLLECTION_NAME} не найдена, создаю...")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=1024,  # для multilingual-e5-large размерность 1024
                distance=models.Distance.COSINE
            )
        )
        print("Коллекция создана.")
    else:
        print("Коллекция уже существует.")

# === Вспомогательные функции ===
def normalize_text(text):
    """Очищает текст от мусора и нормализует тире."""
    if not text:
        return ""
    # Удаляем непечатные символы (оставляем русские, английские буквы, цифры, пробелы, знаки препинания)
    text = re.sub(r'[^\x20-\x7E\u0400-\u04FF\n\r\s\.\,\:\;\(\)\[\]\-]', '', text)
    # Заменяем длинное/короткое тире на обычный дефис
    text = re.sub(r'[–—]', '-', text)
    # Убираем множественные пробелы
    text = re.sub(r'\s+', ' ', text)
    return text

def extract_gost_number_from_pdf(pdf_path):
    """Извлекает номер ГОСТа из первых страниц PDF (более надёжно)."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages[:5]:
                text = page.extract_text()
                if not text:
                    continue
                text = normalize_text(text)
                # Поиск по шаблону ГОСТ XXXX-XXXX
                match = re.search(r'ГОСТ\s*(\d{4,5})[–—\s]*(\d{4})', text)
                if match:
                    return f"{match.group(1)}-{match.group(2)}"
                # Альтернативный шаблон: просто два числа через дефис (может быть номером)
                match = re.search(r'(\d{4,5})-(\d{4})', text)
                if match:
                    return f"{match.group(1)}-{match.group(2)}"
    except Exception as e:
        print(f"Ошибка при извлечении номера из {pdf_path}: {e}")
    return Path(pdf_path).stem  # запасной вариант – имя файла

def extract_text_from_pdf(path):
    """Извлекает текст с помощью pdfplumber (чище, чем pypdf)."""
    text = ""
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Ошибка при извлечении текста из {path}: {e}")
    return normalize_text(text)

def split_into_chunks(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Разбивает текст на чанки по словам с перекрытием."""
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

# === Основной цикл ===
def main():
    ensure_collection()
    
    # Получаем актуальное количество точек в коллекции (для уникальных ID)
    collection_info = client.get_collection(COLLECTION_NAME)
    current_count = collection_info.points_count or 0

    files = list(Path(DOCS_FOLDER).glob("*.pdf"))
    if not files:
        print("В папке нет PDF файлов.")
        return
    print(f"Найдено PDF файлов: {len(files)}")

    for file_path in files:
        print(f"\nОбработка: {file_path.name}")
        
        # Извлекаем номер ГОСТа
        gost_number = extract_gost_number_from_pdf(file_path)
        print(f"  Номер ГОСТа: {gost_number}")
        
        # Извлекаем текст
        text = extract_text_from_pdf(file_path)
        if not text.strip():
            print(f"  ❌ Текст не извлечён, пропускаю")
            continue
        
        # Разбиваем на чанки
        chunks = split_into_chunks(text)
        print(f"  Чанков: {len(chunks)}")
        
        # Создаём эмбеддинги
        vectors = model.encode(chunks).tolist()
        
        # Готовим точки с payload
        points = []
        for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
            points.append(
                models.PointStruct(
                    id=current_count + i,
                    vector=vector,
                    payload={
                        "text": chunk,
                        "source": file_path.name,
                        "gost_number": gost_number
                    }
                )
            )
        
        # Загружаем батчами
        for batch_start in range(0, len(points), BATCH_SIZE):
            batch = points[batch_start:batch_start+BATCH_SIZE]
            client.upsert(collection_name=COLLECTION_NAME, points=batch)
            print(f"  Загружено {batch_start + len(batch)} / {len(points)}")
        
        # Увеличиваем счётчик для следующих файлов
        current_count += len(points)
        print(f"  ✅ Файл {file_path.name} обработан")

    print("\n🎉 Все файлы обработаны!")

if __name__ == "__main__":
    main()