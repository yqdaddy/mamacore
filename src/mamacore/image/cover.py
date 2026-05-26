"""封面图生成 —— 根据文章主题生成公众号封面。"""
from .provider import get_provider, load_prompt_template, ImageResult


async def generate_cover(
    topic: str, style: str = "tech", provider_name: str = "dalle"
) -> dict:
    """生成公众号封面图 (1:1 正方形)。

    Args:
        topic: 文章主题
        style: 图片风格 (tech/lifestyle/business)
        provider_name: 后端名称 (dalle/tongyi)
    """
    template = load_prompt_template(f"{style}_cover") or load_prompt_template(
        "tech_cover"
    )
    if template:
        prompt = template["base_prompt"].format(topic=topic)
    else:
        prompt = f"A professional cover image about {topic}, minimalist design, modern style"

    provider = get_provider(provider_name)
    result = await provider.generate(
        prompt,
        size="1024x1024",
        style=template.get("style", "natural") if template else "natural",
    )

    return {
        "type": "cover",
        "url": result.url,
        "prompt": result.prompt,
        "size": result.size,
    }
