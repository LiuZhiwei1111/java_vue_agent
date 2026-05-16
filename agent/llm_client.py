"""
LLM客户端 - 调用智谱AI API
"""
from openai import OpenAI
from config import Config


class LLMClient:
    def __init__(self):
        self.client = OpenAI(
            api_key=Config.ZHIPU_API_KEY,
            base_url="https://open.bigmodel.cn/api/paas/v4/"
        )
        self.model = "glm-4-flash"

    def chat(self, messages, temperature=0.7):
        """非流式输出（保留兼容）"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"API调用失败: {e}")
            return f"抱歉，AI服务暂时不可用: {str(e)}"

    def chat_stream(self, messages, temperature=0.7):
        """流式输出 - 返回生成器"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                stream=True
            )
            # 直接遍历 response 并 yield 每个 chunk
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            print(f"API调用失败: {e}")
            yield f"抱歉，AI服务暂时不可用: {str(e)}"