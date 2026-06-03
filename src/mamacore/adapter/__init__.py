"""公众号排版适配模块 —— 容器语法 + 主题管理 + SEO 优化。

整合了 wewrite 的 18 个排版主题和完整 Markdown→HTML 转换器。
"""

from .wechat_format import render_containers, markdown_to_wechat_html
from .theme import list_themes, load_theme
from .seo import analyze_seo, extract_keywords, optimize_title_for_seo


def register_tools(mcp) -> None:
    """向 MCP Server 注册本模块的所有 tools。"""

    @mcp.tool()
    async def mama_format_article(
        article_md: str,
        theme: str = "professional-clean",
    ) -> str:
        """将 Markdown 文章转换为公众号 HTML 格式，支持容器语法和排版主题。

        支持的容器语法:
        - :::dialogue ... :::end → 对话气泡
        - :::timeline ... :::end → 时间线
        - :::callout variant=info/warning/success/tip ... :::end → 引用框
        - :::code language=python ... :::end → 代码块

        可用主题: professional-clean, sspai, bytedance, minimal, newspaper,
        focus-red, bold-green, bold-navy, tech-modern, github, warm-editorial,
        elegant-rose, minimal-gold, ink, midnight, bauhaus, bytedance, focus-red

        Args:
            article_md: Markdown 格式文章
            theme: 排版主题名称（可用主题调用 mama_list_themes 查看）
        """
        theme_config = load_theme(theme)
        html = markdown_to_wechat_html(article_md, theme_config.get("css") if theme_config else None)

        # 统计转换信息
        container_count = article_md.count(":::") // 2
        char_count = len(html)

        return (
            f"## 排版完成\n\n"
            f"- 主题: {theme}\n"
            f"- 容器数量: {container_count}\n"
            f"- HTML 长度: {char_count} 字符\n\n"
            f"```\n{html[:2000]}\n```\n\n"
            f"{'HTML 内容较长，已截取前 2000 字符。完整内容可直接使用。' if len(html) > 2000 else '以上为完整 HTML。'}"
        )

    @mcp.tool()
    async def mama_list_themes() -> str:
        """列出所有可用的公众号排版主题。"""
        themes = list_themes()
        lines = ["## 可用排版主题\n"]
        for name in themes:
            theme = load_theme(name)
            desc = theme.get("description", "") if theme else ""
            lines.append(f"- **{name}**: {desc}")
        return "\n".join(lines)

    @mcp.tool()
    async def mama_seo_check(
        article_md: str,
        keywords: str,
    ) -> str:
        """分析文章的微信搜一搜 SEO 表现，给出优化建议。

        Args:
            article_md: Markdown 格式文章
            keywords: 目标关键词，多个用逗号分隔
        """
        kw_list = [k.strip() for k in keywords.split(",") if k.strip()]
        result = analyze_seo(article_md, kw_list)

        lines = [f"## SEO 分析报告 (评分: {result['score']}/100)\n"]

        # 基础检查
        cl = result["checklist"]
        lines.append("### 检查清单")
        lines.append(f"- 标题长度合格 (<=64): {'✅' if cl['title_length_ok'] else '❌'}")
        lines.append(f"- 标题最佳长度 (<=26): {'✅' if cl['title_optimal'] else '⚠️'}")
        lines.append(f"- 标题包含关键词: {'✅' if cl['has_keywords_in_title'] else '❌'}")
        lines.append(f"- 首段包含关键词: {'✅' if cl['has_keywords_in_first_para'] else '❌'}")
        lines.append("")

        # 关键词密度
        lines.append("### 关键词密度")
        for kw, data in result["keyword_density"].items():
            status = "✅" if 0.02 <= data["density"] <= 0.05 else "⚠️"
            lines.append(f"- {kw}: {data['count']} 次 ({data['density']:.2f}%) {status}")
        lines.append("")

        if result["issues"]:
            lines.append("### 问题")
            for issue in result["issues"]:
                lines.append(f"- ❌ {issue}")
            lines.append("")

        if result["suggestions"]:
            lines.append("### 建议")
            for s in result["suggestions"]:
                lines.append(f"- 💡 {s}")
            lines.append("")

        return "\n".join(lines)

    @mcp.tool()
    async def mama_list_personas() -> str:
        """列出所有可用的写作人格 (Persona)。"""
        from mamacore.writer.style_engine import list_personas, load_persona

        personas = list_personas()
        lines = ["## 可用写作人格\n"]
        for name in personas:
            persona = load_persona(name)
            desc = persona.get("description", "")
            lines.append(f"- **{name}**: {desc}")
        return "\n".join(lines)
