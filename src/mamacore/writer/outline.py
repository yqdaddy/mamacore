"""Outline generation — constructs LLM prompts and returns structured outlines."""

import asyncio
import json
import logging

from mamacore.writer.models import FrameworkType, WritingStyle
from mamacore.writer.framework import get_framework_prompt, get_framework_structure
from mamacore.writer.style import get_style_prompt, get_default_word_count
from mamacore.llm.client import llm_generate_with_retry

logger = logging.getLogger(__name__)


async def generate_outline(
    topic: str,
    framework: FrameworkType | str,
    style: WritingStyle | str,
    word_count: tuple[int, int] | None = None,
) -> list[dict]:
    """Generate a structured article outline using LLM.

    Args:
        topic: The article topic.
        framework: Article framework type (checklist/pain/compare/narrative).
        style: Writing style (satire/tongue/analytical/experience/science).
        word_count: Optional (min, max) word count range.

    Returns:
        List of section dicts: [{"section": "...", "key_points": [...]}]
    """
    framework_prompt = get_framework_prompt(framework)
    style_prompt = get_style_prompt(style)
    sections = get_framework_structure(framework)

    if word_count is None:
        word_count = get_default_word_count()

    prompt = _build_outline_prompt(
        topic=topic,
        framework_prompt=framework_prompt,
        style_prompt=style_prompt,
        sections=sections,
        word_count=word_count,
    )

    # Try real LLM call with retry; fall back to mock on failure or missing API key
    system_prompt = f"你是公众号文章大纲生成专家。{style_prompt}"
    try:
        raw = await llm_generate_with_retry(
            prompt=prompt,
            system_prompt=system_prompt,
            model="gpt-4o",
            temperature=0.7,
            max_tokens=2048,
            max_retries=3,
        )
        if raw:
            outline = _parse_outline_json(raw)
            if outline:
                logger.info("LLM 大纲生成成功（真实调用）")
                return outline
            logger.warning(
                "[mamacore] LLM 返回内容无法解析为 JSON，fallback 到 mock 大纲"
            )
        else:
            logger.warning(
                "[mamacore] LLM 返回空内容（无 API Key），fallback 到 mock 大纲"
            )
    except Exception as e:
        logger.warning(
            "[mamacore] LLM 调用失败: %s，fallback 到 mock 大纲", e
        )

    return await _simulate_llm_outline(prompt, topic, framework, sections)


def _parse_outline_json(raw: str) -> list[dict] | None:
    """从 LLM 返回的文本中解析 JSON 大纲。

    尝试直接解析，也尝试提取 ```json ... ``` 代码块。
    """
    # 尝试直接解析
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass

    # 尝试提取 ```json 代码块
    import re

    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", raw, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(1).strip())
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass

    return None


def _build_outline_prompt(
    topic: str,
    framework_prompt: str,
    style_prompt: str,
    sections: list[str],
    word_count: tuple[int, int],
) -> str:
    """Build the LLM prompt for outline generation."""
    return f"""请为以下主题生成一篇公众号文章的结构化大纲。

主题：{topic}

{framework_prompt}

{style_prompt}

要求：
- 目标字数：{word_count[0]}-{word_count[1]} 字
- 大纲包含以下章节：{', '.join(sections)}
- 每个章节列出 2-4 个关键要点
- 输出严格的 JSON 格式，不要有任何额外文字

输出格式：
[
  {{"section": "章节名", "key_points": ["要点1", "要点2"]}},
  ...
]
"""


