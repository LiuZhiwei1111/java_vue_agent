"""
测试 LLM 客户端
运行方式: python test_llm.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from agent.llm_client import LLMClient
from config import Config


def test_llm():
    print("=" * 60)
    print("LLM 客户端测试")
    print("=" * 60)

    # 步骤1: 检查 API Key
    print("\n[步骤1] 检查 API Key...")
    if not Config.ZHIPU_API_KEY:
        print("   ❌ API Key 未配置！")
        print("   请在 .env 文件中设置 ZHIPU_API_KEY")
        return False
    print(f"   ✅ API Key 已配置: {Config.ZHIPU_API_KEY[:10]}...")

    # 步骤2: 创建客户端
    print("\n[步骤2] 创建 LLM 客户端...")
    try:
        client = LLMClient()
        print("   ✅ 客户端创建成功")
    except Exception as e:
        print(f"   ❌ 客户端创建失败: {e}")
        return False

    # 步骤3: 测试简单问答
    print("\n[步骤3] 测试简单问答...")
    messages = [
        {"role": "system", "content": "你是Java和Vue项目的技术助手，请用中文简短回答。"},
        {"role": "user", "content": "你好，请介绍一下你自己"}
    ]

    try:
        print("   发送请求中...")
        response = client.chat(messages)
        print(f"   ✅ 收到回复: {response[:150]}...")
    except Exception as e:
        print(f"   ❌ 请求失败: {e}")
        return False

    # 步骤4: 测试带上下文的问答
    print("\n[步骤4] 测试带上下文的问答...")
    messages = [
        {"role": "system", "content": "你是Java技术专家。"},
        {"role": "user", "content": "Spring Boot中@RestController注解的作用是什么？"}
    ]

    try:
        response = client.chat(messages)
        print(f"   ✅ 收到回复: {response[:150]}...")
    except Exception as e:
        print(f"   ❌ 请求失败: {e}")
        return False

    print("\n✅ LLM 客户端测试完成")
    return True


if __name__ == "__main__":
    test_llm()