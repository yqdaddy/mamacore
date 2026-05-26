"""广告法极限词专项检测。"""
import re

from .sensitive_words import RISK_MEDIUM, check_ad_law


def check_ad_law_full(text: str) -> dict:
    """完整的广告法极限词检测。

    除了词库匹配外，还检测常见广告法违规模式。
    """
    result = check_ad_law(text)

    # 额外检测：绝对化表述模式
    absolute_patterns = [
        (r"最.*之一", "「最...之一」表述在广告法中存在争议，建议慎用"),
        (r".*全网.*最低.*", "「全网最低」属于价格违规表述，请确认合规性"),
        (r".*100%.*有效.*", "「100%有效」属于夸大宣传，违反广告法"),
    ]

    for pattern, warning in absolute_patterns:
        match = re.search(pattern, text)
        if match:
            result["issues"].append({
                "word": match.group(),
                "position": match.start(),
                "risk": RISK_MEDIUM,
                "suggestion": warning,
                "context": "",
            })
            result["passed"] = False
            result["total_issues"] += 1

    return result
