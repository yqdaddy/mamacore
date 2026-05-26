"""爆款模式识别 —— 从历史爆款提取特征公式。"""
from .scraper import load_articles


def analyze_viral_patterns(account_id: str, days: int = 30) -> dict:
    """从历史爆款文章中提取模式。

    Returns:
        {
            "optimal_length": 2000,  # 最佳字数
            "best_publish_hour": 21,  # 最佳发布时间
            "top_frameworks": ["checklist", "pain"],  # 最佳框架
            "title_patterns": ["数字+痛点"],  # 标题规律
            "emotional_tone": "讽刺调侃",  # 情绪基调
            "avg_reads_threshold": 5000,  # 爆款门槛
            "viral_articles": [...],  # 爆款文章列表
        }
    """
    articles = load_articles(account_id, days)
    if not articles:
        return {"recommendations": ["暂无数据"]}

    # 定义爆款门槛（平均阅读的 1.5 倍）
    avg_reads = sum(a.read_count for a in articles) / len(articles)
    threshold = avg_reads * 1.5
    viral = [a for a in articles if a.read_count >= threshold]

    if not viral:
        return {"recommendations": ["暂无明显爆款，建议增加内容质量"]}

    # 最佳发布时间
    hour_counts: dict[int, int] = {}
    for a in viral:
        h = a.published_at.hour
        hour_counts[h] = hour_counts.get(h, 0) + 1
    best_hour = max(hour_counts, key=hour_counts.get) if hour_counts else 21

    return {
        "optimal_length": 2000,  # TODO: 从文章内容计算
        "best_publish_hour": best_hour,
        "viral_count": len(viral),
        "avg_reads": round(avg_reads, 1),
        "viral_threshold": round(threshold, 1),
        "viral_articles": [
            {"title": a.title, "reads": a.read_count, "published": a.published_at.strftime("%Y-%m-%d")}
            for a in sorted(viral, key=lambda x: x.read_count, reverse=True)[:5]
        ],
        "recommendations": [
            f"爆款门槛: 阅读量 >= {threshold:.0f}",
            f"最佳发文时间: {best_hour}:00",
            f"爆款文章数: {len(viral)}/{len(articles)}",
        ],
    }
