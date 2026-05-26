"""内文配图生成。"""
from .provider import get_provider, load_prompt_template, ImageResult


async def generate_inline(
    topic: str,
    section: str = "",
    count: int = 2,
    style: str = "lifestyle",
    provider_name: str = "dalle",
) -> list[dict]:
    """生成文章内文配图。

    Args:
        topic: 文章主题
        section: 对应文章段落标题（为空则自动生成）
        count: 生成数量
        style: 图片风格
        provider_name: 后端名称
    """
    template = load_prompt_template(f"{style}_inline") or load_prompt_template(
        "lifestyle_inline"
    )
    if template:
        base_prompt = template["base_prompt"].format(topic=topic)
        if section:
            base_prompt = f"{base_prompt}, related to: {section}"
    else:
        base_prompt = f"A warm illustration about {topic}"

    provider = get_provider(provider_name)
    images = []
    for i in range(count):
        variant = f"{base_prompt}, variation {i+1}"
        result = await provider.generate(variant, size="1024x1024")
        images.append(
            {
                "type": "inline",
                "url": result.url,
                "prompt": result.prompt,
                "section": section,
            }
        )

    return images
