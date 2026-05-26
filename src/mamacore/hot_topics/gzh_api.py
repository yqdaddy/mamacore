"""公众号爆款文章查询 API 客户端。

基于 gzh-flash-sentry-skill 的数据源：
API: https://gzh.litpp.com/api/skill/cozeSkill/getWxCozeSkillData
无需自行部署，直接调用即可。

支持 4 大榜单：
- 低粉高阅读榜（小账号爆款，最有参考价值）
- 阅读靠前榜（10w+ 级别）
- 原创靠前榜
- 数据增长榜（传播势头正猛的内容）
"""

import json
import sys
import time
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx

from .models import HotTopic, HotTopicList

# 公众号爆款 API 地址（无需自行部署）
API_URL = "https://gzh.litpp.com/api/skill/cozeSkill/getWxCozeSkillData"

# 缓存配置
CACHE_DIR = Path(__file__).parent.parent.parent.parent / "data" / "cache"
CACHE_TTL_SECONDS = 3600  # 爆款数据每日更新，缓存 1 小时足够


class RateLimiter:
    """简单的请求频率限制器。"""

    def __init__(self, calls_per_minute: int = 30):
        self.interval = 60.0 / calls_per_minute
        self.last_call = 0.0

    async def wait(self):
        """等待到可以发起下一次请求的时间。"""
        now = time.time()
        elapsed = now - self.last_call
        if elapsed < self.interval:
            await asyncio.sleep(self.interval - elapsed)
        self.last_call = time.time()


