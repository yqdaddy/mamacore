"""微信搜一搜 SEO 优化 —— 关键词密度分析和标题/摘要优化建议。

微信搜一搜排名影响因素:
1. 标题关键词匹配度
2. 正文关键词密度（2%-5%）
3. 首段出现关键词
4. 图片 alt 属性包含关键词
5. 账号权重和互动数据
"""

import re
from typing import Optional


def extract_keywords(text: str, top_n: int = 5) -> list[dict]:
    """从文本中提取关键词（基于词频的简单实现）。

    TODO: 后续接入 Jieba 分词做更精准的关键词提取。

    Args:
        text: 分析文本
        top_n: 返回前 N 个关键词

    Returns:
        [{"word": "xxx", "count": 5, "density": 0.03}]
    """
    # 简单中文词频：提取 2-4 字词组
    words: dict[str, int] = {}
    total_chars = len(text)

    for length in range(2, 5):
        for i in range(len(text) - length + 1):
            word = text[i:i + length]
            # 过滤纯标点
            if re.match(r'^[一-鿿]+$', word):
                words[word] = words.get(word, 0) + 1

    # 按频率排序
    sorted_words = sorted(words.items(), key=lambda x: x[1], reverse=True)

    result = []
    for word, count in sorted_words[:top_n]:
        density = count / max(1, total_chars) * length * 100
        result.append({
            "word": word,
            "count": count,
            "density": round(density, 4),
        })

    return result


def analyze_seo(article_md: str, target_keywords: list[str]) -> dict:
    """分析文章的 SEO 表现。

    Args:
        article_md: Markdown 格式文章
        target_keywords: 目标关键词列表

    Returns:
        {"score": 75, "issues": [...], "suggestions": [...], "keyword_density": {...}}
    """
    issues: list[str] = []
    suggestions: list[str] = []
    keyword_density: dict = {}

    # 提取标题
    title_match = re.match(r"# (.+)", article_md)
    title = title_match.group(1) if title_match else ""

    # 提取首段
    paragraphs = article_md.split("\n\n")
    first_paragraph = paragraphs[0] if paragraphs else ""

    for kw in target_keywords:
        kw_count = article_md.lower().count(kw.lower())
        total_words = len(article_md)
        density = kw_count / max(1, total_words) * len(kw) * 100

        keyword_density[kw] = {
            "count": kw_count,
            "density": round(density, 4),
        }

        # 检查标题是否包含关键词
        if kw not in title:
            suggestions.append(f"标题中未包含关键词「{kw}」，建议在标题中加入")

        # 检查首段是否包含关键词
        if kw not in first_paragraph:
            suggestions.append(f"首段未包含关键词「{kw}」，建议在前 2 句话中加入")

        # 检查关键词密度
        if density < 0.02:
            issues.append(f"关键词「{kw}」密度偏低 ({density:.2f}%)，建议增加到 2%-5%")
        elif density > 0.05:
            issues.append(f"关键词「{kw}」密度偏高 ({density:.2f}%)，可能被判定为堆砌")

    # SEO 评分计算
    score = 100
    score -= len(issues) * 10
    score -= len(suggestions) * 5
    score = max(0, min(100, score))

    return {
        "score": score,
        "title": title,
        "issues": issues,
        "suggestions": suggestions,
        "keyword_density": keyword_density,
        "checklist": {
            "title_length_ok": len(title) <= 64,
            "title_optimal": len(title) <= 26,  # 订阅列表不截断
            "has_keywords_in_title": any(kw in title for kw in target_keywords),
            "has_keywords_in_first_para": any(kw in first_paragraph for kw in target_keywords),
        },
    }


def optimize_title_for_seo(title: str, keywords: list[str]) -> str:
    """为 SEO 优化标题建议。

    规则:
    - 标题长度 <= 26 字（订阅列表不截断）
    - 至少包含 1 个目标关键词
    - 关键词靠前放置
    """
    if any(kw in title for kw in keywords):
        return title

    # 将第一个关键词插入标题开头
    if keywords and len(keywords[0]) + len(title) <= 26:
        return f"{keywords[0]}：{title}"

    return title
