"""DailyHotApi HTTP 客户端 —— 热榜聚合服务 Python 封装。

支持 56+ 平台热榜：微博/知乎/头条/B站/抖音/百度/豆瓣/36Kr/CSDN 等。
需要先启动 Node.js 服务: cd services/dailyhot && npm start
"""

import httpx
import json
import time
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import HotTopic, HotTopicList

# 默认本地服务地址
DEFAULT_BASE_URL = "http://localhost:6688"

# 缓存配置
CACHE_DIR = Path(__file__).parent.parent.parent.parent / "data" / "cache" / "dailyhot"
CACHE_TTL_SECONDS = 1800  # 30 分钟缓存


class RateLimiter:
    """请求频率限制器。"""

    def __init__(self, calls_per_minute: int = 60):
        self.interval = 60.0 / calls_per_minute
        self.last_call = 0.0

    async def wait(self):
        now = time.time()
        elapsed = now - self.last_call
        if elapsed < self.interval:
            await asyncio.sleep(self.interval - elapsed)
        self.last_call = time.time()


class DailyHotClient:
    """DailyHotApi 本地服务客户端。"""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 15.0,
        use_cache: bool = True,
        calls_per_minute: int = 60,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.use_cache = use_cache
        self.rate_limiter = RateLimiter(calls_per_minute=calls_per_minute)

    def _cache_path(self, source: str) -> Path:
        return CACHE_DIR / f"hot_{source}.json"

    def _is_cache_valid(self, source: str) -> bool:
        if not self.use_cache:
            return False
        cache_file = self._cache_path(source)
        if not cache_file.exists():
            return False
        age = time.time() - cache_file.stat().st_mtime
        return age < CACHE_TTL_SECONDS

    def _load_cache(self, source: str) -> Optional[dict]:
        cache_file = self._cache_path(source)
        if cache_file.exists():
            with open(cache_file, encoding="utf-8") as f:
                return json.load(f)
        return None

    def _save_cache(self, source: str, data: list) -> None:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_file = self._cache_path(source)
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def _parse_items(raw_data: list[dict], source: str) -> list[HotTopic]:
        """解析 API 返回的数据为 HotTopic 列表。"""
        topics = []
        for item in raw_data:
            # DailyHotApi 返回格式: {title, description, url, hot, timestamp, ...}
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
                description=item.get("description", "") or "",
                url=item.get("url", "") or "",
                source=source,
                hot_score=hot_score,
                published_at=published_at,
            ))
        return topics

    async def get_sources(self) -> list[str]:
        """获取所有可用数据源列表。"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(f"{self.base_url}/all")
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", [])

    async def get_hot_topics(
        self,
        source: str = "weibo",
        count: int = 20,
    ) -> HotTopicList:
        """抓取指定平台的热点数据。

        先查缓存，缓存失效时再请求本地服务。
        每次 API 请求前会经过限流器。

        Args:
            source: 数据来源 (weibo/zhihu/toutiao/baidu/douyin/bilibili 等)
            count: 返回数量上限
        """
        count = max(1, min(50, count))

        # 先检查缓存
        if self.use_cache and self._is_cache_valid(source):
            cached = self._load_cache(source)
            if cached:
                topics = self._parse_items(cached[:count], source)
                return HotTopicList(
                    topics=topics,
                    source=source,
                    fetched_at=datetime.now(),
                    total=len(topics),
                )

        # 缓存失效，请求 API（先等限流器）
        await self.rate_limiter.wait()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.base_url}/{source}"
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
        except httpx.ConnectError:
            raise ConnectionError(
                f"无法连接到 DailyHotApi 服务 ({self.base_url})。\n"
                f"请先启动服务: cd services/dailyhot && bash start.sh"
            )

        raw_data = data.get("data", [])

        # 保存缓存
        if self.use_cache:
            self._save_cache(source, raw_data)

        topics = self._parse_items(raw_data[:count], source)

        return HotTopicList(
            topics=topics,
            source=source,
            fetched_at=datetime.now(),
            total=len(topics),
        )
