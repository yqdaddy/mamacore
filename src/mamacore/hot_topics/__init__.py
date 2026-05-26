"""热点抓取模块 —— 双数据源。

1. 公众号爆款文章 (gzh.litpp.com) — 专注公众号爆款内容
2. DailyHotApi 热榜聚合 (本地服务) — 30+ 平台通用热榜
"""

import os

from .models import HotTopic, HotTopicList
from .gzh_api import GzhExplosiveClient
from .dailyhot_service import DailyHotClient


def register_tools(mcp) -> None:
    """向 MCP Server 注册本模块的所有 tools。"""

    @mcp.tool()
    async def mama_hot_topics(
        source: str = "gzh",
        keyword: str = "",
        count: int = 10,
        days: int = 7,
    ) -> str:
        """查询热点/爆款文章。

        支持两个数据源：
        - source="gzh": 公众号爆款文章（低粉高阅读/阅读靠前/原创/数据增长）
        - source="weibo/zhihu/toutiao/baidu/douyin/bilibili/...": DailyHotApi 热榜

        公众号爆款无需部署，直接调用。
        DailyHotApi 热榜需先启动本地服务: services/dailyhot/start.sh

        Args:
            source: 数据源。gzh=公众号爆款，其他=DailyHotApi 对应平台
            keyword: 公众号搜索关键词（仅 source=gzh 时有效）
            count: 返回数量上限 (1-20)
            days: 时间范围（天），仅 source=gzh 时有效
        """
        if source == "gzh":
            return await _query_gzh_explosive(keyword, count, days)
        else:
            return await _query_dailyhot(source, count)


async def _query_gzh_explosive(keyword: str, count: int, days: int) -> str:
    """查询公众号爆款文章。"""
    from datetime import datetime, timedelta

    count = max(1, min(20, count))
    days = max(1, min(30, days))
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    client = GzhExplosiveClient()

    try:
        result = await client.get_explosive_articles(
            keyword=keyword,
            max_items=count,
            start_date=start_date,
        )
    except Exception as e:
        return f"爆款查询失败：{e}\n\n请检查网络连接或稍后重试。"

    if not result.topics:
        return (
            f"## 公众号爆款 ({keyword or '全站热门'}, 近 {days} 天)\n\n"
            f"暂无爆款数据。建议更换关键词，如：职场干货、育儿经验、情感故事。"
        )

    time_label = f"近 {days} 天" if days > 1 else "近 1 天"
    lines = [
        f"## 公众号爆款 ({keyword or '全站热门'}, {time_label})",
        f"查询时间: {result.fetched_at.strftime('%Y-%m-%d %H:%M:%S')}",
        f"共 {result.total} 条",
        "",
        "收录依据：低粉高阅读、阅读靠前、数据增长中、原创靠前",
        "",
    ]

    for i, topic in enumerate(result.topics, 1):
        lines.append(f"{i}. {topic.title}")
        lines.append(f"   {topic.description}")
        if topic.url:
            lines.append(f"   {topic.url}")
        lines.append("")

    return "\n".join(lines)


async def _query_dailyhot(source: str, count: int) -> str:
    """查询 DailyHotApi 热榜。"""
    service_url = os.environ.get("DAILYHOT_API_URL", "http://localhost:6688")
    count = max(1, min(50, count))
    client = DailyHotClient(base_url=service_url)

    try:
        result = await client.get_hot_topics(source, count)
    except ConnectionError as e:
        return (
            f"热榜查询失败：{e}\n\n"
            f"DailyHotApi 热榜需要启动本地服务：\n"
            f"  cd services/dailyhot && npm install && npm start\n\n"
            f"可用平台: weibo/zhihu/toutiao/baidu/douyin/bilibili/36kr/juejin/csdn 等"
        )
    except Exception as e:
        return f"热榜查询失败：{e}"

    if not result.topics:
        return f"## {source} 热榜\n\n暂无数据。"

    platform_names = {
        "weibo": "微博热搜", "zhihu": "知乎热榜", "toutiao": "头条热榜",
        "baidu": "百度热搜", "douyin": "抖音热点", "bilibili": "B站热门",
        "36kr": "36氪热榜", "juejin": "掘金热榜", "csdn": "CSDN热榜",
        "tieba": "贴吧热榜", "douban": "豆瓣讨论", "ithome": "IT之家",
    }
    platform_name = platform_names.get(source, f"{source}热榜")

    lines = [
        f"## {platform_name}",
        f"更新时间: {result.fetched_at.strftime('%Y-%m-%d %H:%M:%S')}",
        f"共 {result.total} 条",
        "",
    ]

    for i, topic in enumerate(result.topics, 1):
        hot = f"[{topic.hot_score}]" if topic.hot_score > 0 else ""
        lines.append(f"{i}. {hot} {topic.title}")
        if topic.description:
            lines.append(f"   {topic.description[:100]}")
        if topic.url:
            lines.append(f"   {topic.url}")
        lines.append("")

    return "\n".join(lines)
