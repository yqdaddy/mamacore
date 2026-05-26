"""统一 LLM 客户端 —— OpenAI SDK 封装。"""

import asyncio
import os
import sys
import time
from typing import AsyncGenerator, Optional

from openai import AsyncOpenAI


# ---------------------------------------------------------------------------
# 重试相关
# ---------------------------------------------------------------------------

class RetryError(Exception):
    """超过最大重试次数后抛出的异常。"""
    pass


# 可重试的 OpenAI 错误状态码 / 类型
_RETRIABLE_STATUSES = {429, 500, 502, 503, 504}
_RETRIABLE_KEYWORDS = ("rate limit", "timeout", "connection error")


def _is_retriable(error: Exception) -> bool:
    """判断错误是否属于可重试类型。

    可重试：429 限流、5xx 服务器错误、超时、连接错误。
    不可重试：401 无效 key、404 无效模型、400 参数错误。
    """
    # OpenAI SDK 异常带 status_code 属性
    status_code = getattr(error, "status_code", None)
    if status_code is not None:
        return status_code in _RETRIABLE_STATUSES

    # 按错误消息关键词兜底
    msg = str(error).lower()
    return any(kw in msg for kw in _RETRIABLE_KEYWORDS)


async def llm_generate_with_retry(
    prompt: str,
    system_prompt: str = "",
    model: str = "gpt-4o",
    temperature: float = 0.7,
    max_tokens: int = 4096,
    max_retries: int = 3,
    initial_delay: float = 1.0,
) -> str:
    """带指数退避重试的 LLM 调用。

    重试策略：1s -> 2s -> 4s，最多重试 3 次。
    区分可重试错误（rate limit, timeout）和不可重试错误（invalid key, invalid model）。

    Args:
        prompt: 用户提示词。
        system_prompt: 系统提示词（可选）。
        model: 模型名称，默认 gpt-4o。
        temperature: 温度参数，默认 0.7。
        max_tokens: 最大 token 数，默认 4096。
        max_retries: 最大重试次数，默认 3。
        initial_delay: 初始延迟秒数，默认 1.0。

    Returns:
        LLM 生成的文本内容。

    Raises:
        RetryError: 超过最大重试次数仍未成功。
    """
    client = get_openai_client()
    if not client:
        print(
            "[mamacore] 警告: 未设置 OPENAI_API_KEY 环境变量，使用 mock 数据",
            file=sys.stderr,
        )
        return ""

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    delay = initial_delay
    last_error: Optional[Exception] = None

    for attempt in range(max_retries + 1):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            last_error = e
            if not _is_retriable(e):
                # 不可重试错误（如 401 invalid key、404 invalid model），直接抛出
                raise
            if attempt < max_retries:
                print(
                    f"[mamacore] LLM 调用失败（第 {attempt + 1}/{max_retries + 1} 次），"
                    f"{delay:.1f}s 后重试: {e}",
                    file=sys.stderr,
                )
                await asyncio.sleep(delay)
                delay *= 2  # 指数退避
            else:
                break

    raise RetryError(
        f"LLM 调用在 {max_retries + 1} 次尝试后仍然失败: {last_error}"
    ) from last_error


# ---------------------------------------------------------------------------
# Token 成本估算
# ---------------------------------------------------------------------------

# Token 成本表（每 1K tokens 的美元价格）
# 键格式："模型名:input" 或 "模型名:output"
MODEL_COST: dict[str, float] = {
    "gpt-4o:input": 0.0025,
    "gpt-4o:output": 0.01,
    "gpt-4o-mini:input": 0.00015,
    "gpt-4o-mini:output": 0.0006,
    "gpt-4:input": 0.03,
    "gpt-4:output": 0.06,
    "gpt-3.5-turbo:input": 0.0005,
    "gpt-3.5-turbo:output": 0.0015,
    "claude-sonnet-4-20250514:input": 0.003,
    "claude-sonnet-4-20250514:output": 0.015,
}

# 中文约 1.5 字符/token，英文约 4 字符/token
_CN_CHARS_PER_TOKEN = 1.5
_EN_CHARS_PER_TOKEN = 4.0


def _count_tokens(text: str) -> int:
    """简单 token 计数估算。

    中文按 1.5 chars/token，英文按 4 chars/token，混合文本按比例加权。
    """
    cn_count = sum(1 for c in text if "一" <= c <= "鿿")
    en_count = len(text) - cn_count

    cn_tokens = cn_count / _CN_CHARS_PER_TOKEN
    en_tokens = en_count / _EN_CHARS_PER_TOKEN
    return int(cn_tokens + en_tokens)


def estimate_cost(text: str, model: str = "gpt-4o", direction: str = "output") -> dict:
    """估算单次调用的 token 数量和成本。

    使用简单估算：中文约 1.5 chars/token，英文约 4 chars/token。

    Args:
        text: 要估算的文本。
        model: 模型名称，默认 gpt-4o。
        direction: "input" 或 "output"，默认 output。

    Returns:
        包含 token 数量和估算成本的字典：
        {"tokens": int, "cost_usd": float, "model": str, "direction": str}
    """
    tokens = _count_tokens(text)
    cost_key = f"{model}:{direction}"
    per_1k = MODEL_COST.get(cost_key, MODEL_COST.get(f"gpt-4o:{direction}", 0.01))
    cost_usd = (tokens / 1000) * per_1k

    return {
        "tokens": tokens,
        "cost_usd": round(cost_usd, 6),
        "model": model,
        "direction": direction,
        "per_1k_usd": per_1k,
    }


# ---------------------------------------------------------------------------
# 流式输出
# ---------------------------------------------------------------------------

async def llm_generate_stream(
    prompt: str,
    system_prompt: str = "",
    model: str = "gpt-4o",
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> AsyncGenerator[str, None]:
    """流式生成，逐 chunk 返回文本。

    适用于需要实时显示生成进度的场景。

    Args:
        prompt: 用户提示词。
        system_prompt: 系统提示词（可选）。
        model: 模型名称，默认 gpt-4o。
        temperature: 温度参数，默认 0.7。
        max_tokens: 最大 token 数，默认 4096。

    Yields:
        每次生成的文本片段（chunk）。
    """
    client = get_openai_client()
    if not client:
        print(
            "[mamacore] 警告: 未设置 OPENAI_API_KEY 环境变量，无法流式生成",
            file=sys.stderr,
        )
        return

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )

    async for chunk in response:
        delta = chunk.choices[0].delta if chunk.choices else None
        if delta and delta.content:
            yield delta.content


# ---------------------------------------------------------------------------
# 原有函数（向后兼容）
# ---------------------------------------------------------------------------

def get_openai_client() -> Optional[AsyncOpenAI]:
    """获取 OpenAI 异步客户端。未设置 API Key 时返回 None。"""
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    return AsyncOpenAI(api_key=api_key)


async def llm_generate(
    prompt: str,
    system_prompt: str = "",
    model: str = "gpt-4o",
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> str:
    """调用 LLM 生成文本。

    如果未设置 API Key，返回空字符串并打印警告到 stderr。

    Args:
        prompt: 用户提示词。
        system_prompt: 系统提示词（可选）。
        model: 模型名称，默认 gpt-4o。
        temperature: 温度参数，默认 0.7。
        max_tokens: 最大 token 数，默认 4096。

    Returns:
        LLM 生成的文本内容。无 API Key 时返回空字符串。
    """
    client = get_openai_client()
    if not client:
        print(
            "[mamacore] 警告: 未设置 OPENAI_API_KEY 环境变量，使用 mock 数据",
            file=sys.stderr,
        )
        return ""

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content or ""
