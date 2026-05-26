"""标题 A/B 效果分析 —— 从历史数据提取标题模式规律。"""
import re
from .scraper import load_articles


def analyze_title_patterns(account_id: str, days: int = 30) -> dict:
    """分析历史文章的标题模式效果。

    Returns:
        {
            "patterns": [
                {"pattern": "数字+痛点", "avg_reads": 5000, "count": 5},
            ],
            "best_performing": "数字+痛点+悬念",
            "recommendations": ["你的账号上数字类标题效果最好", "建议多使用痛点元素"],
        }
    """
    articles = load_articles(account_id, days)
    if not articles:
        return {"patterns": [], "best_performing": "", "recommendations": ["暂无数据，请先导入文章数据"]}

    # 简单标题模式提取
    pattern_groups: dict[str, list] = {}
    for a in articles:
        patterns = []
        if re.search(r'\d+', a.title):
            patterns.append("数字")
        if any(w in a.title for w in ['为什么', '怎么', '如何']):
            patterns.append("疑问")
        if any(w in a.title for w in ['最', '第一', '顶级']):
            patterns.append("极致")
        if any(w in a.title for w in ['别', '不要', '停止']):
            patterns.append("劝阻")
        if any(w in a.title for w in ['真相', '秘密', '意外']):
            patterns.append("悬念")
        if not patterns:
            patterns.append("常规")

        pattern_key = "+".join(patterns)
        if pattern_key not in pattern_groups:
            pattern_groups[pattern_key] = []
        pattern_groups[pattern_key].append(a)

    results = []
    for pattern, arts in pattern_groups.items():
        avg_reads = sum(a.read_count for a in arts) / len(arts)
        results.append({
            "pattern": pattern,
            "avg_reads": round(avg_reads, 1),
            "count": len(arts),
        })

    results.sort(key=lambda x: x["avg_reads"], reverse=True)
    best = results[0]["pattern"] if results else ""

    return {
        "patterns": results,
        "best_performing": best,
        "recommendations": [
            f"你的账号上「{best}」类标题效果最好",
            f"共使用了 {len(pattern_groups)} 种标题模式",
        ],
    }
