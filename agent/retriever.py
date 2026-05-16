"""
知识库检索器
作用：接收用户问题，从向量库中找出最相关的代码块
"""
from config import Config


class KnowledgeRetriever:
    def __init__(self, vector_store):
        self.vector_store = vector_store

    def retrieve(self, question: str, top_k: int = None):
        if top_k is None:
            top_k = Config.RETRIEVAL_TOP_K

        if self.vector_store is None:
            print("警告: 检索器未初始化")
            return []

        try:
            if hasattr(self.vector_store, 'search'):
                results = self.vector_store.search(question, top_k)
            else:
                results = self.vector_store.similarity_search_with_score(question, k=top_k)
                formatted = []
                for doc, score in results:
                    if score > 1.2:
                        continue
                    formatted.append({
                        "content": doc.page_content,
                        "source": doc.metadata.get("source", "未知"),
                        "type": doc.metadata.get("type", "未知"),
                        "relevance_score": score
                    })
                return formatted
            return results
        except Exception as e:
            print(f"检索失败: {e}")
            return []

    def format_context(self, results):
        if not results or len(results) == 0:
            return "未在项目代码中找到相关内容。\n\n提示：请确保已经运行索引构建。"

        context_parts = []

        for i, r in enumerate(results[:3]):
            if '\\' in r['source']:
                file_name = r['source'].split('\\')[-1]
            else:
                file_name = r['source'].split('/')[-1]

            context_parts.append(f"""
            ### [{i+1}] 文件: {file_name}
            **完整路径:** `{r['source']}`
            **文件类型:** {r['type']}
            **相关度:** {r['relevance_score']}
            {r['type']} {r['content'][:800]} """)
            header = """## 项目代码上下文（来自知识库检索）
            以下是与你问题相关的项目代码片段：
            """

        return header + "\n".join(context_parts)

    def retrieve_and_format(self, question: str, top_k: int = None):
        """一站式方法：检索并格式化"""
        raw_results = self.retrieve(question, top_k)
        formatted_context = self.format_context(raw_results)
        return formatted_context, raw_results