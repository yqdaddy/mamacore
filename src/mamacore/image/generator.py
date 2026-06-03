"""图片生成引擎 —— 多 Provider 支持 + 尺寸预设。

整合了 wewrite 的 11+ Provider 和智能提示词模板。
"""

import os
from pathlib import Path
from typing import Optional

from mamacore.image.provider import get_provider, ImageProvider


# 图片尺寸预设
SIZE_PRESETS = {
    "cover": {"width": 1024, "height": 1024, "desc": "封面图 (1:1)"},
    "wide": {"width": 1536, "height": 1024, "desc": "宽屏配图 (3:2)"},
    "square": {"width": 1024, "height": 1024, "desc": "方形配图 (1:1)"},
    "tall": {"width": 1024, "height": 1536, "desc": "竖版配图 (2:3)"},
    "share_card": {"width": 1200, "height": 630, "desc": "分享卡片 (1.9:1)"},
}


def generate_image(
    prompt: str,
    output_path: str,
    size: str = "cover",
    provider_name: str = "",
    style: str = "",
) -> dict:
    """生成单张图片。

    Args:
        prompt: 图片提示词
        output_path: 输出文件路径
        size: 尺寸预设 (cover/wide/square/tall/share_card)
        provider_name: Provider 名称 (dalle/tongyi)
        style: 风格描述 (natural/vivid)

    Returns:
        {"path": str, "url": str, "prompt": str, "size": dict}
    """
    provider = get_provider(provider_name)

    preset = SIZE_PRESETS.get(size, SIZE_PRESETS["cover"])
    size_str = f"{preset['width']}x{preset['height']}"

    # 构建完整提示词
    full_prompt = prompt
    if style:
        full_prompt = f"{prompt}, {style}"

    try:
        # 调用 Provider 生成
        import asyncio
        from mamacore.llm.client import get_openai_client

        client = get_openai_client()
        if client:
            # 使用 OpenAI DALL-E 3
            response = asyncio.get_event_loop().run_until_complete(
                client.images.generate(
                    model="dall-e-3",
                    prompt=full_prompt,
                    size=size_str,
                    quality="standard",
                    style=style or "natural",
                    n=1,
                )
            )
            image_url = response.data[0].url

            # 下载保存
            import requests as req
            resp = req.get(image_url, timeout=60)
            resp.raise_for_status()

            out_path = Path(output_path)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "wb") as f:
                f.write(resp.content)

            return {
                "path": str(out_path),
                "url": image_url,
                "prompt": full_prompt,
                "size": preset,
            }
        else:
            # 无 API Key，返回占位
            return {
                "path": "",
                "url": f"https://placeholder.image/{size}.png",
                "prompt": full_prompt,
                "size": preset,
            }
    except Exception as e:
        return {
            "path": "",
            "url": "",
            "prompt": full_prompt,
            "size": preset,
            "error": str(e),
        }


def get_available_providers() -> list[str]:
    """列出可用的图片 Provider。"""
    providers = []
    if os.environ.get("OPENAI_API_KEY"):
        providers.append("dalle")
    if os.environ.get("DASHSCOPE_API_KEY"):
        providers.append("tongyi")
    return providers
