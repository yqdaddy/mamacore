"""集成测试 —— 端到端 Mock 流程。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mamacore.writer.framework import get_framework_prompt, get_framework_structure
from mamacore.writer.style import build_style_system_prompt
from mamacore.writer.title import score_title


class TestWriterPipeline:
    """写作流程集成测试。"""

    def test_framework_prompts_exist(self):
        """测试所有框架 prompt 存在。"""
        for framework in ["checklist", "pain", "compare", "narrative"]:
            prompt = get_framework_prompt(framework)
            assert prompt, f"框架 {framework} 的 prompt 为空"

    def test_framework_structure(self):
        """测试框架结构返回正确。"""
        for framework in ["checklist", "pain", "compare", "narrative"]:
            structure = get_framework_structure(framework)
            assert isinstance(structure, list)
            assert len(structure) > 0

    def test_unknown_framework(self):
        """测试未知框架抛出 ValueError。"""
        import pytest
        from mamacore.writer.framework import get_framework_prompt
        with pytest.raises(ValueError):
            get_framework_prompt("unknown_framework_xyz")

    def test_style_prompts(self):
        """测试所有风格 prompt 可构建。"""
        for style in ["satire", "tongue", "analytical", "experience", "science"]:
            prompt = build_style_system_prompt(style)
            assert prompt, f"风格 {style} 的 prompt 为空"

    def test_unknown_style(self):
        """测试未知风格抛出 ValueError。"""
        import pytest
        with pytest.raises(ValueError):
            build_style_system_prompt("unknown_style_xyz")


class TestTitleScoring:
    """标题评分集成测试。"""

    def test_high_score_title(self):
        """测试高分标题。"""
        result = score_title("关于 AI Agent，这 5 个坑你千万别踩")
        assert result["score"] >= 30

    def test_low_score_title(self):
        """测试低分标题。"""
        result = score_title("AI 简介")
        assert result["score"] <= 25

    def test_title_patterns(self):
        """测试标题模式提取。"""
        result = score_title("5 个真相！")
        assert isinstance(result["patterns"], list)


class TestEndToEnd:
    """端到端流程测试。"""

    def test_full_article_pipeline_mock(self):
        """测试完整文章流程（mock 数据）。"""
        # 1. 获取框架 prompt
        framework = "checklist"
        prompt = get_framework_prompt(framework)
        assert "清单型" in prompt

        # 2. 获取风格 prompt
        style = "satire"
        style_prompt = build_style_system_prompt(style)
        assert style_prompt

        # 3. 验证框架结构
        structure = get_framework_structure(framework)
        assert len(structure) > 0

    def test_safety_before_publish(self):
        """测试安全检测在发布前拦截。"""
        from mamacore.safety.sensitive_words import check_sensitive

        # 模拟一篇有问题的文章
        article = "这是最好的AI产品，完美无缺"
        result = check_sensitive(article)

        # 应该检测到问题
        assert result["total_issues"] > 0
        # 不应该通过检测
        assert result["passed"] is False

    def test_format_before_publish(self):
        """测试排版转换在发布前可用。"""
        from mamacore.adapter.wechat_format import markdown_to_wechat_html

        md = "# 标题\n\n这是内容\n\n:::callout\n提示\n:::end"
        html = markdown_to_wechat_html(md)
        assert html
        assert "<h1" in html
        assert "mama-callout" in html

    def test_analytics_models(self):
        """测试数据分析模型可用。"""
        from mamacore.analytics.models import ArticleMetrics, AccountProfile
        from datetime import datetime

        a = ArticleMetrics(
            article_id="1",
            title="测试",
            published_at=datetime.now(),
            read_count=1000,
        )
        assert a.interaction_rate == 0.0  # 没有点赞评论

    def test_hot_topics_models(self):
        """测试热点数据模型可用。"""
        from mamacore.hot_topics.models import HotTopic, HotTopicList

        t = HotTopic(title="测试", source="weibo")
        assert t.hot_score == 0

        lst = HotTopicList(topics=[t], source="weibo")
        assert len(lst.topics) == 1
