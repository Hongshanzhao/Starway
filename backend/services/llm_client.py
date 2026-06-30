import json
import os
import time
from typing import Dict, Iterable, Iterator, List, Optional

import requests
from dotenv import load_dotenv


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"), override=False)


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


def provider_chain(provider: Optional[str] = None) -> List[str]:
    selected = (provider or os.getenv("LLM_PROVIDER") or os.getenv("LLM_MODE") or "local").lower()
    if selected in ("auto", "real"):
        chain = []
        if os.getenv("ZHIPU_API_KEY"):
            chain.append("zhipu")
        if os.getenv("DEEPSEEK_API_KEY"):
            chain.append("deepseek")
        return chain or ["local"]
    if selected in PROVIDERS:
        return [selected]
    return ["local"]


class LLMClient:
    def __init__(self, provider: Optional[str] = None, timeout: int = 18):
        self.requested_provider = (provider or os.getenv("LLM_PROVIDER") or os.getenv("LLM_MODE") or "local").lower()
        self.provider = normalize_provider(provider)
        self.last_error = ""
        self.used_fallback = False
        self.timeout = timeout

    @property
    def is_local(self) -> bool:
        return self.provider == "local"

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.3,
             max_tokens: int = 2000, stream: bool = False) -> str:
        errors = []
        for provider in provider_chain(self.requested_provider):
            self.provider = provider
            if provider == "local":
                self.used_fallback = True
                return local_answer(messages)
            try:
                return self._remote_chat(provider, messages, temperature, max_tokens, stream)
            except Exception as exc:
                errors.append(f"{provider}: {exc}")
                self.last_error = " | ".join(errors)
        self.provider = "local"
        self.used_fallback = True
        return local_answer(messages)

    def chat_remote_only(self, messages: List[Dict[str, str]], temperature: float = 0.3,
                         max_tokens: int = 2000, stream: bool = False,
                         skip_providers: Optional[Iterable[str]] = None) -> str:
        errors = []
        skip = set(skip_providers or [])
        for provider in provider_chain(self.requested_provider):
            if provider == "local" or provider in skip:
                continue
            self.provider = provider
            try:
                self.used_fallback = False
                return self._remote_chat(provider, messages, temperature, max_tokens, stream)
            except Exception as exc:
                errors.append(f"{provider}: {exc}")
                self.last_error = " | ".join(errors)
        raise RuntimeError(self.last_error or "No remote LLM provider configured")

    def _remote_chat(self, provider: str, messages: List[Dict[str, str]], temperature: float,
                     max_tokens: int, stream: bool = False) -> str:
        cfg = PROVIDERS[provider]
        api_key = os.getenv(cfg["env_key"])
        if not api_key:
            raise RuntimeError(f"{cfg['env_key']} is not configured")
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

    def test_remote(self, messages: List[Dict[str, str]], temperature: float = 0.1,
                    max_tokens: int = 100) -> str:
        errors = []
        for provider in provider_chain(self.requested_provider):
            if provider == "local":
                continue
            self.provider = provider
            try:
                self.used_fallback = False
                return self._remote_chat(provider, messages, temperature, max_tokens, stream=False)
            except Exception as exc:
                errors.append(f"{provider}: {exc}")
        self.last_error = " | ".join(errors)
        raise RuntimeError(self.last_error or "No remote LLM provider configured")

    def stream_chat(self, messages: List[Dict[str, str]], temperature: float = 0.3,
                    max_tokens: int = 2000) -> Iterator[str]:
        errors = []
        for provider in provider_chain(self.requested_provider):
            self.provider = provider
            if provider == "local":
                self.used_fallback = True
                yield from chunk_text(local_answer(messages))
                return
            try:
                yield from self._remote_stream_chat(provider, messages, temperature, max_tokens)
                return
            except Exception as exc:
                errors.append(f"{provider}: {exc}")
                self.last_error = " | ".join(errors)
        self.provider = "local"
        self.used_fallback = True
        yield from chunk_text(local_answer(messages))

    def _remote_stream_chat(self, provider: str, messages: List[Dict[str, str]],
                            temperature: float, max_tokens: int) -> Iterator[str]:
        cfg = PROVIDERS[provider]
        api_key = os.getenv(cfg["env_key"])
        if not api_key:
            raise RuntimeError(f"{cfg['env_key']} is not configured")
        payload = {
            "model": cfg["model"],
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        with requests.post(
            cfg["base_url"],
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=self.timeout,
            stream=True,
        ) as response:
            response.raise_for_status()
            for raw in response.iter_lines(decode_unicode=True):
                if not raw:
                    continue
                line = raw.strip()
                if not line.startswith("data:"):
                    continue
                payload_text = line[5:].strip()
                if payload_text == "[DONE]":
                    break
                try:
                    data = json.loads(payload_text)
                    delta = data.get("choices", [{}])[0].get("delta") or {}
                    content = delta.get("content") or ""
                    if content:
                        yield content
                except Exception:
                    continue


def chunk_text(text: str, size: int = 48) -> Iterator[str]:
    for i in range(0, len(text), size):
        yield text[i:i + size]
        time.sleep(0.01)


def local_answer(messages: Iterable[Dict[str, str]]) -> str:
    last = ""
    for message in messages:
        if message.get("role") == "user":
            last = message.get("content", "")
    lower = last.lower()
    if "python" in lower or "后端" in last:
        return """可以按“基础能力、项目作品、简历表达、面试准备”四条线推进。

1. 基础能力：优先补齐 Python Web 框架（Flask/FastAPI）、RESTful API、SQL 查询与索引、Redis 缓存、Linux 基础和 Docker 部署。不要只学语法，要能解释一次请求从前端到数据库再返回的完整链路。

2. 项目作品：做一个完整后端项目，比如岗位推荐、学习计划、校园服务或数据看板。项目要包含登录鉴权、数据库设计、核心 API、错误处理、日志、部署说明和接口文档。面试时重点讲“为什么这样设计”和“遇到问题怎么排查”。

3. 简历表达：每条经历尽量写成“动作 + 技术 + 结果”。例如：使用 Flask 设计 12 个 REST API，接入 SQLite/MySQL，完成岗位搜索、画像生成和报告导出，将页面接口响应控制在某个范围内。

4. 面试准备：准备 Python 基础、数据库索引、HTTP、缓存、并发、部署、项目复盘这些高频问题。每天做一点小复盘，把回答练到具体、清晰、有证据。"""
    if "简历" in last or "作品" in last:
        return """简历优化建议从三层入手：第一层是岗位关键词匹配，把目标岗位 JD 中高频技能放到技能栏和项目描述里；第二层是成果量化，每个项目至少写清你的职责、技术方案和结果；第三层是可验证材料，比如项目仓库、接口文档、截图、部署地址或分析报告。不要堆形容词，尽量用具体动作证明能力。"""
    return """建议先明确一个主目标岗位和两个相邻备选方向，然后做三件事：一是整理已有技能和经历，找出最能证明能力的素材；二是对照岗位 JD 标记缺口，按 30/60/90 天节奏补齐；三是把学习过程沉淀成作品、简历条目和面试讲稿。职业规划不是一次性决定，而是持续试探、反馈和调整。"""


def sse_event(event_type: str, data: Dict) -> str:
    payload = json.dumps({"type": event_type, **data}, ensure_ascii=False)
    return f"data: {payload}\n\n"
