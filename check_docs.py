from qdrant_client import QdrantClient
import re

client = QdrantClient("localhost", port=6333)
collection_name = "med_docs"

# Проверим, сколько точек имеют правильный gost_number
results = client.scroll(
    collection_name=collection_name,
    limit=100,
    with_payload=True
)

gost_counts = {}
for point in results[0]:
    gost = point.payload.get("gost_number")
    if gost:
        gost_counts[gost] = gost_counts.get(gost, 0) + 1
    else:
        print(f"Точка {point.id} без gost_number")

print("Статистика по номерам ГОСТов:")
for gost, count in gost_counts.items():
    print(f"{gost}: {count} чанков")