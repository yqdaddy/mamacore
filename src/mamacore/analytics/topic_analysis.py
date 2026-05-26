"""选题热力图 —— 统计各话题的平均阅读量、互动率，发现"写了就火"和"写了就扑"的话题。"""
import json
from collections import defaultdict
from .scraper import load_articles


def get_topic_heatmap(account_id: str, days: int = 30) -> dict:
    """生成选题热力图。

    Returns:
        {
            "topics": [
                {"topic": "AI", "avg_reads": 5000, "avg_interaction_rate": 0.05, "article_count": 10, "heat": "hot"},
            ],
            "hot_topics": [...],  # 平均阅读 > 整体平均 的话题
            "cold_topics": [...],  # 平均阅读 < 整体平均 的话题
        }
    """
    articles = load_articles(account_id, days)
    if not articles:
        return {"topics": [], "hot_topics": [], "cold_topics": []}

    # 按 topic_tags 分组
    topic_groups: dict[str, list] = defaultdict(list)
    for a in articles:
        tags = a.topic_tags if a.topic_tags else ["未分类"]
        for tag in tags:
            topic_groups[tag].append(a)

    # 如果没有 tag，用标题关键词简单分类
    if len(topic_groups) <= 1:
        keyword_topics = {
            "AI": ["AI", "人工智能", "Agent"],
            "技术": ["代码", "编程", "开发"],
            "运营": ["运营", "增长", "流量"],
        }
        for a in articles:
            assigned = False
            for topic, keywords in keyword_topics.items():
                if any(kw in a.title for kw in keywords):
                    topic_groups[topic].append(a)
                    assigned = True
                    break
            if not assigned:
                topic_groups["其他"].append(a)

    overall_avg_reads = sum(a.read_count for a in articles) / len(articles)

    topics = []
    for topic, arts in topic_groups.items():
        avg_reads = sum(a.read_count for a in arts) / len(arts)
        avg_interaction = sum(a.interaction_rate for a in arts) / len(arts)
        heat = "hot" if avg_reads > overall_avg_reads else "cold"
        topics.append({
            "topic": topic,
            "avg_reads": round(avg_reads, 1),
            "avg_interaction_rate": round(avg_interaction, 4),
            "article_count": len(arts),
            "heat": heat,
        })

    topics.sort(key=lambda x: x["avg_reads"], reverse=True)
    return {
        "topics": topics,
        "hot_topics": [t for t in topics if t["heat"] == "hot"],
        "cold_topics": [t for t in topics if t["heat"] == "cold"],
    }
