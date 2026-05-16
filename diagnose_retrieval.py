"""诊断检索问题"""
from config import Config
from knowledge_base.loader import load_java_files, load_vue_files

# 1. 检查 AuthController 是否存在
print("=" * 60)
print("1. 检查 AuthController 文件是否存在")
print("=" * 60)

java_files = load_java_files(Config.BACKEND_PATH)
auth_files = []

for f in java_files:
    if 'AuthController' in f['source']:
        auth_files.append(f)
        print(f"✅ 找到: {f['source']}")
        # 检查内容中是否有 login
        if 'login' in f['content'].lower():
            print(f"   ✅ 内容包含 'login'")
        else:
            print(f"   ❌ 内容不包含 'login'")
        # 显示文件的前500字符
        print(f"\n   文件内容预览:")
        print(f"   {f['content'][:500]}...")
        print()

if not auth_files:
    print("❌ 未找到 AuthController.java 文件！")
    print("   请检查路径配置是否正确")

# 2. 测试向量检索
print("\n" + "=" * 60)
print("2. 测试向量检索")
print("=" * 60)

if Config.USE_VECTOR_RETRIEVAL:
    from knowledge_base.vector_retriever import VectorRetriever

    retriever = VectorRetriever()

    test_queries = [
        "登录功能是怎么实现的？",
        "login",
        "AuthController",
        "用户登录"
    ]

    for query in test_queries:
        print(f"\n查询: '{query}'")
        results = retriever.search(query, top_k=5)

        if results:
            for i, r in enumerate(results):
                print(f"  [{i + 1}] {r['file_name']} (相似度: {r['relevance_score']:.4f})")
                print(f"      路径: {r['source']}")
        else:
            print(f"  ❌ 没有找到结果")
else:
    from knowledge_base.indexer import CodeIndexer

    indexer = CodeIndexer()
    indexer.build_index(Config.FRONTEND_PATH, Config.BACKEND_PATH)

    test_queries = ["登录", "login", "AuthController"]

    for query in test_queries:
        print(f"\n查询: '{query}'")
        results = indexer.search(query, top_k=5)

        if results:
            for i, r in enumerate(results):
                file_name = r['source'].split('\\')[-1].split('/')[-1]
                print(f"  [{i + 1}] {file_name} (相关度: {r['relevance_score']})")
        else:
            print(f"  ❌ 没有找到结果")