import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ========== API配置 ==========
    ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY")

    # ========== 知识库配置 ==========
    CHROMA_PERSIST_DIR = "./data/chroma_db"  # 向量数据库存储路径
    CHUNK_SIZE = 500  # 代码分块大小（字符数）
    CHUNK_OVERLAP = 50  # 分块重叠大小
    RETRIEVAL_TOP_K = 5  # 每次检索返回的代码块数量

    # ========== 检索模式配置 ==========
    RETRIEVAL_MODE = "vector"  # 可选: "keyword"(关键词), "vector"(向量), "hybrid"(混合)
    USE_VECTOR_RETRIEVAL = True  # 是否使用向量检索（True=向量, False=关键词）
    REBUILD_INDEX_ON_STARTUP = False  # 是否每次启动都重建索引（首次启动建议True）

    # ========== 项目路径（重要：修改为你的实际路径）==========
    FRONTEND_PATH = r"D:\java_project\mdm_web\mdm_web\master"
    BACKEND_PATH = r"D:\java_project\mdm_api\mdm_api\master"