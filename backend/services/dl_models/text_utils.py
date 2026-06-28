"""
文本清洗工具：去除HTML标签、URL、特殊符号
仅在内存中清洗，不写回数据库
"""

import re


def clean_text(text: str) -> str:
    """
    清洗文本：
    - 去除 HTML 标签
    - 去除 URL
    - 去除特殊符号，保留中文/英文/数字/句号/逗号
    - 合并多余空格
    - 过滤长度 < 5 的文本
    """
    if not text:
        return ""

    # 去除 HTML 标签
    text = re.sub(r'<[^>]+>', ' ', text)
    # 去除 URL
    text = re.sub(r'https?://\S+', ' ', text)
    # 去除特殊符号，保留中文、英文、数字、句号、逗号
    text = re.sub(r'[^一-鿿A-Za-z0-9。，,.]', ' ', text)
    # 合并多余空格
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def is_valid_text(text: str, min_len: int = 5) -> bool:
    """检查清洗后的文本是否有效（长度 >= min_len）"""
    return len(clean_text(text)) >= min_len
