"""智能发文排期 —— 结合热点 + 历史表现生成发文建议。"""
from datetime import datetime, timedelta
from .viral_patterns import analyze_viral_patterns
from .audience_profile import build_audience_profile


def generate_content_calendar(account_id: str, days_ahead: int = 7) -> list[dict]:
    """生成未来 N 天的发文排期建议。

    Returns:
        [
            {"date": "2026-05-25", "hour": 21, "topic_suggestion": "AI Agent", "framework": "checklist"},
        ]
    """
    viral = analyze_viral_patterns(account_id)
    audience = build_audience_profile(account_id)

    best_hour = viral.get("best_publish_hour", audience.get("peak_hour", 21))
    best_day = audience.get("peak_day", "Tuesday")

    # 简单排期：建议在工作日的最佳时间发文
    schedule = []
    today = datetime.now()
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    for i in range(days_ahead):
        date = today + timedelta(days=i)
        day_name = day_names[date.weekday()]

        # 优先推荐受众最活跃的日子
        if day_name == best_day or day_name in ["Tuesday", "Wednesday", "Thursday"]:
            schedule.append({
                "date": date.strftime("%Y-%m-%d"),
                "day": day_name,
                "hour": best_hour,
                "recommended": True,
            })
        else:
            schedule.append({
                "date": date.strftime("%Y-%m-%d"),
                "day": day_name,
                "hour": best_hour,
                "recommended": False,
            })

    return schedule
