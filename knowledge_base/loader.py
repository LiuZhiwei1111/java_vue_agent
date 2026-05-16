"""
代码加载器
作用：扫描文件夹，读取所有Java和Vue文件的内容
"""

import os
from pathlib import Path
from typing import List, Dict


def load_java_files(root_path: str) -> List[Dict]:
    """
    加载所有Java文件
    参数: root_path - Java项目根目录
    返回: 包含文件路径和内容的字典列表
    """
    java_files = []
    if not os.path.exists(root_path):
        print(f"⚠️ 警告: Java路径不存在 {root_path}")
        return java_files

    for path in Path(root_path).rglob("*.java"):
        if "test" in str(path).lower():
            continue
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            java_files.append({
                "content": content,
                "source": str(path),
                "type": "java"
            })
        except Exception as e:
            print(f"读取失败 {path}: {e}")

    print(f"✅ 已加载 {len(java_files)} 个Java文件")
    return java_files


def load_vue_files(root_path: str) -> List[Dict]:
    """加载所有Vue文件"""
    vue_files = []
    if not os.path.exists(root_path):
        print(f"⚠️ 警告: Vue路径不存在 {root_path}")
        return vue_files

    for path in Path(root_path).rglob("*.vue"):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            vue_files.append({
                "content": content,
                "source": str(path),
                "type": "vue"
            })
        except Exception as e:
            print(f"读取失败 {path}: {e}")

    print(f"✅ 已加载 {len(vue_files)} 个Vue文件")
    return vue_files