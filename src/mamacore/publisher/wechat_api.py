"""公众号 API 封装 -- 服务号 + 个人号双适配。

微信公众号 API 文档: https://developers.weixin.qq.com/doc/offiaccount/Getting_Started/Overview.html

重要限制:
- 已认证服务号：完整 API 权限（上传素材、创建草稿、直接发布）
- 个人订阅号（2025年7月后）：仅能创建草稿，需手动点发布
"""
import os
import json
import time
import httpx
import asyncio
from pathlib import Path
from typing import Optional

WECHAT_APP_ID = os.environ.get("MAMA_WECHAT_APP_ID", "")
WECHAT_APP_SECRET = os.environ.get("MAMA_WECHAT_APP_SECRET", "")
WECHAT_BASE = "https://api.weixin.qq.com"

# Token 缓存路径
_TOKEN_CACHE_DIR = Path(__file__).parent.parent.parent.parent / "data" / "cache"
_TOKEN_CACHE_FILE = _TOKEN_CACHE_DIR / "wechat_token.json"
_TOKEN_REFRESH_BUFFER = 300  # token 过期前 5 分钟刷新


def _load_cached_token() -> Optional[dict]:
    """加载缓存的 access_token。"""
    if not _TOKEN_CACHE_FILE.exists():
        return None
    try:
        with open(_TOKEN_CACHE_FILE) as f:
            data = json.load(f)
        if time.time() < data.get("expires_at", 0) - _TOKEN_REFRESH_BUFFER:
            return data
    except (json.JSONDecodeError, KeyError):
        pass
    return None


def _save_cached_token(token: str, expires_in: int = 7200) -> None:
    """保存 access_token 到缓存。"""
    _TOKEN_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(_TOKEN_CACHE_FILE, "w") as f:
        json.dump({
            "access_token": token,
            "expires_at": time.time() + expires_in,
        }, f)


async def _wechat_request(
    url: str,
    method: str = "GET",
    params: Optional[dict] = None,
    json_body: Optional[dict] = None,
    files: Optional[dict] = None,
    max_retries: int = 2,
) -> dict:
    """带重试和 token 自动刷新的微信 API 请求。"""
    for attempt in range(max_retries + 1):
        async with httpx.AsyncClient(timeout=30) as client:
            kwargs: dict = {"params": params}
            if json_body:
                kwargs["json"] = json_body
            if files:
                kwargs["files"] = files

            if method == "GET":
                resp = await client.get(url, **kwargs)
            elif method == "POST":
                resp = await client.post(url, **kwargs)
            else:
                raise ValueError(f"不支持的 HTTP 方法: {method}")

            resp.raise_for_status()
            data = resp.json()

            # 微信 API 错误码处理
            errcode = data.get("errcode", 0)
            if errcode == 0:
                return data
            elif errcode == 40001 or errcode == 42001:
                # token 过期或无效，清除缓存重试
                if _TOKEN_CACHE_FILE.exists():
                    _TOKEN_CACHE_FILE.unlink(missing_ok=True)
                if attempt < max_retries:
                    await asyncio.sleep(1)
                    continue
            elif errcode == 45009:
                raise WeChatAPIError(f"API 调用频率超限: {data.get('errmsg', '')}")
            elif errcode == 40013:
                raise WeChatAPIError(f"AppID 无效: {data.get('errmsg', '')}")

            # 其他错误，最后一次尝试时抛出
            if attempt == max_retries:
                raise WeChatAPIError(f"微信 API 错误 {errcode}: {data.get('errmsg', 'unknown')}")

            await asyncio.sleep(2 ** attempt)

    raise WeChatAPIError("请求失败：超过最大重试次数")


class WeChatAPIError(Exception):
    """微信公众号 API 调用异常。"""
    pass


async def get_access_token() -> str:
    """获取 access_token，带 7200 秒缓存和自动刷新。"""
    if not WECHAT_APP_ID or not WECHAT_APP_SECRET:
        raise WeChatAPIError("未设置 MAMA_WECHAT_APP_ID 或 MAMA_WECHAT_APP_SECRET 环境变量")

    # 先查缓存
    cached = _load_cached_token()
    if cached:
        return cached["access_token"]

    # 请求新 token
    data = await _wechat_request(
        f"{WECHAT_BASE}/cgi-bin/token",
        params={
            "grant_type": "client_credential",
            "appid": WECHAT_APP_ID,
            "secret": WECHAT_APP_SECRET,
        },
    )

    token = data.get("access_token")
    if not token:
        raise WeChatAPIError(f"获取 token 失败: {data.get('errmsg', 'unknown')}")

    # 缓存 token
    expires_in = data.get("expires_in", 7200)
    _save_cached_token(token, expires_in)
    return token


async def upload_material(file_path: str, material_type: str = "image") -> dict:
    """上传永久素材（仅服务号）。

    Args:
        file_path: 文件路径
        material_type: 素材类型 (image/voice/video/thumb)

    Raises:
        FileNotFoundError: 文件不存在
        WeChatAPIError: API 调用失败
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"素材文件不存在: {file_path}")

    token = await get_access_token()
    with open(path, "rb") as f:
        return await _wechat_request(
            f"{WECHAT_BASE}/cgi-bin/material/add_material",
            method="POST",
            params={"access_token": token, "type": material_type},
            files={"media": f},
        )


async def create_draft(
    title: str,
    content: str,
    cover_media_id: str = "",
    author: str = "",
) -> str:
    """创建草稿（服务号 + 个人号均可）。

    Args:
        title: 文章标题
        content: 文章 HTML 内容
        cover_media_id: 封面图 media_id（可选）
        author: 作者名（可选）

    Returns:
        草稿的 media_id

    Raises:
        WeChatAPIError: 创建失败
    """
    token = await get_access_token()
    articles_data = [{
        "title": title,
        "content": content,
        "digest": content[:120],
        "show_cover_pic": 1 if cover_media_id else 0,
        "media_id": cover_media_id,
        "author": author,
        "content_source_url": "",
    }]

    data = await _wechat_request(
        f"{WECHAT_BASE}/cgi-bin/draft/add",
        method="POST",
        params={"access_token": token},
        json_body={"articles": articles_data},
    )
    return data["media_id"]


async def publish(media_id: str) -> dict:
    """直接发布（仅服务号支持）。

    Args:
        media_id: 草稿的 media_id

    Returns:
        发布结果

    Raises:
        WeChatAPIError: 发布失败
    """
    token = await get_access_token()
    return await _wechat_request(
        f"{WECHAT_BASE}/cgi-bin/freepublish/submit",
        method="POST",
        params={"access_token": token},
        json_body={"media_id": media_id},
    )


async def get_account_type() -> str:
    """检测公众号账号类型（服务号 / 个人号）。

    简化实现：检查环境变量 MAMA_ACCOUNT_TYPE=service|personal
    """
    return os.environ.get("MAMA_ACCOUNT_TYPE", "personal")
