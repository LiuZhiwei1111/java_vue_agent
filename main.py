"""
项目知识库智能体 - 主程序
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import uuid
import json
import os
import time
import asyncio

from agent.retriever import KnowledgeRetriever
from agent.llm_client import LLMClient
from config import Config

# 根据配置导入不同的检索器
if Config.USE_VECTOR_RETRIEVAL:
    from knowledge_base.vector_retriever import VectorRetriever
else:
    from knowledge_base.indexer import CodeIndexer

from knowledge_base.loader import load_java_files, load_vue_files

app = FastAPI(title="项目知识库智能体")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

vector_store = None
retriever = None
llm_client = None


class SessionManager:
    def __init__(self, persist_file="sessions.json"):
        self.persist_file = persist_file
        self.sessions = self.load_sessions()

    def load_sessions(self):
        if os.path.exists(self.persist_file):
            with open(self.persist_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def save_sessions(self):
        with open(self.persist_file, 'w', encoding='utf-8') as f:
            json.dump(self.sessions, f, ensure_ascii=False, indent=2)

    def get_session(self, session_id):
        return self.sessions.get(session_id, [])

    def add_message(self, session_id, role, content):
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        self.sessions[session_id].append({
            "role": role,
            "content": content,
            "timestamp": time.time()
        })
        if len(self.sessions[session_id]) > 20:
            self.sessions[session_id] = self.sessions[session_id][-20:]
        self.save_sessions()

    def clear_session(self, session_id):
        if session_id in self.sessions:
            del self.sessions[session_id]
            self.save_sessions()


session_manager = SessionManager()


class QueryRequest(BaseModel):
    question: str
    session_id: Optional[str] = None


class QueryResponse(BaseModel):
    answer: str
    session_id: str
    sources: List[Dict]


@app.on_event("startup")
async def startup_event():
    global vector_store, retriever, llm_client
    print("=" * 60)
    print("启动智能体服务...")
    print(f"检索模式: {'向量检索' if Config.USE_VECTOR_RETRIEVAL else '关键词检索'}")
    print("=" * 60)

    # 初始化 LLM
    llm_client = LLMClient()
    print("✅ LLM客户端初始化完成")

    # 加载代码文件
    print("\n📂 加载代码文件...")
    java_files = load_java_files(Config.BACKEND_PATH)
    vue_files = load_vue_files(Config.FRONTEND_PATH)
    all_docs = java_files + vue_files
    print(f"   共加载 {len(all_docs)} 个文件 (Java: {len(java_files)}, Vue: {len(vue_files)})")

    if Config.USE_VECTOR_RETRIEVAL:
        # 使用向量检索
        print("\n🚀 初始化向量检索器...")
        vector_store = VectorRetriever()

        # 检查是否需要重建索引
        if Config.REBUILD_INDEX_ON_STARTUP or vector_store.collection.count() == 0:
            print("   构建向量索引...")
            vector_store.build_index(all_docs)
        else:
            print(f"   使用已有索引，文档片段数: {vector_store.collection.count()}")
    else:
        # 使用关键词检索
        print("\n📝 初始化关键词检索器...")
        indexer = CodeIndexer()
        vector_store = indexer.build_index(Config.FRONTEND_PATH, Config.BACKEND_PATH)

    retriever = KnowledgeRetriever(vector_store)
    print("\n✅ 智能体已就绪！")
    print("=" * 60)


@app.post("/query")
async def query(request: QueryRequest):
    """非流式接口（保留兼容）"""
    session_id = request.session_id or str(uuid.uuid4())
    history = session_manager.get_session(session_id)

    retrieved_docs = retriever.retrieve(request.question)
    code_context = retriever.format_context(retrieved_docs)

    messages = build_messages(request.question, code_context, history)
    answer = llm_client.chat(messages)

    session_manager.add_message(session_id, "user", request.question)
    session_manager.add_message(session_id, "assistant", answer)

    return QueryResponse(
        answer=answer,
        session_id=session_id,
        sources=retrieved_docs[:3]
    )


@app.post("/query/stream")
async def query_stream(request: QueryRequest):
    """流式接口"""
    session_id = request.session_id or str(uuid.uuid4())
    history = session_manager.get_session(session_id)

    # 先保存用户消息
    session_manager.add_message(session_id, "user", request.question)

    # 检索相关代码
    retrieved_docs = retriever.retrieve(request.question)
    code_context = retriever.format_context(retrieved_docs)

    # 构建消息
    messages = build_messages(request.question, code_context, history)

    # 创建流式响应
    async def generate():
        full_answer = ""

        # 先发送会话ID和来源信息
        meta_data = {
            "type": "meta",
            "session_id": session_id,
            "sources": retrieved_docs[:3]
        }
        yield f"data: {json.dumps(meta_data, ensure_ascii=False)}\n\n"

        # 流式生成回答
        try:
            # 注意：chat_stream 现在返回生成器，直接遍历
            for content_chunk in llm_client.chat_stream(messages):
                full_answer += content_chunk
                # 发送内容块
                data = {
                    "type": "content",
                    "content": content_chunk
                }
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0)  # 让出控制权

            # 保存完整回答到会话
            session_manager.add_message(session_id, "assistant", full_answer)

            # 发送结束标志
            yield f"data: {json.dumps({'type': 'end'})}\n\n"

        except Exception as e:
            print(f"流式生成错误: {e}")
            error_data = {
                "type": "error",
                "error": str(e)
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )


def build_messages(question: str, code_context: str, history: List[Dict]) -> List[Dict]:
    system_prompt = f"""你是Java+Vue3项目的专属智能助手。

## 项目代码参考
{code_context}

## 回答规则
1. 优先使用上述代码回答
2. 指出具体文件路径
3. 如果代码中没有，说明未找到
"""

    messages = [{"role": "system", "content": system_prompt}]
    for msg in history[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": question})
    return messages


@app.get("/sessions/{session_id}")
async def get_session_history(session_id: str):
    return {"session_id": session_id, "history": session_manager.get_session(session_id)}


@app.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    session_manager.clear_session(session_id)
    return {"status": "cleared"}


@app.get("/health")
async def health_check():
    return {"status": "ok", "session_count": len(session_manager.sessions)}


@app.get("/sessions")
async def get_all_sessions():
    """获取所有会话ID列表"""
    return {"sessions": list(session_manager.sessions.keys())}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)