"""受众画像 —— 阅读时段分布、分享路径分析。"""
from collections import defaultdict
from .scraper import load_articles


def build_audience_profile(account_id: str, days: int = 30) -> dict:
    """构建受众画像。

    Returns:
        {
            "active_hours": {8: 200, 12: 500, 21: 800},  # 活跃时段分布
            "peak_hour": 21,
            "active_days": {"Monday": 300, "Tuesday": 500},  # 活跃星期分布
            "peak_day": "Tuesday",
        }
    """
    articles = load_articles(account_id, days)
    if not articles:
        return {"recommendations": ["暂无数据"]}

    hour_reads: dict[int, int] = defaultdict(int)
    day_reads: dict[str, int] = defaultdict(int)
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    for a in articles:
        hour_reads[a.published_at.hour] += a.read_count
        day_name = day_names[a.published_at.weekday()]
        day_reads[day_name] += a.read_count

    peak_hour = max(hour_reads, key=hour_reads.get) if hour_reads else 12
    peak_day = max(day_reads, key=day_reads.get) if day_reads else "Tuesday"

    return {
        "active_hours": dict(sorted(hour_reads.items())),
        "peak_hour": peak_hour,
        "active_days": dict(day_reads),
        "peak_day": peak_day,
        "recommendations": [
            f"受众最活跃的时间是 {peak_hour}:00",
            f"受众最活跃的星期是 {peak_day}",
            "建议在此时段发布文章以获得最大阅读",
        ],
    }
