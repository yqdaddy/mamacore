"""分享卡片生成（朋友圈分享用）。"""
from .provider import get_provider, load_prompt_template, ImageResult


async def generate_share_card(
    title: str, subtitle: str = "", provider_name: str = "dalle"
) -> dict:
    """生成朋友圈分享卡片图。

    Args:
        title: 文章标题
        subtitle: 副标题/简介
        provider_name: 后端名称
    """
    template = load_prompt_template("share_card")
    if template:
        prompt = template["base_prompt"].format(topic=title)
    else:
        prompt = f"A minimalist share card design for {title}"

    provider = get_provider(provider_name)
    result = await provider.generate(
        prompt,
        size="1024x1024",
        style=template.get("style", "vivid") if template else "vivid",
    )

    return {
        "type": "share_card",
        "url": result.url,
        "prompt": result.prompt,
        "title": title,
    }
