#!/usr/bin/env python3
"""dailyhot-skill 集成 —— 自动管理 Node.js 服务进程，无需手动启动。

设计理念：
- 首次调用时自动启动 localhost:6688 服务
- 后续调用复用已有服务
- 进程退出时自动清理

使用方式：
    client = DailyHotClient()  # 自动启动服务
    topics = await client.get_hot_topics("weibo", count=20)
"""

import json
import os
import signal
import subprocess
import time
import sys
import atexit
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx

from .models import HotTopic, HotTopicList

# 服务配置
SERVICE_DIR = Path(__file__).parent.parent.parent.parent / "services" / "dailyhot"
SERVICE_PORT = int(os.environ.get("DAILYHOT_PORT", "6688"))
BASE_URL = f"http://localhost:{SERVICE_PORT}"

# 全局进程引用
_server_process: Optional[subprocess.Popen] = None


def _start_server() -> bool:
    """启动 dailyhot-api Node.js 服务（后台进程）。

    仅在首次调用时启动，后续复用。
    """
    global _server_process

    # 已启动则不重复
    if _server_process is not None and _server_process.poll() is None:
        return True

    # 检查是否已在运行
    try:
        httpx.get(f"{BASE_URL}/all", timeout=2)
        return True
    except (httpx.ConnectError, httpx.TimeoutException):
        pass

    # 检查依赖是否已安装
    if not (SERVICE_DIR / "node_modules").exists():
        print("[dailyhot] 正在安装 Node.js 依赖...", file=sys.stderr)
        subprocess.run(
            ["npm", "install"],
            cwd=str(SERVICE_DIR),
            capture_output=True,
            text=True,
        )

    # 启动服务
    print(f"[dailyhot] 正在启动热榜服务 (端口 {SERVICE_PORT})...", file=sys.stderr)
    _server_process = subprocess.Popen(
        ["node", "scripts/start-server.mjs", str(SERVICE_PORT)],
        cwd=str(SERVICE_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # 等待服务就绪（最多 10 秒）
    for _ in range(20):
        time.sleep(0.5)
        try:
            resp = httpx.get(f"{BASE_URL}/all", timeout=2)
            if resp.status_code == 200:
                print(f"[dailyhot] 热榜服务就绪", file=sys.stderr)
                return True
        except (httpx.ConnectError, httpx.TimeoutException):
            continue

    print(f"[dailyhot] 服务启动超时", file=sys.stderr)
    return False


def _cleanup_server():
    """进程退出时自动清理服务。"""
    global _server_process
    if _server_process is not None and _server_process.poll() is None:
        _server_process.send_signal(signal.SIGTERM)
        _server_process = None


# 注册退出清理
atexit.register(_cleanup_server)


class DailyHotClient:
    """dailyhot-skill 客户端 —— 自动管理服务，无需手动启动。"""

    def __init__(self, timeout: float = 15.0):
        self.timeout = timeout

    @staticmethod
    def _parse_items(raw_data: list[dict], source: str) -> list[HotTopic]:
        topics = []
        for item in raw_data:
            hot_score = item.get("hot", 0) or 0
            if isinstance(hot_score, str):
                hot_score = int(hot_score) if hot_score.isdigit() else 0

            ts = item.get("timestamp", 0) or item.get("time", 0)
            published_at = None
            if ts:
                try:
                    published_at = datetime.fromtimestamp(ts)
                except (ValueError, OSError):
                    pass

            topics.append(HotTopic(
                title=item.get("title", ""),
                description=item.get("description", "") or item.get("desc", "") or "",
                url=item.get("url", "") or "",
                source=source,
                hot_score=hot_score,
                published_at=published_at,
            ))
        return topics

    async def get_hot_topics(
        self,
        source: str = "weibo",
        count: int = 20,
    ) -> HotTopicList:
        """查询热榜。自动启动服务（如需），无需手动干预。"""
        count = max(1, min(50, count))

        # 自动启动服务
        if not _start_server():
            raise ConnectionError(
                f"无法启动 dailyhot 服务 (端口 {SERVICE_PORT})。\n"
                f"请检查 Node.js 是否已安装: node --version"
            )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{BASE_URL}/{source}"
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
        except httpx.ConnectError:
            raise ConnectionError(
                f"无法连接到热榜服务 ({BASE_URL})。\n"
                f"请检查 Node.js 是否已安装并重试。"
            )

        raw_data = data.get("data", [])
        topics = self._parse_items(raw_data[:count], source)

        return HotTopicList(
            topics=topics,
            source=source,
            fetched_at=datetime.now(),
            total=len(topics),
        )
