"""图片生成抽象接口 —— 多后端统一调度。"""
import os
import json
import httpx
from pathlib import Path
from typing import Optional
from abc import ABC, abstractmethod

from openai import AsyncOpenAI


class ImageResult:
    def __init__(self, url: str, prompt: str, size: str):
        self.url = url
        self.prompt = prompt
        self.size = size

    def to_dict(self) -> dict:
        return {"url": self.url, "prompt": self.prompt, "size": self.size}


class ImageProvider(ABC):
    @abstractmethod
    async def generate(
        self, prompt: str, size: str = "1024x1024", style: str = "natural"
    ) -> ImageResult:
        pass


class DALLEProvider(ImageProvider):
    """DALL-E 3 后端。"""

    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY", "")
        self.model = "dall-e-3"

    async def generate(
        self, prompt: str, size: str = "1024x1024", style: str = "natural"
    ) -> ImageResult:
        if not self.api_key:
            # 无 API Key 时返回占位图，不抛异常以保证流程不中断
            return ImageResult(
                url=f"https://placeholder.image/dalle/{size.replace('x', '_')}.png",
                prompt=prompt,
                size=size,
            )

        # 接入真实 DALL-E 3 API
        client = AsyncOpenAI(api_key=self.api_key)
        response = await client.images.generate(
            model=self.model,
            prompt=prompt,
            size=size,
            quality="standard",
            style=style,
            n=1,
        )
        url = response.data[0].url
        return ImageResult(url=url, prompt=prompt, size=size)


class TongyiProvider(ImageProvider):
    """通义万相后端。"""

    def __init__(self):
        self.api_key = os.environ.get("DASHSCOPE_API_KEY", "")
        self.model = "wanx-v1"

    async def generate(
        self, prompt: str, size: str = "1024*1024", style: str = "<auto>"
    ) -> ImageResult:
        if not self.api_key:
            raise ValueError("未设置 DASHSCOPE_API_KEY 环境变量")

        # TODO: 接入真实通义万相 API
        # async with httpx.AsyncClient() as client:
        #     resp = await client.post(
        #         "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis",
        #         headers={
        #             "Authorization": f"Bearer {self.api_key}",
        #             "Content-Type": "application/json",
        #         },
        #         json={"model": self.model, "input": {"prompt": prompt}, "parameters": {"size": size}},
        #     )
        #     data = resp.json()
        #     return ImageResult(url=data["output"]["results"][0]["url"], prompt=prompt, size=size)

        return ImageResult(
            url=f"https://placeholder.image/tongyi/{size.replace('*', '_')}.png",
            prompt=prompt,
            size=size,
        )


def get_provider(name: str = "dalle") -> ImageProvider:
    """工厂方法：根据名称返回 Provider。"""
    providers = {"dalle": DALLEProvider, "tongyi": TongyiProvider}
    cls = providers.get(name.lower())
    if not cls:
        raise ValueError(f"不支持的图片后端: {name}。支持: dalle, tongyi")
    return cls()


def load_prompt_template(name: str) -> Optional[dict]:
    """加载提示词模板 JSON。"""
    prompts_dir = Path(__file__).parent / "prompts"
    path = prompts_dir / f"{name}.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return None


def list_prompt_templates() -> list[str]:
    """列出所有可用提示词模板名称。"""
    prompts_dir = Path(__file__).parent / "prompts"
    if not prompts_dir.exists():
        return []
    return [f.stem for f in prompts_dir.iterdir() if f.suffix == ".json"]
