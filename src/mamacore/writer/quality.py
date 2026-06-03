"""人性化评分引擎 —— 检测文章是否像 AI 生成的。

从 wewrite 迁移的三维评分系统：
- Tier 1 (统计特征，50%): 句长方差、词汇丰富度、突发性等
- Tier 2 (模式特征，30%): 禁用词、破句、真实来源等
- Tier 3 (语义特征，20%): 由 LLM 评估的风格漂移、密度波等
"""

import re
import math
from typing import Optional


# 禁用词列表（AI 常用过渡词）
BANNED_WORDS = [
    "首先", "其次", "再者", "最后", "总之", "综上所述", "总而言之",
    "此外", "另外", "与此同时", "不仅如此", "更重要的是", "在此基础上",
    "作为一个", "让我们", "值得注意的是", "需要指出的是", "不可否认",
    "毋庸置疑", "众所周知", "事实上", "显而易见", "可以说", "从某种意义上说",
    "非常重要", "至关重要", "不言而喻", "具有重要意义", "发挥着重要作用",
    "意义深远", "影响深远", "引发了广泛关注", "引起了热烈讨论",
    "总的来说", "综合来看", "由此可见", "不难发现", "通过以上分析",
    "正如我们所看到的",
]

# 真实来源模式（人类写作常引用具体来源）
REAL_SOURCE_PATTERNS = [
    r'[A-Z][a-z]+\s+[A-Z][a-z]+',
    r'[一-鿿]{2,4}(?:表示|指出|认为|写道|提到|说过)',
]


def check_sentence_variance(text: str) -> float:
    """检查句长方差。人类写作句长变化剧烈，AI 趋于均匀。"""
    sentences = [s.strip() for s in re.split(r'[。！？；]', text) if s.strip()]
    if len(sentences) < 5:
        return 0.5  # 样本不足，返回中等

    lengths = [len(s) for s in sentences]
    mean_len = sum(lengths) / len(lengths)
    variance = sum((l - mean_len) ** 2 for l in lengths) / len(lengths)
    std_dev = math.sqrt(variance)

    # 标准差 ≥ 15 为优秀，≤ 5 为 AI 特征
    score = min(1.0, std_dev / 25)
    return round(score, 3)


def check_banned_words(text: str) -> float:
    """检查禁用词密度。AI 倾向使用固定过渡词。"""
    found = [w for w in BANNED_WORDS if w in text]
    density = len(found) / max(1, len(text) / 100)  # 每 100 字
    # 密度 ≤ 0.5 为优秀，≥ 3 为 AI 特征
    score = max(0.0, 1.0 - density / 3)
    return round(score, 3)


def check_broken_sentences(text: str) -> float:
    """检查破句风格。人类会用短句制造节奏。"""
    sentences = [s.strip() for s in re.split(r'[。！？；\n]', text) if s.strip()]
    short_count = sum(1 for s in sentences if len(s) <= 5)
    ratio = short_count / max(1, len(sentences))
    # 破句比例 0.1-0.3 为自然
    score = 1.0 if 0.05 <= ratio <= 0.4 else max(0.2, 1.0 - abs(ratio - 0.2) * 2)
    return round(score, 3)


def check_real_sources(text: str) -> float:
    """检查真实来源引用。人类常引用具体人名/机构。"""
    found = sum(1 for p in REAL_SOURCE_PATTERNS if re.search(p, text))
    # 找到 ≥ 2 个真实来源模式为优秀
    score = min(1.0, found / 3)
    return round(score, 3)


def check_paragraph_variance(text: str) -> float:
    """检查段落长度变化。AI 段落趋于均匀。"""
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    if len(paragraphs) < 3:
        return 0.5

    lengths = [len(p) for p in paragraphs]
    mean_len = sum(lengths) / len(lengths)
    variance = sum((l - mean_len) ** 2 for l in lengths) / len(lengths)
    std_dev = math.sqrt(variance)

    # 标准差 ≥ 40 为优秀
    score = min(1.0, std_dev / 80)
    return round(score, 3)


def check_negative_emotion(text: str) -> float:
    """检查负面情绪表达。AI 中文过于中性。"""
    negative_words = ['扯', '失望', '焦虑', '坑', '骗', '扯淡', '不靠谱', '瞎', '糊弄']
    found = sum(1 for w in negative_words if w in text)
    # 负面情绪 ≥ 2 处为自然
    score = min(1.0, found / 3)
    return round(score, 3)


def check_vocabulary_richness(text: str) -> float:
    """检查词汇丰富度。AI 词汇趋于窄。"""
    words = re.findall(r'[一-鿿]+', text)
    if not words:
        return 0.5
    unique_ratio = len(set(words)) / len(words)
    # 独特词汇比例 ≥ 0.7 为优秀
    score = min(1.0, unique_ratio / 0.8)
    return round(score, 3)


def score_humanness(text: str, tier3_score: Optional[float] = None) -> dict:
    """计算人性化评分。

    Args:
        text: 文章文本
        tier3_score: Tier 3 语义评分（可选，0-1）

    Returns:
        {
            "score": 0.85,  # 综合评分 0-1
            "tier1": 0.82,  # 统计特征
            "tier2": 0.75,  # 模式特征
            "tier3": 0.90,  # 语义特征（如提供）
            "details": {
                "sentence_variance": 0.85,
                "banned_words": 0.70,
                ...
            },
            "verdict": "pass" | "warning" | "fail"
        }
    """
    details = {
        "sentence_variance": check_sentence_variance(text),
        "banned_words": check_banned_words(text),
        "broken_sentences": check_broken_sentences(text),
        "real_sources": check_real_sources(text),
        "paragraph_variance": check_paragraph_variance(text),
        "negative_emotion": check_negative_emotion(text),
        "vocabulary_richness": check_vocabulary_richness(text),
    }

    # Tier 1: 统计特征 (句长方差 + 段落方差 + 词汇丰富度)
    tier1 = round(
        (details["sentence_variance"] * 0.4 +
         details["paragraph_variance"] * 0.3 +
         details["vocabulary_richness"] * 0.3),
        3,
    )

    # Tier 2: 模式特征 (禁用词 + 破句 + 真实来源 + 负面情绪)
    tier2 = round(
        (details["banned_words"] * 0.3 +
         details["broken_sentences"] * 0.2 +
         details["real_sources"] * 0.3 +
         details["negative_emotion"] * 0.2),
        3,
    )

    # Tier 3: 语义特征（由 LLM 评估）
    tier3 = tier3_score if tier3_score is not None else (tier1 + tier2) / 2

    # 综合评分
    if tier3_score is not None:
        score = round(tier1 * 0.5 + tier2 * 0.3 + tier3 * 0.2, 3)
    else:
        # 无 Tier 3 时重新分配权重
        score = round(tier1 * 0.625 + tier2 * 0.375, 3)

    # 判定
    if score >= 0.7:
        verdict = "pass"
    elif score >= 0.4:
        verdict = "warning"
    else:
        verdict = "fail"

    return {
        "score": score,
        "tier1": tier1,
        "tier2": tier2,
        "tier3": round(tier3, 3),
        "details": details,
        "verdict": verdict,
    }
