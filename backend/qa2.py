from pymilvus import MilvusClient
from sentence_transformers import SentenceTransformer

# ======================
# 1. embedding 模型
# ======================
model = SentenceTransformer(r"D:\test\model\all-MiniLM-L6-v2")


def embed(text):
    return model.encode(text).tolist()


# ======================
# 2. 连接 Milvus（Docker）
# ======================
client = MilvusClient(uri="http://localhost:19530")

collection_name = "agent"

# 如果不存在就创建
if not client.has_collection(collection_name):
    client.create_collection(collection_name=collection_name, dimension=384)

# ======================
# 3. 准备数据
# ======================
texts = [
    "Milvus 是一个向量数据库，用于存储 embedding",
    "向量数据库可以做语义搜索，而不是关键词搜索",
    "RAG 是 Retrieval Augmented Generation",
    "LangChain 可以快速构建 AI 应用",
]

data = []
for i, text in enumerate(texts):
    data.append({"id": i, "vector": embed(text), "text": text})

# client.insert(collection_name, data)

# client.load_collection(collection_name)
stats = client.get_collection_stats(collection_name="docs")
print(f"集合总数据量：{stats['row_count']}")  # 应等于30
print(client.describe_collection("docs"))


# ======================
# 4. 查询
# ======================
def search(query):
    query_vec = embed(query)
    # print(query_vec)
    results = client.search(
        collection_name=collection_name,
        data=[query_vec],
        limit=3,
        output_fields=["text"],
    )

    print("\n🔍 查询：", query)
    print("📌 最相关内容：")

    for r in results[0]:
        print("-", r["entity"]["text"])


# ======================
# 5. 测试
# ======================
# search("什么是向量数据库")
search("RAG 是什么")
