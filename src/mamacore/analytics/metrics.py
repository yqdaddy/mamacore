"""指标计算 —— 标准化指标 + 趋势分析。"""
import json
from datetime import datetime, timedelta

from .models import ArticleMetrics, AccountProfile
from .scraper import load_articles


def calculate_account_profile(
    account_id: str, days: int = 30
) -> AccountProfile:
    """计算账号画像指标。"""
    articles = load_articles(account_id, days)
    if not articles:
        return AccountProfile(
            account_id=account_id,
            account_name=account_id,
            data_range_days=days,
        )

    total = len(articles)
    avg_reads = sum(a.read_count for a in articles) / total
    avg_likes = sum(a.like_count for a in articles) / total
    avg_interaction = sum(a.interaction_rate for a in articles) / total

    # 最佳发文时间
    hour_counts: dict[int, int] = {}
    for a in articles:
        h = a.published_at.hour
        hour_counts[h] = hour_counts.get(h, 0) + a.read_count
    best_hour = max(hour_counts, key=hour_counts.get) if hour_counts else 12

    return AccountProfile(
        account_id=account_id,
        account_name=account_id,
        total_articles=total,
        avg_reads=round(avg_reads, 1),
        avg_likes=round(avg_likes, 1),
        avg_interaction_rate=round(avg_interaction, 4),
        best_publish_hour=best_hour,
        data_range_days=days,
    )


def get_top_articles(
    account_id: str,
    days: int = 30,
    limit: int = 10,
    sort_by: str = "reads",
) -> list[dict]:
    """获取表现最好的文章排行。

    sort_by: reads / likes / interaction_rate / comments
    """
    articles = load_articles(account_id, days)

    sort_key = {
        "reads": lambda a: a.read_count,
        "likes": lambda a: a.like_count,
        "interaction_rate": lambda a: a.interaction_rate,
        "comments": lambda a: a.comment_count,
    }.get(sort_by, lambda a: a.read_count)

    articles.sort(key=sort_key, reverse=True)

    return [
        {
            "title": a.title,
            "reads": a.read_count,
            "likes": a.like_count,
            "comments": a.comment_count,
            "interaction_rate": round(a.interaction_rate, 4),
            "published_at": a.published_at.strftime("%Y-%m-%d %H:%M"),
        }
        for a in articles[:limit]
    ]


def get_trend(account_id: str, days: int = 30) -> list[dict]:
    """获取阅读量趋势（按天聚合）。"""
    articles = load_articles(account_id, days)
    daily: dict[str, int] = {}
    for a in articles:
        date_str = a.published_at.strftime("%Y-%m-%d")
        daily[date_str] = daily.get(date_str, 0) + a.read_count

    return [{"date": d, "reads": r} for d, r in sorted(daily.items())]
