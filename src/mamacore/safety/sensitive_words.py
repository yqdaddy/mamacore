"""敏感词检测引擎 —— 基于 pyahocorasick 的 Aho-Corasick 自动机。

支持:
- 多词库合并（广告法/政治/平台特定）
- 风险等级分类
- 位置报告 + 替换建议
"""
import os
import re
from pathlib import Path
from typing import Optional

import ahocorasick

WORDLIST_DIR = Path(__file__).parent / "wordlist"

# 风险等级定义
RISK_HIGH = "high"
RISK_MEDIUM = "medium"
RISK_LOW = "low"

# 词库对应的风险等级
WORDLIST_RISK = {
    "ad_law.txt": RISK_MEDIUM,        # 广告法极限词（中等风险）
    "political.txt": RISK_HIGH,       # 政治敏感词（高风险）
    "platform_specific.txt": RISK_LOW,  # 平台特定词（低风险）
}


class SensitiveWordDetector:
    """敏感词检测器 —— 单例模式。"""

    _instance: Optional["SensitiveWordDetector"] = None
    _automaton: Optional[ahocorasick.Automaton] = None
    _word_risk: dict[str, str] = {}

    def __new__(cls) -> "SensitiveWordDetector":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._automaton is not None:
            return
        self._build_automaton()

    def _build_automaton(self):
        """构建 Aho-Corasick 自动机。"""
        automaton = ahocorasick.Automaton()
        word_risk = {}

        for filename, risk_level in WORDLIST_RISK.items():
            wordlist_path = WORDLIST_DIR / filename
            if not wordlist_path.exists():
                continue

            with open(wordlist_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # 跳过注释和空行
                    if not line or line.startswith("#"):
                        continue
                    # 清理 Markdown 格式（如 **最好**、## 标题）
                    word = re.sub(r"[#*_`]", "", line).strip()
                    if word:
                        automaton.add_word(word, word)
                        word_risk[word] = risk_level

        automaton.make_automaton()
        self._automaton = automaton
        self._word_risk = word_risk

    def check(self, text: str, strict: bool = False) -> dict:
        """检测文本中的敏感词。

        Args:
            text: 待检测文本
            strict: 严格模式（包含低风险词）

        Returns:
            {
                "passed": bool,
                "total_issues": int,
                "high": int,
                "medium": int,
                "low": int,
                "issues": [
                    {"word": "最好", "position": 12, "risk": "medium",
                     "suggestion": "建议替换为更客观的表述"}
                ]
            }
        """
        if self._automaton is None:
            return {
                "passed": True,
                "total_issues": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "issues": [],
            }

        issues = []
        for end_index, word in self._automaton.iter(text):
            risk = self._word_risk.get(word, RISK_LOW)

            # 严格模式包含所有风险等级，否则只返回中高风险
            if not strict and risk == RISK_LOW:
                continue

            start_index = end_index - len(word) + 1
            suggestion = _get_suggestion(word, risk)
            issues.append({
                "word": word,
                "position": start_index,
                "risk": risk,
                "suggestion": suggestion,
                "context": _get_context(text, start_index, 20),
            })

        # 去重（同一词多次出现只保留一次）
        seen = set()
        unique_issues = []
        for issue in issues:
            key = issue["word"]
            if key not in seen:
                seen.add(key)
                unique_issues.append(issue)

        high_count = sum(1 for i in unique_issues if i["risk"] == RISK_HIGH)
        medium_count = sum(1 for i in unique_issues if i["risk"] == RISK_MEDIUM)
        low_count = sum(1 for i in unique_issues if i["risk"] == RISK_LOW)

        return {
            "passed": high_count == 0 and medium_count == 0,
            "total_issues": len(unique_issues),
            "high": high_count,
            "medium": medium_count,
            "low": low_count,
            "issues": unique_issues,
        }


def _get_suggestion(word: str, risk: str) -> str:
    """根据敏感词和风险等级生成替换建议。"""
    suggestions = {
        "最好": "建议替换为更客观的表述",
        "第一": "建议替换为具体描述",
        "唯一": "建议替换为更准确的表述",
        "国家级": "避免使用此类表述",
        "最高级": "避免使用此类表述",
        "顶级": "建议替换为具体描述",
        "极致": "建议使用更客观的形容词",
        "绝无仅有": "建议替换为更准确的表述",
        "史无前例": "建议替换为具体事实",
        "完美": "建议替换为更客观的评价",
        "完美无缺": "建议替换为更客观的评价",
        "首选": "建议使用更中性的推荐语",
        "领导品牌": "建议使用更客观的表述",
        "行业第一": "建议使用具体数据替代",
    }
    return suggestions.get(word, f"建议审查并考虑替换「{word}」")


def _get_context(text: str, position: int, radius: int = 20) -> str:
    """获取敏感词周围的上下文。"""
    start = max(0, position - radius)
    end = min(len(text), position + radius + 10)
    context = text[start:end]
    if start > 0:
        context = "..." + context
    if end < len(text):
        context += "..."
    return context


# 便捷函数
def check_sensitive(text: str, strict: bool = False) -> dict:
    """快速检测敏感词。"""
    detector = SensitiveWordDetector()
    return detector.check(text, strict)


def check_ad_law(text: str) -> dict:
    """仅检测广告法极限词。"""
    result = SensitiveWordDetector().check(text)
    ad_law_issues = [i for i in result["issues"] if i["risk"] == RISK_MEDIUM]
    return {
        "passed": len(ad_law_issues) == 0,
        "total_issues": len(ad_law_issues),
        "issues": ad_law_issues,
    }
