from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import os

# 1. Подключаемся к Qdrant
client = QdrantClient("localhost", port=6333)
collection_name = "med_docs"

# 2. Загружаем модель эмбеддингов (скачается один раз, потом будет локально)
print("Загружаем модель...")
model = SentenceTransformer('intfloat/multilingual-e5-large')

# 3. Подготовим тестовый текст (пока просто строка, позже будем читать из файла)
text = """
ГОСТ Р 52623.3-2015 Технологии выполнения простых медицинских услуг. 
Манипуляции сестринского ухода. Настоящий стандарт устанавливает требования 
к технологиям выполнения простых медицинских услуг.
Стерилизация инструментов должна проводиться в соответствии с СанПиН 2.1.3.2630-10.
Температура хранения стерильных материалов: от +5 до +25 градусов Цельсия.
Влажность: не более 70%.
Срок хранения стерильных материалов в закрытой упаковке — 3 суток.
"""

# 4. Разбиваем на чанки (просто на предложения для теста)
chunks = text.strip().split('\n')
print(f"Получили {len(chunks)} чанков")

# 5. Создаём эмбеддинги для всех чанков
print("Создаём эмбеддинги...")
vectors = model.encode(chunks).tolist()

# 6. Готовим точки для загрузки в Qdrant
from qdrant_client.http import models

points = []
for idx, (chunk, vector) in enumerate(zip(chunks, vectors)):
    points.append(
        models.PointStruct(
            id=idx,
            vector=vector,
            payload={"text": chunk, "source": "test_doc.txt"}
        )
    )

# 7. Заливаем
print("Заливаем в Qdrant...")
client.upsert(
    collection_name=collection_name,
    points=points
)

print("Готово!")