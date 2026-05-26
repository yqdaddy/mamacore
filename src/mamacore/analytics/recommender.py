"""内容策略推荐引擎 —— 综合所有分析数据，生成"下周该写什么"的策略报告。"""
from .topic_analysis import get_topic_heatmap
from .title_ab import analyze_title_patterns
from .viral_patterns import analyze_viral_patterns
from .content_calendar import generate_content_calendar


def generate_content_strategy(account_id: str, days_ahead: int = 7) -> dict:
    """生成下周内容策略报告。

    Returns:
        {
            "hot_topics": ["当前热点中与你账号相关的话题"],
            "untapped_topics": ["你还没写过的热门话题"],
            "best_titles": ["基于历史表现的标题建议"],
            "publish_schedule": ["最佳发文时间"],
            "framework_suggestion": "推荐写作框架",
            "style_adjustment": "风格微调建议",
        }
    """
    # 收集各模块数据
    heatmap = get_topic_heatmap(account_id)
    title_patterns = analyze_title_patterns(account_id)
    viral = analyze_viral_patterns(account_id)
    calendar = generate_content_calendar(account_id, days_ahead)

    # 综合策略
    hot_topics = heatmap.get("hot_topics", [])
    best_pattern = title_patterns.get("best_performing", "")

    # 从未写过但表现差的话题（机会点：如果之前写太少，可能只是样本不够）
    untapped = []
    for topic in heatmap.get("cold_topics", []):
        if topic.get("article_count", 0) == 0:
            untapped.append(topic)

    # 推荐框架（基于爆款分析）
    framework_suggestion = "checklist"  # 默认
    if viral.get("viral_articles"):
        # 简化：从爆款文章推断
        framework_suggestion = "checklist"

    return {
        "account_id": account_id,
        "days_ahead": days_ahead,
        "hot_topics": [t["topic"] for t in hot_topics[:3]],
        "untapped_topics": untapped[:3],
        "best_title_pattern": best_pattern,
        "publish_schedule": [c for c in calendar if c.get("recommended")][:3],
        "framework_suggestion": framework_suggestion,
        "best_publish_hour": viral.get("best_publish_hour", 21),
        "summary": (
            f"建议本周发布 {min(days_ahead, 3)} 篇文章，"
            f"优先选择「{', '.join(t['topic'] for t in hot_topics[:2])}」话题，"
            f"使用「{best_pattern or '数字+痛点'}」标题模式，"
            f"在 {viral.get('best_publish_hour', 21)}:00 发布。"
        ),
    }
