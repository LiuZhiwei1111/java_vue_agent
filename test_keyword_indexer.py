# test_keyword_indexer.py - 放在项目根目录
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from knowledge_base.indexer import CodeIndexer
from config import Config

print("=" * 60)
print("关键词索引器测试")
print("=" * 60)

# 1. 创建索引器
print("\n📌 第1步：创建索引器")
indexer = CodeIndexer()

# 2. 构建索引
print("\n📌 第2步：构建索引（这可能需要几分钟）")
print(f"   Java路径: {Config.BACKEND_PATH}")
print(f"   Vue路径: {Config.FRONTEND_PATH}")
print("")

vector_store = indexer.build_index(Config.FRONTEND_PATH, Config.BACKEND_PATH)

# 3. 测试搜索
print("\n📌 第3步：测试搜索功能")
test_queries = [
    "用户登录",
    "login",
    "@PostMapping",
    "axios请求",
    "RestController",
    "数据库连接"
]

for query in test_queries:
    print(f"\n   问题: '{query}'")
    results = vector_store.search(query, top_k=3)
    print(f"   找到 {len(results)} 个结果")
    for i, r in enumerate(results, 1):
        file_name = r['source'].split('\\')[-1] if '\\' in r['source'] else r['source'].split('/')[-1]
        print(f"      {i}. {file_name} (相关度: {r['relevance_score']})")

# 4. 测试与原有代码的兼容性
print("\n📌 第4步：测试兼容性")
print("   测试 similarity_search 方法...")
results = vector_store.similarity_search("登录", k=2)
print(f"   结果数: {len(results)}")

print("\n✅ 索引器测试完成！")