from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

client = QdrantClient("localhost", port=6333)
collection_name = "med_docs"
model = SentenceTransformer('intfloat/multilingual-e5-large')

query = "какие условия хранения стерильных материалов?"
print(f"Запрос: {query}")

query_vector = model.encode(query).tolist()

# Используем query_points вместо search
search_result = client.query_points(
    collection_name=collection_name,
    query=query_vector,
    limit=3
)

# Результаты лежат в search_result.points
results = search_result.points

print("\nНайденные чанки:")
if not results:
    print("Ничего не найдено. Возможно, коллекция пуста.")
else:
    for hit in results:
        print(f"Оценка: {hit.score:.4f}")
        print(f"Текст: {hit.payload['text']}")
        print("-" * 50)