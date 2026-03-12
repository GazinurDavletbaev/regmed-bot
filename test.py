from qdrant_client import QdrantClient
import re

client = QdrantClient("localhost", port=6333)
collection_name = "med_docs"

# Получаем все чанки из этого файла
results = client.scroll(
    collection_name=collection_name,
    limit=100,
    with_payload=True
)

for point in results[0]:
    src = point.payload.get("source", "")
    if "62845.pdf" in src:
        text = point.payload.get("text", "")
        # Поиск номера ГОСТа в тексте чанка
        match = re.search(r'ГОСТ\s*(\d+)[–—]?\s*(\d+)', text)
        if match:
            print(f"Чанк {point.id}: найден ГОСТ {match.group(1)}-{match.group(2)}")
        else:
            print(f"Чанк {point.id}: номер ГОСТа не найден")