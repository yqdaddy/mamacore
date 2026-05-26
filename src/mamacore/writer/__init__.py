"""M.A.M.A. Core Writer Module — framework engine for WeChat article generation.

Provides MCP tools for the full article generation pipeline:
outline generation → draft → enhancement → title candidates.
"""

from mcp.server.fastmcp import FastMCP

from mamacore.writer.models import Article, FrameworkType, WritingStyle
from mamacore.writer.outline import generate_outline
from mamacore.writer.draft import generate_draft
from mamacore.writer.enhance import enhance_article
from mamacore.writer.framework import get_framework_prompt, get_framework_structure
from mamacore.writer.style import (
    build_style_system_prompt,
    get_default_framework,
    get_default_style,
    get_style_prompt,
)


def register_tools(mcp: FastMCP) -> None:
    """Register all writer MCP tools on the given FastMCP server."""

    @mcp.tool()
    async def mama_generate_outline(
        topic: str,
        framework: str = "",
        style: str = "",
    ) -> list[dict]:
        """为指定主题生成文章大纲。

        Args:
            topic: 文章主题。
            framework: 框架类型（checklist/pain/compare/narrative），默认使用配置文件中的值。
            style: 写作风格（satire/tongue/analytical/experience/science），默认使用配置文件中的值。

        Returns:
            结构化大纲列表，每项包含 section（章节名）和 key_points（关键要点列表）。
        """
        fw = framework or get_default_framework()
        st = style or get_default_style().value
        return await generate_outline(topic, fw, st)

    @mcp.tool()
    async def mama_write_article(
        topic: str,
        framework: str = "",
        style: str = "",
        include_images: bool = False,
    ) -> dict:
        """全流程生成公众号文章：大纲 → 初稿 → 增强 → 标题候选。

        Args:
            topic: 文章主题。
            framework: 框架类型（checklist/pain/compare/narrative），默认使用配置文件中的值。
            style: 写作风格（satire/tongue/analytical/experience/science），默认使用配置文件中的值。
            include_images: 是否包含配图建议（当前为模拟数据）。

        Returns:
            包含完整文章数据的字典，对应 Article 模型的所有字段。
        """
        fw = framework or get_default_framework()
        st = style or get_default_style().value

        # Step 1: Generate outline
        outline = await generate_outline(topic, fw, st)

        # Step 2: Generate draft
        draft = await generate_draft(topic, outline, fw, st)

        # Step 3: Enhance
        enhanced = await enhance_article(draft)

        # Step 4: Generate title candidates
        title_candidates = _generate_title_candidates(topic, fw)

        # Build article model
        article = Article(
            topic=topic,
            framework=FrameworkType(fw),
            style=WritingStyle(st),
            outline=outline,
            draft=draft,
            enhanced=enhanced,
            title_candidates=title_candidates,
            selected_title=title_candidates[0]["text"] if title_candidates else "",
        )

        if include_images:
            article.images = _generate_image_suggestions(topic)

        return article.model_dump(mode="json")

    @mcp.tool()
    async def mama_score_title(title: str) -> str:
        """给标题打分，基于多维度规则评分（数字/悬念/痛点/情绪）。

        返回详细评分 breakdown 和优化建议。

        Args:
            title: 要评分的标题
        """
        from mamacore.writer.title import score_title

        result = score_title(title)

        lines = [
            f"## 标题评分: {result['score']}/100",
            f"模式标签: {', '.join(result['patterns'])}",
            "",
            "维度得分:",
        ]
        for dim, pts in result["breakdown"].items():
            lines.append(f"  - {dim}: {pts}/25")

        lines.append("")
        if result["score"] >= 75:
            lines.append("评价: 优秀标题，具备打开率优势。")
        elif result["score"] >= 50:
            lines.append("评价: 合格标题，建议优化悬念或痛点维度。")
        else:
            lines.append("评价: 建议重写，缺少吸引力元素。")

        return "\n".join(lines)

    # Private helpers (not registered as MCP tools)


def _generate_title_candidates(
    topic: str, framework: str
) -> list[dict]:
    """Generate mock title candidates with scores.

    TODO: Replace with LLM-generated titles once integrated.
    """
    templates: dict[str, list[str]] = {
        "checklist": [
            f"关于 {topic}，这 5 条建议价值百万",
            f"{topic} 最全指南：从入门到精通的完整清单",
            f"搞懂 {topic}，看这一篇就够了",
        ],
        "pain": [
            f"为什么你的 {topic} 总是做不好？90% 的人都踩了这个坑",
            f"别再被误导了：{topic} 的真相",
            f"我花了 3 个月才明白的 {topic} 核心逻辑",
        ],
        "compare": [
            f"{topic} 终极对比：选 A 还是选 B？一文说清",
            f"花了两周实测，终于搞清了 {topic} 的选型答案",
            f"{topic} 选型指南：不看这篇，你可能选错了",
        ],
        "narrative": [
            f"从 0 到 1：我在 {topic} 路上踩过的坑和收获的光",
            f"那个让我重新认识 {topic} 的深夜",
            f"一个关于 {topic} 的故事，和它教我的事",
        ],
    }

    candidates = templates.get(framework, templates["checklist"])
    return [
        {"text": text, "score": 90 - i * 5} for i, text in enumerate(candidates)
    ]


def _generate_image_suggestions(topic: str) -> list[dict]:
    """Generate mock image suggestions for the article.

    TODO: Replace with actual image generation once integrated.
    """
    return [
        {
            "url": f"https://example.com/images/{topic.replace(' ', '_')}_cover.jpg",
            "caption": f"{topic} — 封面图",
            "position": "cover",
        },
        {
            "url": f"https://example.com/images/{topic.replace(' ', '_')}_inline_1.jpg",
            "caption": "内文配图 1",
            "position": "inline",
        },
        {
            "url": f"https://example.com/images/{topic.replace(' ', '_')}_inline_2.jpg",
            "caption": "内文配图 2",
            "position": "inline",
        },
    ]


__all__ = [
    "register_tools",
    "Article",
    "FrameworkType",
    "WritingStyle",
    "generate_outline",
    "generate_draft",
    "enhance_article",
    "get_framework_prompt",
    "get_framework_structure",
    "get_style_prompt",
    "get_default_framework",
    "get_default_style",
    "build_style_system_prompt",
]
