"""Draft generation — generates a full Markdown article draft from an outline."""

import asyncio
import logging

from mamacore.writer.models import FrameworkType, WritingStyle
from mamacore.writer.framework import get_framework_prompt
from mamacore.writer.style import get_style_prompt, get_default_word_count
from mamacore.llm.client import llm_generate_with_retry

logger = logging.getLogger(__name__)


async def generate_draft(
    topic: str,
    outline: list[dict],
    framework: FrameworkType | str,
    style: WritingStyle | str,
    word_count: tuple[int, int] | None = None,
) -> str:
    """Generate a full Markdown draft from an outline.

    Args:
        topic: The article topic.
        outline: Structured outline from generate_outline().
        framework: Article framework type.
        style: Writing style.
        word_count: Optional (min, max) word count range.

    Returns:
        Full article Markdown text.
    """
    framework_prompt = get_framework_prompt(framework)
    style_prompt = get_style_prompt(style)

    if word_count is None:
        word_count = get_default_word_count()

    prompt = _build_draft_prompt(
        topic=topic,
        outline=outline,
        framework_prompt=framework_prompt,
        style_prompt=style_prompt,
        word_count=word_count,
    )

    # Try real LLM call with retry; fall back to mock on failure or missing API key
    system_prompt = f"你是公众号文章写作专家。{style_prompt}"
    try:
        draft = await llm_generate_with_retry(
            prompt=prompt,
            system_prompt=system_prompt,
            model="gpt-4o",
            temperature=0.7,
            max_tokens=8192,
            max_retries=3,
        )
        if draft:
            logger.info("LLM 初稿生成成功（真实调用）")
            return draft
        logger.warning(
            "[mamacore] LLM 返回空内容（无 API Key），fallback 到 mock 草稿"
        )
    except Exception as e:
        logger.warning(
            "[mamacore] LLM 调用失败: %s，fallback 到 mock 草稿", e
        )

    return await _simulate_llm_draft(prompt, topic, outline, framework, style)


def _build_draft_prompt(
    topic: str,
    outline: list[dict],
    framework_prompt: str,
    style_prompt: str,
    word_count: tuple[int, int],
) -> str:
    """Build the LLM prompt for draft generation."""
    import json

    outline_json = json.dumps(outline, ensure_ascii=False, indent=2)

    return f"""请根据以下大纲，写一篇完整的公众号文章。

主题：{topic}

{framework_prompt}

{style_prompt}

大纲：
{outline_json}

要求：
- 目标字数：{word_count[0]}-{word_count[1]} 字
- 使用 Markdown 格式
- 小标题使用 ## 级别
- 中英文之间加空格，中文与数字之间加空格
- 使用全角中文标点
- 不要有任何额外的说明文字，直接输出文章正文
"""


async def _simulate_llm_draft(
    prompt: str,
    topic: str,
    outline: list[dict],
    framework: FrameworkType | str,
    style: WritingStyle | str,
) -> str:
    """Simulate LLM draft generation with a mock response."""
    framework_key = (
        framework.value if isinstance(framework, FrameworkType) else framework
    )
    style_key = style.value if isinstance(style, WritingStyle) else style

    lines: list[str] = []
    lines.append(f"# {topic}\n")

    for section in outline:
        section_title = section.get("section", "")
        key_points = section.get("key_points", [])

        lines.append(f"## {section_title}\n")
        for i, point in enumerate(key_points, 1):
            lines.append(f"**{i}. {point}**\n")
            lines.append(
                f"（这里是关于「{point}」的详细说明，包含具体案例、数据和"
                f"分析。实际生成时会由 LLM 展开为 2-3 段完整文字。）\n"
            )
        lines.append("")

    lines.append("---\n")
    lines.append(
        "> 注：这是一篇基于框架引擎生成的初稿。\n"
        "> 框架类型：{} | 写作风格：{} | 待接入 LLM 后自动填充完整内容。\n".format(
            framework_key, style_key
        )
    )

    return "\n".join(lines)
