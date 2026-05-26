"""数据分析模型测试。"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mamacore.analytics.models import ArticleMetrics, AccountProfile


class TestArticleMetrics:
    """文章指标模型测试。"""

    def test_interaction_rate(self):
        """测试互动率计算。"""
        a = ArticleMetrics(
            article_id="1",
            title="测试",
            published_at=datetime.now(),
            read_count=1000,
            like_count=50,
            comment_count=30,
        )
        assert a.interaction_rate == 0.08  # (50+30)/1000

    def test_interaction_rate_zero_reads(self):
        """测试零阅读时互动率为 0。"""
        a = ArticleMetrics(
            article_id="1",
            title="测试",
            published_at=datetime.now(),
            read_count=0,
            like_count=10,
            comment_count=5,
        )
        assert a.interaction_rate == 0.0

    def test_share_rate(self):
        """测试分享率计算。"""
        a = ArticleMetrics(
            article_id="1",
            title="测试",
            published_at=datetime.now(),
            read_count=1000,
            share_count=20,
        )
        assert a.share_rate == 0.02

    def test_default_values(self):
        """测试默认值。"""
        a = ArticleMetrics(
            article_id="1",
            title="测试",
            published_at=datetime.now(),
        )
        assert a.read_count == 0
        assert a.like_count == 0
        assert a.comment_count == 0
        assert a.share_count == 0
        assert a.is_original is False
        assert a.topic_tags == []

    def test_topic_tags(self):
        """测试话题标签。"""
        a = ArticleMetrics(
            article_id="1",
            title="测试",
            published_at=datetime.now(),
            topic_tags=["AI", "技术"],
        )
        assert "AI" in a.topic_tags


class TestAccountProfile:
    """账号画像模型测试。"""

    def test_default_values(self):
        """测试默认值。"""
        p = AccountProfile(account_id="test", account_name="Test")
        assert p.total_articles == 0
        assert p.avg_reads == 0.0
        assert p.best_publish_hour == 12

    def test_all_fields(self):
        """测试所有字段。"""
        p = AccountProfile(
            account_id="test",
            account_name="Test",
            total_articles=100,
            avg_reads=5000.0,
            avg_likes=200.0,
            avg_interaction_rate=0.05,
            best_publish_hour=21,
            data_range_days=30,
        )
        assert p.total_articles == 100
        assert p.avg_reads == 5000.0
        assert p.best_publish_hour == 21