class GzhExplosiveClient:
    """公众号爆款文章查询客户端。"""

    def __init__(
        self,
        api_url: str = API_URL,
        timeout: float = 60.0,
        use_cache: bool = True,
        calls_per_minute: int = 30,
    ):
        self.api_url = api_url
        self.timeout = timeout
        self.use_cache = use_cache
        self.rate_limiter = RateLimiter(calls_per_minute=calls_per_minute)

    # ── 缓存相关 ──────────────────────────────────────────────

    def _cache_path(self, keyword: str, start_date: str = "") -> Path:
        safe_kw = keyword.replace("/", "_").replace("\\", "_").replace("\x00", "")[:50]
        date_suffix = start_date.replace("-", "") if start_date else "latest"
        return CACHE_DIR / f"gzh_{safe_kw}_{date_suffix}.json"

    def _is_cache_valid(self, keyword: str, start_date: str = "") -> bool:
        if not self.use_cache:
            return False
        cache_file = self._cache_path(keyword, start_date)
        if not cache_file.exists():
            return False
        age = time.time() - cache_file.stat().st_mtime
        return age < CACHE_TTL_SECONDS

    def _load_cache(self, keyword: str, start_date: str = "") -> Optional[dict]:
        cache_file = self._cache_path(keyword, start_date)
        if cache_file.exists():
            with open(cache_file, encoding="utf-8") as f:
                return json.load(f)
        return None

    def _save_cache(self, keyword: str, start_date: str, data: dict) -> None:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_file = self._cache_path(keyword, start_date)
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def _parse_count(value) -> int:
        """解析数量，支持 "17w+"、"1.5w" 格式。"""
        if value is None:
            return 0
        if isinstance(value, int):
            return value
        value_str = str(value).replace("+", "").replace(",", "").strip()
        if "w" in value_str.lower():
            value_str = value_str.lower().replace("w", "")
            try:
                return int(float(value_str) * 10000)
            except Exception:
                return 0
        try:
            return int(float(value_str))
        except Exception:
            return 0

    # ── 核心方法 ──────────────────────────────────────────────

    async def get_explosive_articles(
        self,
        keyword: str = "",
        max_items: int = 10,
        start_date: Optional[str] = None,
    ) -> HotTopicList:
        """查询公众号爆款文章。

        Args:
            keyword: 搜索关键词（空字符串表示全站热门）
            max_items: 返回数量上限 (1-20)
            start_date: 开始日期，格式 yyyy-MM-dd（默认最近 30 天）

        Returns:
            HotTopicList 包含合并排序后的爆款文章列表
        """
        max_items = max(1, min(20, max_items))

        # 先查缓存
        if self.use_cache and self._is_cache_valid(keyword, start_date or ""):
            cached = self._load_cache(keyword, start_date or "")
            if cached:
                return self._build_from_cache(cached, max_items)

        # 缓存失效，请求 API（先等限流器）
        await self.rate_limiter.wait()

        params = {"keyword": keyword, "source": "mamacore"}
        if start_date:
            params["startDate"] = start_date

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
        }

        last_error = None
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.get(self.api_url, params=params, headers=headers)
                    resp.raise_for_status()
                    data = resp.json()

                if "data" not in data:
                    raise ValueError(f"API 错误: {data.get('msg', '未知错误')}")

                result_data = data["data"]

                # 保存缓存
                if self.use_cache:
                    self._save_cache(keyword, start_date or "", data)

                # 解析并返回
                return self._parse_and_merge(result_data, keyword, max_items)

            except Exception as e:
                last_error = e
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                continue

        raise ConnectionError(
            f"公众号爆款 API 请求失败: {last_error}\n"
            f"请检查网络连接或稍后重试。"
        )

    def _parse_and_merge(self, result_data: dict, keyword: str, max_items: int) -> HotTopicList:
        """解析 API 返回的 4 大榜单数据，合并排序。"""
        categories = [
            ("lowPowderExplosiveArticle", "低粉高阅读"),
            ("tenWReadingRank", "阅读靠前"),
            ("originalRank", "原创靠前"),
            ("oneWReadingRank", "数据增长中"),
        ]

        # 合并去重
        seen_ids = set()
        all_items = []
        for cat_key, cat_name in categories:
            items = result_data.get(cat_key, [])
            for item in items:
                photo_id = item.get("photoId", "")
                if photo_id and photo_id not in seen_ids:
                    seen_ids.add(photo_id)
                    all_items.append((cat_key, cat_name, item))

        # 评分排序
        scored = []
        for cat_key, cat_name, item in all_items:
            score = self._calculate_score(item, cat_key)
            scored.append({
                "cat_key": cat_key,
                "cat_name": cat_name,
                "item": item,
                "score": score,
            })

        scored.sort(key=lambda x: x["score"], reverse=True)

        # 保证分类多样性（轮流选取）
        final = self._ensure_diversity(scored, max_items)

        # 构建 HotTopicList
        topics = []
        for entry in final:
            item = entry["item"]
            title = item.get("title", "") or (item.get("summary", "") or "")[:50]
            clicks = self._parse_count(item.get("clicksCount", 0))
            photo_id = item.get("photoId", "")
            pub_time = item.get("publicTime", "")

            topics.append(HotTopic(
                title=title,
                description=f"阅读 {clicks} | {entry['cat_name']} | 粉丝 {item.get('fans', 0)}",
                url=f"https://mp.weixin.qq.com/s/{photo_id}" if photo_id else "",
                source="公众号爆款",
                hot_score=clicks,
                published_at=datetime.fromisoformat(pub_time) if pub_time and len(pub_time) >= 10 else None,
            ))

        return HotTopicList(
            topics=topics,
            source="公众号爆款",
            fetched_at=datetime.now(),
            total=len(topics),
        )

    def _calculate_score(self, item: dict, cat_key: str) -> float:
        """计算数据表现分数（0-100）。"""
        import math

        like_num = self._parse_count(item.get("likeCount", 0))
        comment_num = self._parse_count(item.get("useCommentCount", 0) or item.get("commentCount", 0))
        share_num = self._parse_count(item.get("shareCount", 0))
        interactive_num = self._parse_count(item.get("interactiveCount", 0))
        clicks_num = self._parse_count(item.get("clicksCount", 0))

        score = (
            math.log10(like_num + 1) * 15 +
            math.log10(share_num + 1) * 20 +
            math.log10(comment_num + 1) * 18 +
            math.log10(interactive_num + 1) * 12
        )

        if clicks_num > 0:
            score += min(15, math.log10(clicks_num + 1) * 3)

        # 低粉高阅读额外加分
        if cat_key == "lowPowderExplosiveArticle":
            fans = self._parse_count(item.get("fans", 0))
            if 0 < fans < 10000:
                score += 8
            elif 0 < fans < 50000:
                score += 5

        # 10w+ 加分
        if cat_key == "tenWReadingRank" and clicks_num >= 100000:
            score += 10

        return min(100, score)

    def _ensure_diversity(self, scored_items: list, max_items: int) -> list:
        """保证分类多样性，轮流从各榜单选取。"""
        if not scored_items:
            return []

        # 按分类分组
        cat_items: dict = {}
        for item in scored_items:
            cat_key = item["cat_key"]
            if cat_key not in cat_items:
                cat_items[cat_key] = []
            cat_items[cat_key].append(item)

        # 轮流选取
        result = []
        used_indices = {cat_key: 0 for cat_key in cat_items}
        sorted_cats = sorted(
            cat_items.keys(),
            key=lambda k: cat_items[k][0]["score"] if cat_items[k] else 0,
            reverse=True,
        )

        while len(result) < max_items:
            added = False
            for cat_key in sorted_cats:
                if used_indices[cat_key] < len(cat_items[cat_key]):
                    result.append(cat_items[cat_key][used_indices[cat_key]])
                    used_indices[cat_key] += 1
                    added = True
                    if len(result) >= max_items:
                        break
            if not added:
                break

        result.sort(key=lambda x: x["score"], reverse=True)
        return result

    def _build_from_cache(self, cached: dict, max_items: int) -> HotTopicList:
        """从缓存数据构建 HotTopicList。"""
        result_data = cached.get("data", {})
        return self._parse_and_merge(result_data, cached.get("keyword", ""), max_items)
