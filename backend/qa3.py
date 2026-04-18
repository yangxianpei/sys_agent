from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType

# 1. 连接
connections.connect(host="localhost", port="19530")

# ========================
# 🔥 关键：删除旧表，重建正确的表（自动ID）
# ========================


# 2. 创建新表（支持自动生成ID，永远不重复）
fields = [
    # ✅ 主键：自动ID，你完全不用传
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
    # 向量字段 384 维
    FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=384),
    # 文本字段
    FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
    # 你自己的业务ID
    FieldSchema(name="idx", dtype=DataType.INT64),
]

schema = CollectionSchema(fields=fields)
col = Collection("agent", schema=schema)
print("✅ 新表创建成功（自动ID）")

# 3. 创建索引（必须建索引才能加载）
index_params = {"index_type": "FLAT", "metric_type": "COSINE"}
col.create_index("vector", index_params)
col.load()
print("✅ 索引创建完成，集合已加载")

# ========================
# ✅ 插入数据（不传 id！！！）
# ========================
embeded = []

# 你的测试文本
text_list = [
    "人工智能正在改变各行各业的工作方式",
    "向量数据库适合存储高维特征用于快速检索",
    "RAG技术通过检索增强让大模型回答更准确",
    "Milvus是目前最流行的开源向量数据库之一",
    "文本向量化可以把文字转为计算机可理解的向量",
    "语义检索能理解文字含义而不只是关键词匹配",
    "自动生成ID可以避免数据重复插入的问题",
    "元数据可以用来存储业务自定义信息",
    "数据清洗是AI应用中非常重要的预处理步骤",
    "向量相似度检索是智能问答系统的核心能力",
]

# 构造数据（绝对不带 id）
for idx, text in enumerate(text_list):
    embeded.append(
        {
            "vector": [0.1] * 384,  # 替换成你的 self.embed_process(text)
            "text": text,
            "idx": idx,  # 你自己的ID
        }
    )

# 插入
col.insert(embeded)
print("✅ 插入成功（Milvus自动生成ID）")

# ========================
# 查看所有数据
# ========================
result = col.query(expr="id >= 0", output_fields=["id", "text", "idx"])
print("\n📊 最终数据：")
for item in result:
    print(item)
