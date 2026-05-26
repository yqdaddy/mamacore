"""变现分析 —— 阅读量 -> 收益映射（估算）。"""
from .scraper import load_articles


def analyze_monetization(account_id: str, days: int = 30) -> dict:
    """分析变现能力。

    微信公众号变现方式:
    - 流量主（广告分成）: 约 0.5-2 元/千阅读
    - 赞赏: 约 0.1-1 元/赞赏
    - 付费阅读: 约 1-50 元/篇
    - 广告接单: 约 500-10000 元/篇（取决于粉丝量）
    """
    articles = load_articles(account_id, days)
    if not articles:
        return {"recommendations": ["暂无数据"]}

    total_reads = sum(a.read_count for a in articles)
    avg_reads = total_reads / len(articles)

    # 估算流量主收益 (1 元/千阅读)
    estimated_ad_revenue = total_reads / 1000 * 1.0

    # 广告价值评估
    if avg_reads > 5000:
        ad_value = "高 (单篇广告报价 2000-5000 元)"
    elif avg_reads > 1000:
        ad_value = "中 (单篇广告报价 500-2000 元)"
    elif avg_reads > 500:
        ad_value = "低 (单篇广告报价 100-500 元)"
    else:
        ad_value = "初期 (建议先提升内容质量和粉丝量)"

    return {
        "total_reads": total_reads,
        "avg_reads": round(avg_reads, 1),
        "estimated_ad_revenue": round(estimated_ad_revenue, 2),
        "ad_value": ad_value,
        "articles_count": len(articles),
        "days": days,
        "daily_avg_reads": round(total_reads / days, 1),
        "recommendations": [
            f"估算流量主收入: ¥{estimated_ad_revenue:.0f} ({days}天)",
            f"广告价值: {ad_value}",
            f"日均阅读: {total_reads / days:.0f}",
        ],
    }
