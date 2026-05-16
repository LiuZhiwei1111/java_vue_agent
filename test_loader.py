# test_loader.py
from knowledge_base.loader import load_java_files, load_vue_files
from config import Config

print("测试代码加载器...")
java_files = load_java_files(Config.BACKEND_PATH)
vue_files = load_vue_files(Config.FRONTEND_PATH)

print(f"找到 {len(java_files)} 个Java文件")
print(f"找到 {len(vue_files)} 个Vue文件")

if len(java_files) == 0:
    print("⚠️ 请检查 config.py 中的 BACKEND_PATH 是否正确")
if len(vue_files) == 0:
    print("⚠️ 请检查 config.py 中的 FRONTEND_PATH 是否正确")