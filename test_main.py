"""
测试主程序 API
"""
import requests
import time
import sys

try:
    import requests
except ImportError:
    print("请先安装: pip install requests")
    sys.exit(1)


def test_api():
    print("=" * 60)
    print("主程序 API 测试")
    print("=" * 60)

    base_url = "http://localhost:8000"

    # 步骤1: 检查服务状态
    print("\n[步骤1] 检查服务状态...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print(f"   ✅ 服务正常运行")
            print(f"   响应: {response.json()}")
        else:
            print(f"   ❌ 服务异常")
            return False
    except Exception as e:
        print(f"   ❌ 连接失败: {e}")
        return False

    # 步骤2: 测试单次问答（增加超时到120秒）
    print("\n[步骤2] 测试单次问答...")
    question = "用户登录"
    print(f"   问题: {question}")

    try:
        # 增加超时时间到120秒
        response = requests.post(
            f"{base_url}/query",
            json={"question": question},
            timeout=120  # 增加到120秒
        )
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 收到回答")
            print(f"   会话ID: {data['session_id']}")
            print(f"   回答长度: {len(data['answer'])} 字符")
            print(f"   来源数量: {len(data.get('sources', []))}")
            print(f"\n   回答内容:")
            print("-" * 40)
            print(data['answer'][:500])
            print("-" * 40)
        else:
            print(f"   ❌ 请求失败: {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print("   ❌ 请求超时（120秒）")
        print("   检索可能太慢，考虑优化索引")
        return False
    except Exception as e:
        print(f"   ❌ 请求失败: {e}")
        return False

    print("\n✅ 主程序 API 测试完成")
    return True


if __name__ == "__main__":
    test_api()