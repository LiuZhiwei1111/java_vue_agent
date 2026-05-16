"""
关键词索引器 - 无需网络，使用关键词匹配进行代码检索
支持中英文混合搜索（优化版）
"""
import os
import re
from pathlib import Path
from collections import Counter
from config import Config


class CodeIndexer:
    """基于关键词的代码检索器（支持中文搜索）"""

    def __init__(self):
        print("📥 初始化关键词索引器...")
        self.documents = []
        self.inverted_index = {}
        self.doc_scores_cache = {}  # 缓存常用查询的搜索结果
        print("✅ 索引器初始化完成")

    def build_index(self, frontend_path, backend_path):
        """构建关键词索引"""
        print("📂 开始构建关键词索引...")
        all_docs = []

        # ========== 1. 加载 Java 文件 ==========
        print("  正在扫描 Java 文件...")
        java_count = 0
        for path in Path(backend_path).rglob("*.java"):
            if "test" in str(path).lower():
                continue
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                all_docs.append({
                    "content": content,
                    "source": str(path),
                    "type": "java"
                })
                java_count += 1
                if java_count % 200 == 0:
                    print(f"      已扫描 {java_count} 个 Java 文件...")
            except Exception as e:
                print(f"      跳过 {path}: {e}")

        print(f"      ✅ 加载了 {java_count} 个 Java 文件")

        # ========== 2. 加载 Vue 文件 ==========
        print("  正在扫描 Vue 文件...")
        vue_count = 0
        for path in Path(frontend_path).rglob("*.vue"):
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                all_docs.append({
                    "content": content,
                    "source": str(path),
                    "type": "vue"
                })
                vue_count += 1
                if vue_count % 200 == 0:
                    print(f"      已扫描 {vue_count} 个 Vue 文件...")
            except Exception as e:
                print(f"      跳过 {path}: {e}")

        print(f"      ✅ 加载了 {vue_count} 个 Vue 文件")

        self.documents = all_docs
        print(f"\n  📊 共加载 {len(self.documents)} 个文件")

        # ========== 3. 构建倒排索引 ==========
        print("\n  🔄 正在构建倒排索引（提取关键词）...")
        self._build_inverted_index()
        print(f"  ✅ 倒排索引构建完成，共 {len(self.inverted_index)} 个关键词")

        # 清空缓存
        self.doc_scores_cache = {}
        return self

    def _build_inverted_index(self):
        """构建倒排索引 - 增加文件名和路径的权重"""
        self.inverted_index = {}

        english_pattern = re.compile(r'[a-zA-Z_][a-zA-Z0-9_]{2,}')
        chinese_pattern = re.compile(r'[\u4e00-\u9fa5]{2,6}')

        for idx, doc in enumerate(self.documents):
            content = doc["content"].lower()
            source = doc["source"]

            # 提取文件名和路径中的关键词（重要！）
            file_name = source.split('/')[-1].split('\\')[-1].replace('.java', '').replace('.vue', '').lower()
            # 提取路径中的模块名
            path_parts = source.replace('\\', '/').split('/')
            module_names = [p for p in path_parts if 'module' in p or 'biz' in p or 'api' in p]

            # ========== 新增：为文件名和模块名给予高权重 ==========
            # 文件名中的词（如 AuthController → auth, controller）
            file_words = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]{2,}', file_name)
            # 模块名
            module_words = []
            for module in module_names:
                module_words.extend(re.findall(r'[a-zA-Z_][a-zA-Z0-9_]{2,}', module.lower()))

            # 提取内容关键词
            english_keywords = english_pattern.findall(content)
            chinese_keywords = chinese_pattern.findall(content)

            # 合并关键词，并为文件名/模块名关键词给予更高权重
            all_keywords = english_keywords + chinese_keywords
            word_counts = Counter(all_keywords)

            # 为文件名关键词增加权重（出现次数+10，确保优先级）
            for word in file_words:
                word_counts[word] += 10
            for word in module_words:
                word_counts[word] += 5

            # 修改过滤条件：降低门槛
            for word, count in word_counts.items():
                if count >= 1:  # 改为出现1次就索引
                    if word not in self.inverted_index:
                        self.inverted_index[word] = {}
                    # 使用加权后的次数
                    self.inverted_index[word][idx] = self.inverted_index[word].get(idx, 0) + count

            if (idx + 1) % 500 == 0:
                print(f"      已处理 {idx + 1}/{len(self.documents)} 个文件")

    def search(self, query: str, top_k: int = None):
        """
        搜索相关代码（优化版：增加缓存和提前终止）
        """
        if top_k is None:
            top_k = Config.RETRIEVAL_TOP_K

        if not self.documents:
            return []

        # 清理查询
        query = query.strip()
        if len(query) < 2:
            return []

        # 检查缓存
        cache_key = f"{query}_{top_k}"
        if cache_key in self.doc_scores_cache:
            return self.doc_scores_cache[cache_key]

        # ========== 1. 提取并扩展关键词 ==========
        query_lower = query.lower()

        # 英文关键词
        english_keywords = set(re.findall(r'[a-zA-Z_][a-zA-Z0-9_]{2,}', query_lower))

        # 中文关键词
        chinese_keywords = set(re.findall(r'[\u4e00-\u9fa5]{2,}', query))

        # 中英文映射表（精简版，提高速度）
        keyword_mapping = {
            "登录": ["login", "signin"],
            "用户": ["user"],
            "密码": ["password"],
            "查询": ["select", "find", "get"],
            "添加": ["add", "insert", "create"],
            "删除": ["delete", "remove"],
            "更新": ["update", "modify"],
            "接口": ["api", "controller"],
            "配置": ["config"],
        }

        # 扩展关键词
        expanded_keywords = set(english_keywords)
        for ch in chinese_keywords:
            expanded_keywords.add(ch)
            if ch in keyword_mapping:
                for mapped in keyword_mapping[ch]:
                    expanded_keywords.add(mapped)

        keywords = list(expanded_keywords)

        if not keywords:
            return []

        # ========== 2. 快速筛选候选文档 ==========
        # 只包含至少包含一个关键词的文档
        candidate_docs = set()
        for kw in keywords:
            if kw in self.inverted_index:
                candidate_docs.update(self.inverted_index[kw].keys())

        if not candidate_docs:
            return []

        # ========== 3. 计算得分（只计算候选文档）==========
        scores = {}
        for doc_id in candidate_docs:
            score = 0
            for kw in keywords:
                if kw in self.inverted_index and doc_id in self.inverted_index[kw]:
                    score += self.inverted_index[kw][doc_id]
            if score > 0:
                scores[doc_id] = score

        if not scores:
            return []

        # ========== 4. 排序并返回 ==========
        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        results = []
        for doc_id, score in sorted_docs:
            doc = self.documents[doc_id]
            results.append({
                "content": doc["content"],
                "source": doc["source"],
                "type": doc["type"],
                "relevance_score": score
            })

        # 缓存结果（最多缓存100个查询）
        if len(self.doc_scores_cache) < 100:
            self.doc_scores_cache[cache_key] = results

        return results

    def similarity_search(self, query: str, k: int = None):
        """兼容 Chroma 接口"""
        return self.search(query, k)

    def similarity_search_with_score(self, query: str, k: int = None):
        """兼容 Chroma 接口"""
        results = self.search(query, k)

        class MockDocument:
            def __init__(self, page_content, metadata):
                self.page_content = page_content
                self.metadata = metadata

        return [(MockDocument(r["content"], {"source": r["source"], "type": r["type"]}),
                 r["relevance_score"]) for r in results]

    def add_documents(self, documents):
        """兼容 Chroma 接口"""
        print("⚠️ 关键词索引暂不支持增量添加")

    def persist(self):
        """兼容 Chroma 接口"""
        pass

    def load_index(self):
        """加载已有索引"""
        raise NotImplementedError("请使用 build_index() 重新构建索引")