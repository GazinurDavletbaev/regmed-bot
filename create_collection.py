from qdrant_client import QdrantClient
from qdrant_client.http import models

client = QdrantClient("localhost", port=6333)
collection_name = "med_docs"

# Удалим старую коллекцию, если есть (чтобы не было конфликтов)
client.delete_collection(collection_name)

# Создаём новую
client.create_collection(
    collection_name=collection_name,
    vectors_config=models.VectorParams(
        size=1024,
        distance=models.Distance.COSINE
    )
)

print(f"Коллекция '{collection_name}' создана")