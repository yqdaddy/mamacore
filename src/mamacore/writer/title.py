"""Title scoring engine — rule-based scoring for WeChat article titles."""

import re


def score_title(title: str) -> dict:
    """Score a title on multiple dimensions.

    Args:
        title: The title to score.

    Returns:
        Dict with score (0-100), patterns matched, breakdown, and suggestions.
    """
    breakdown = {
        "数字": 0,
        "悬念": 0,
        "痛点": 0,
        "情绪": 0,
    }
    patterns: list[str] = []

    # 数字：包含具体数字增加可信度和打开率
    numbers = re.findall(r'\d+', title)
    if numbers:
        breakdown["数字"] = min(25, len(numbers) * 10 + 5)
        patterns.append("数字")

    # 悬念：问号、省略号、悬念词汇
    if any(c in title for c in ('？', '?', '…', '……')):
        breakdown["悬念"] = 20
        patterns.append("悬念")
    if any(w in title for w in ('到底', '究竟', '真相', '秘密', '原来')):
        breakdown["悬念"] = min(25, breakdown["悬念"] + 10)
        patterns.append("悬念词")

    # 痛点：负面词汇、困境描述
    pain_words = ('坑', '错', '失败', '痛点', '焦虑', '困扰', '难', '别', '不要', '别再')
    if any(w in title for w in pain_words):
        breakdown["痛点"] = 20
        patterns.append("痛点")
    if any(w in title for w in ('为什么', '怎么', '如何')):
        breakdown["痛点"] = min(25, breakdown["痛点"] + 5)

    # 情绪：强烈情感词汇
    emotion_words = ('最', '绝', '爆', '炸', '震惊', '终于', '千万', '一定', '必须')
    if any(w in title for w in emotion_words):
        breakdown["情绪"] = 20
        patterns.append("情绪词")
    if any(w in title for w in ('我', '你', '他')):
        breakdown["情绪"] = min(25, breakdown["情绪"] + 5)
        patterns.append("人称")

    total = sum(breakdown.values())
    suggestions = []
    if breakdown["数字"] == 0:
        suggestions.append("考虑加入具体数字增强可信度")
    if breakdown["悬念"] < 15:
        suggestions.append("可以增加悬念元素提升打开率")
    if breakdown["痛点"] < 10:
        suggestions.append("加入痛点描述能增强共鸣")
    if breakdown["情绪"] < 15:
        suggestions.append("使用更强情绪词提升感染力")

    return {
        "score": total,
        "patterns": patterns,
        "breakdown": breakdown,
        "suggestions": suggestions,
    }
