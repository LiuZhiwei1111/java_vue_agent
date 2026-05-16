# test_indexer.py
from knowledge_base.indexer import CodeIndexer
from config import Config

print("测试索引器...")
indexer = CodeIndexer()

# 测试加载索引（如果已存在）
try:
    vector_store = indexer.load_index()
    print("✅ 索引加载成功")
except Exception as e:
    print(f"未找到索引，需要构建: {e}")
    print("正在构建新索引...")
    vector_store = indexer.build_index(Config.FRONTEND_PATH, Config.BACKEND_PATH)
    print("✅ 索引构建成功")

print("测试检索...")
results = vector_store.similarity_search("get", k=2)
print(f"检索到 {len(results)} 个结果")
for r in results:
    print(f"  - {r.metadata.get('source', '未知')[:50]}")