async def _simulate_llm_outline(
    prompt: str,
    topic: str,
    framework: FrameworkType | str,
    sections: list[str],
) -> list[dict]:
    """Simulate LLM outline generation with a mock response.

    This will be replaced with an actual LLM API call once the LLM
    integration is complete.
    """
    framework_key = (
        framework.value if isinstance(framework, FrameworkType) else framework
    )

    # Simulated outlines per framework type
    mock_outlines: dict[str, list[dict]] = {
        "checklist": [
            {
                "section": "开头引入",
                "key_points": [
                    f"从当前行业现象切入，点出{topic}的重要性",
                    "用一组数据或案例说明为什么需要这份清单",
                    "预告清单核心价值，激发阅读期待",
                ],
            },
            {
                "section": "核心清单",
                "key_points": [
                    "条目 1：最基础但最常被忽略的关键点",
                    "条目 2：进阶技巧，大多数人不知道",
                    "条目 3：效率倍增的隐藏方法",
                    "条目 4：避坑指南——常见错误及替代方案",
                    "条目 5：终极建议——什么情况下应该怎么做",
                ],
            },
            {
                "section": "结尾总结",
                "key_points": [
                    "回顾清单最核心的 3 个要点",
                    "给出第一步行动建议",
                    "金句收尾，引导转发或收藏",
                ],
            },
        ],
        "pain": [
            {
                "section": "痛点场景",
                "key_points": [
                    f"描绘一个具体场景：{topic} 中遇到的典型困境",
                    "让读者产生'这就是我'的强烈共鸣",
                    "点出这个痛点造成的实际损失",
                ],
            },
            {
                "section": "根因分析",
                "key_points": [
                    "打破常见认知误区——'不是你想的那样'",
                    "分析痛点的深层原因",
                    "用数据或案例支撑分析",
                ],
            },
            {
                "section": "解决方案",
                "key_points": [
                    "方案 1：立即可执行的第一步",
                    "方案 2：中期优化策略",
                    "方案 3：长期体系建设",
                ],
            },
            {
                "section": "案例证明",
                "key_points": [
                    "真实案例：谁用了什么方案，效果如何",
                    "数据对比：使用前后的具体变化",
                ],
            },
            {
                "section": "行动号召",
                "key_points": [
                    "总结最有效的方案",
                    "给出读者今天的行动建议",
                    "金句收尾",
                ],
            },
        ],
        "compare": [
            {
                "section": "选型困境",
                "key_points": [
                    f"说明{topic}领域中为什么需要做选择",
                    "列举常见选项和选择困惑",
                    "点出选错的代价",
                ],
            },
            {
                "section": "对比维度",
                "key_points": [
                    "维度 1：性能/效果对比",
                    "维度 2：成本/门槛对比",
                    "维度 3：生态/扩展性对比",
                    "维度 4：风险/踩坑对比",
                ],
            },
            {
                "section": "逐项分析",
                "key_points": [
                    "每个维度的详细对比 + 真实体感",
                    "给出明确评分或评级",
                    "指出各选项最适合的场景",
                ],
            },
            {
                "section": "场景结论",
                "key_points": [
                    "场景 A 下的最佳选择",
                    "场景 B 下的最佳选择",
                    "场景 C 下的最佳选择",
                ],
            },
            {
                "section": "选择建议",
                "key_points": [
                    "决策流程图或 checklist",
                    "新手和老手的不同建议",
                    "金句收尾",
                ],
            },
        ],
        "narrative": [
            {
                "section": "场景开场",
                "key_points": [
                    f"用一个引人入胜的场景开场：{topic} 相关的真实冲突或转折",
                    "设置悬念，让读者想知道后来发生了什么",
                ],
            },
            {
                "section": "故事展开",
                "key_points": [
                    "遇到挑战——具体困难和挫折",
                    "探索过程——尝试了哪些方法，失败了什么",
                    "转折点——关键发现或顿悟时刻",
                    "领悟——从经历中提炼的核心认知",
                ],
            },
            {
                "section": "观点升华",
                "key_points": [
                    "从故事中提炼核心观点",
                    "用数据或理论支撑这个观点",
                    "说明这个观点的普遍适用性",
                ],
            },
            {
                "section": "延伸启示",
                "key_points": [
                    "将观点扩展到更广泛的场景",
                    "给出读者可以立即尝试的行动",
                ],
            },
            {
                "section": "闭环结尾",
                "key_points": [
                    "回到开头场景，展示变化",
                    "一句话总结核心启示",
                    "留白，让读者思考",
                ],
            },
        ],
    }

    outline = mock_outlines.get(framework_key, mock_outlines["checklist"])
    return outline
