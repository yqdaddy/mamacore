"""图片生成模块 —— DALL-E / 通义万相多后端支持。"""

from .cover import generate_cover
from .inline import generate_inline
from .share_card import generate_share_card
from .provider import get_provider, load_prompt_template, list_prompt_templates


def register_tools(mcp) -> None:
    """向 MCP Server 注册本模块的所有 tools。"""

    @mcp.tool()
    async def mama_generate_images(
        topic: str,
        image_count: int = 3,
        style: str = "tech",
        include_cover: bool = True,
        provider: str = "",
    ) -> str:
        """为文章生成配图（封面 + 内文）。

        Args:
            topic: 文章主题
            image_count: 内文配图数量 (1-5)
            style: 图片风格 (tech/lifestyle/business)
            include_cover: 是否包含封面图
            provider: 图片后端 (dalle/tongyi，默认取配置)
        """
        import os

        provider_name = provider or os.environ.get("MAMA_IMAGE_PROVIDER", "dalle")
        image_count = max(1, min(5, image_count))
        results = []

        if include_cover:
            cover = await generate_cover(topic, style=style, provider_name=provider_name)
            results.append(cover)

        inline_images = await generate_inline(
            topic, count=image_count, style=style, provider_name=provider_name
        )
        results.extend(inline_images)

        lines = [f"## 图片生成完成 ({len(results)} 张)\n"]
        for img in results:
            lines.append(f"- **{img['type']}**: {img['url']}")
            lines.append(f"  提示词: {img['prompt']}")
        lines.append(f"\n后端: {provider_name}")
        return "\n".join(lines)

    @mcp.tool()
    async def mama_generate_cover(
        topic: str,
        style: str = "tech",
        provider: str = "",
    ) -> str:
        """生成公众号封面图 (1:1 正方形)。

        Args:
            topic: 文章主题
            style: 图片风格 (tech/lifestyle/business)
            provider: 图片后端 (dalle/tongyi)
        """
        import os

        provider_name = provider or os.environ.get("MAMA_IMAGE_PROVIDER", "dalle")
        cover = await generate_cover(topic, style=style, provider_name=provider_name)
        return (
            f"## 封面图生成\n\n"
            f"- URL: {cover['url']}\n"
            f"- 提示词: {cover['prompt']}\n"
            f"- 尺寸: {cover['size']}\n"
            f"- 后端: {provider_name}"
        )

    @mcp.tool()
    async def mama_list_image_templates() -> str:
        """列出所有可用的图片提示词模板。"""
        templates = list_prompt_templates()
        if not templates:
            return "无可用图片模板。"
        lines = ["## 可用图片提示词模板\n"]
        for name in templates:
            tpl = load_prompt_template(name)
            desc = tpl.get("description", "") if tpl else ""
            lines.append(f"- **{name}**: {desc}")
        return "\n".join(lines)
