"""多平台同步 -- Wechatsync CLI 封装。

Wechatsync: https://github.com/wechatsync/Wechatsync
支持 27+ 平台: 知乎/头条/百家号/CSDN/掘金/简书等
"""
import asyncio
import subprocess
from typing import Optional


async def sync_to_platforms(
    article_path: str,
    platforms: list[str],
    cookie_dir: str = "",
) -> dict:
    """同步文章到多个平台。

    Args:
        article_path: 文章 Markdown/HTML 文件路径
        platforms: 目标平台列表 (zhihu/toutiao/baijiahao/csdn/juejin)
        cookie_dir: 浏览器 cookie 目录（Wechatsync 使用登录态）
    """
    results = {}
    cookie_flag = f"--cookie-dir={cookie_dir}" if cookie_dir else ""

    for platform in platforms:
        cmd = f"npx @wechatsync/cli publish --platform {platform} --file {article_path} {cookie_flag}".strip()
        try:
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode == 0:
                results[platform] = {"status": "success", "output": stdout.decode()}
            else:
                results[platform] = {"status": "failed", "error": stderr.decode()}
        except Exception as e:
            results[platform] = {"status": "error", "error": str(e)}

    return results
