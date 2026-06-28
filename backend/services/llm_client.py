import json
import os
import time
from typing import Dict, Iterable, Iterator, List, Optional

import requests


PROVIDERS = {
    "deepseek": {
        "base_url": "https://api.deepseek.com/chat/completions",
        "env_key": "DEEPSEEK_API_KEY",
        "model": "deepseek-chat",
    },
    "zhipu": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "env_key": "ZHIPU_API_KEY",
        "model": "glm-4-flash",
    },
}


def normalize_provider(provider: Optional[str] = None) -> str:
    selected = (provider or os.getenv("LLM_PROVIDER") or os.getenv("LLM_MODE") or "local").lower()
    if selected in ("auto", "real"):
        if os.getenv("ZHIPU_API_KEY"):
            return "zhipu"
        if os.getenv("DEEPSEEK_API_KEY"):
            return "deepseek"
        return "local"
    if selected in PROVIDERS:
        return selected
    return "local"


class LLMClient:
    def __init__(self, provider: Optional[str] = None, timeout: int = 60):
        self.provider = normalize_provider(provider)
        self.timeout = timeout

    @property
    def is_local(self) -> bool:
        return self.provider == "local"

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.3,
             max_tokens: int = 2000, stream: bool = False) -> str:
        if self.is_local:
            return local_answer(messages)
        cfg = PROVIDERS[self.provider]
        api_key = os.getenv(cfg["env_key"])
        if not api_key:
            return local_answer(messages)
        payload = {
            "model": cfg["model"],
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }
        response = requests.post(
            cfg["base_url"],
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=self.timeout,
            stream=stream,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    def stream_chat(self, messages: List[Dict[str, str]], temperature: float = 0.3,
                    max_tokens: int = 2000) -> Iterator[str]:
        text = self.chat(messages, temperature=temperature, max_tokens=max_tokens, stream=False)
        for chunk in chunk_text(text):
            yield chunk


def chunk_text(text: str, size: int = 48) -> Iterator[str]:
    for i in range(0, len(text), size):
        yield text[i:i + size]
        time.sleep(0.01)


def local_answer(messages: Iterable[Dict[str, str]]) -> str:
    last = ""
    for message in messages:
        if message.get("role") == "user":
            last = message.get("content", "")
    if "python" in last.lower() or "后端" in last:
        return "建议重点补齐 Flask/FastAPI、SQL 优化、接口设计、项目部署和简历中的量化项目成果。"
    return "可以先明确目标岗位、已有技能和城市偏好，再按技能差距、项目作品和面试准备三步推进。"


def sse_event(event_type: str, data: Dict) -> str:
    payload = json.dumps({"type": event_type, **data}, ensure_ascii=False)
    return f"data: {payload}\n\n"
