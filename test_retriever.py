"""
测试知识库检索器
运行方式: python test_retriever.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from knowledge_base.indexer import CodeIndexer
from agent.retriever import KnowledgeRetriever
from config import Config


def test_retriever():
    print("=" * 60)
    print("知识库检索器测试")
    print("=" * 60)

    # 步骤1: 构建索引
    print("\n[步骤1] 构建关键词索引...")
    indexer = CodeIndexer()
    vector_store = indexer.build_index(Config.FRONTEND_PATH, Config.BACKEND_PATH)

    if not vector_store or len(vector_store.documents) == 0:
        print("   ❌ 索引构建失败")
        return False

    print(f"   ✅ 索引构建成功，共 {len(vector_store.documents)} 个文件")

    # 步骤2: 创建检索器
    print("\n[步骤2] 创建检索器...")
    retriever = KnowledgeRetriever(vector_store)
    print("   ✅ 检索器创建成功")

    # 步骤3: 测试检索
    print("\n[步骤3] 测试检索功能...")
    test_questions = ["用户登录", "login", "用户管理"]

    for question in test_questions:
        print(f"\n   问题: {question}")
        results = retriever.retrieve(question, top_k=3)
        print(f"   检索到: {len(results)} 个结果")
        for r in results[:3]:
            name = r['source'].split('\\')[-1] if '\\' in r['source'] else r['source'].split('/')[-1]
            print(f"      - {name} (相关度: {r['relevance_score']})")

    # 步骤4: 测试格式化
    print("\n[步骤4] 测试格式化...")
    results = retriever.retrieve("用户登录", top_k=2)
    formatted = retriever.format_context(results)
    print(f"   格式化后长度: {len(formatted)} 字符")
    print("\n   预览:")
    print("-" * 40)
    print(formatted[:500])
    print("-" * 40)

    print("\n✅ 检索器测试完成")
    return True


if __name__ == "__main__":
    test_retriever()