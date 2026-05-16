"""
向量检索器 - 基于语义的代码检索
"""
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
import re
from typing import List, Dict, Optional
from config import Config

# 设置 HuggingFace 镜像
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'


class VectorRetriever:
    """基于向量数据库的语义检索器"""

    def __init__(self, persist_dir: str = None):
        self.persist_dir = persist_dir or Config.CHROMA_PERSIST_DIR
        self.model_name = "shibing624/text2vec-base-chinese"
        self.embedding_model = None
        self.client = None
        self.collection = None

        print(f"📥 初始化向量检索器...")
        print(f"   模型: {self.model_name}")

        # 加载嵌入模型
        try:
            from sentence_transformers import SentenceTransformer
            print(f"   从镜像下载模型: {self.model_name}")
            self.embedding_model = SentenceTransformer(self.model_name)
            print(f"   ✅ 模型加载成功")
        except Exception as e:
            print(f"   ❌ 模型加载失败: {e}")
            print(f"   提示: 请在 config.py 中设置 USE_VECTOR_RETRIEVAL = False")
            raise RuntimeError(f"向量模型加载失败: {e}")

        # 初始化 ChromaDB
        try:
            import chromadb
            from chromadb.config import Settings

            os.makedirs(self.persist_dir, exist_ok=True)
            self.client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=Settings(anonymized_telemetry=False)
            )

            # 获取或创建集合
            self.collection = self.client.get_or_create_collection(
                name="code_knowledge",
                metadata={"hnsw:space": "cosine"}
            )
            print(f"✅ 向量检索器初始化完成")
            print(f"   已有文档数: {self.collection.count()}")
        except Exception as e:
            print(f"   ❌ ChromaDB 初始化失败: {e}")
            raise

    def build_index(self, documents: List[Dict]):
        """构建向量索引"""
        if self.embedding_model is None or self.collection is None:
            raise RuntimeError("向量检索器未正确初始化")

        print(f"\n🔨 开始构建向量索引...")
        print(f"   待处理文档数: {len(documents)}")

        # 清空现有集合
        try:
            self.client.delete_collection("code_knowledge")
        except:
            pass
        self.collection = self.client.create_collection(
            name="code_knowledge",
            metadata={"hnsw:space": "cosine"}
        )

        # 配置代码分块器
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP,
            separators=["\nclass ", "\npublic ", "\nprivate ", "\nprotected ",
                        "\nfunction ", "\nconst ", "\nlet ", "\nvar ", "\n//", "\n", " ", ""]
        )

        all_chunks = []
        chunk_metadatas = []
        chunk_ids = []

        # 分割文档
        for idx, doc in enumerate(documents):
            content = doc["content"]
            source = doc["source"]
            doc_type = doc["type"]

            # 分割代码块
            chunks = text_splitter.split_text(content)

            for chunk_idx, chunk in enumerate(chunks):
                if len(chunk) > 2000:
                    chunk = chunk[:2000]

                chunk_id = f"{source}_{chunk_idx}".replace("/", "_").replace("\\", "_").replace(":", "_")
                all_chunks.append(chunk)
                chunk_metadatas.append({
                    "source": source,
                    "type": doc_type,
                    "file_name": source.split('/')[-1].split('\\')[-1],
                    "chunk_index": chunk_idx
                })
                chunk_ids.append(chunk_id)

            if (idx + 1) % 100 == 0:
                print(f"   已处理 {idx + 1}/{len(documents)} 个文件, 生成 {len(all_chunks)} 个片段")

        # 批量生成向量并存储
        print(f"\n   生成向量嵌入...")
        batch_size = 100
        for i in range(0, len(all_chunks), batch_size):
            batch_chunks = all_chunks[i:i + batch_size]
            batch_ids = chunk_ids[i:i + batch_size]
            batch_metadatas = chunk_metadatas[i:i + batch_size]

            # 生成向量
            embeddings = self.embedding_model.encode(batch_chunks).tolist()

            # 存入数据库
            self.collection.add(
                embeddings=embeddings,
                documents=batch_chunks,
                metadatas=batch_metadatas,
                ids=batch_ids
            )

            if (i + batch_size) % 500 == 0:
                print(f"   已存储 {i + len(batch_chunks)}/{len(all_chunks)} 个片段")

        print(f"\n✅ 向量索引构建完成!")
        print(f"   总片段数: {self.collection.count()}")
        return self

    def search(self, query: str, top_k: int = None) -> List[Dict]:
        """语义搜索"""
        if self.collection is None or self.embedding_model is None:
            print("⚠️ 向量检索器未正确初始化")
            return []

        if top_k is None:
            top_k = Config.RETRIEVAL_TOP_K

        if self.collection.count() == 0:
            print("⚠️ 向量库为空，请先构建索引")
            return []

        try:
            # 生成查询向量
            query_embedding = self.embedding_model.encode(query).tolist()

            # 搜索
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )

            # 格式化结果
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for doc, metadata, distance in zip(
                        results['documents'][0],
                        results['metadatas'][0],
                        results['distances'][0]
                ):
                    # 距离转分数（余弦距离越小越相似）
                    relevance_score = 1 - distance
                    formatted_results.append({
                        "content": doc,
                        "source": metadata.get("source", "未知"),
                        "type": metadata.get("type", "未知"),
                        "file_name": metadata.get("file_name", "未知"),
                        "relevance_score": relevance_score
                    })

            return formatted_results
        except Exception as e:
            print(f"检索失败: {e}")
            return []

    def similarity_search_with_score(self, query: str, k: int = None):
        """兼容原有接口"""
        results = self.search(query, k)

        class MockDocument:
            def __init__(self, page_content, metadata):
                self.page_content = page_content
                self.metadata = metadata

        return [(MockDocument(r["content"], {"source": r["source"], "type": r["type"]}),
                 r["relevance_score"]) for r in results]