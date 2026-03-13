from qdrant_client import QdrantClient

client = QdrantClient("localhost", port=6333)
results = client.scroll(
    collection_name="med_docs",
    limit=200,
    with_payload=True
)

for point in results[0]:
    print(f"Точка {point.id}: gost_number = {point.payload.get('gost_number', 'НЕТ')}")