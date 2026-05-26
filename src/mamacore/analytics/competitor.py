"""竞品对标分析 —— 对比竞品账号，找到内容差距和机会点。"""
from .scraper import load_articles
from .topic_analysis import get_topic_heatmap


def compare_competitors(my_account: str, competitor_accounts: list[str], days: int = 30) -> dict:
    """对比竞品账号。

    Returns:
        {
            "my_heatmap": {...},
            "competitor_heatmaps": {"竞品A": {...}, "竞品B": {...}},
            "gaps": ["竞品A写了但你没写的话题"],
            "opportunities": ["内容空白点"],
        }
    """
    my_heatmap = get_topic_heatmap(my_account, days)
    my_topics = set(t["topic"] for t in my_heatmap["topics"])

    competitor_data = {}
    all_competitor_topics: set = set()

    for comp_id in competitor_accounts:
        comp_heatmap = get_topic_heatmap(comp_id, days)
        competitor_data[comp_id] = comp_heatmap
        all_competitor_topics.update(t["topic"] for t in comp_heatmap["topics"])

    # 找到竞品写了但你没写的话题
    gaps = list(all_competitor_topics - my_topics)

    return {
        "my_account": my_account,
        "my_topic_count": len(my_topics),
        "my_top_topics": my_heatmap["hot_topics"][:3],
        "competitors": competitor_accounts,
        "gaps": gaps,
        "opportunities": [f"话题「{g}」竞品有覆盖，你尚未涉及" for g in gaps[:5]],
    }
