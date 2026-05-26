"""热点数据模型测试。"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mamacore.hot_topics.models import HotTopic, HotTopicList


class TestHotTopic:
    """热点数据测试。"""

    def test_create_hot_topic(self):
        """测试创建热点数据。"""
        topic = HotTopic(
            title="测试热点",
            source="weibo",
            hot_score=100,
        )
        assert topic.title == "测试热点"
        assert topic.source == "weibo"
        assert topic.hot_score == 100

    def test_default_values(self):
        """测试默认值。"""
        topic = HotTopic(
            title="测试",
            source="weibo",
        )
        assert topic.description == ""
        assert topic.url == ""
        assert topic.hot_score == 0
        assert topic.published_at is None
        assert topic.related is False
        assert topic.related_score == 0.0


class TestHotTopicList:
    """热点列表测试。"""

    def test_create_list(self):
        """测试创建热点列表。"""
        topics = [
            HotTopic(title="热点1", source="weibo", hot_score=100),
            HotTopic(title="热点2", source="weibo", hot_score=50),
        ]
        lst = HotTopicList(topics=topics, source="weibo")
        assert len(lst.topics) == 2

    def test_filter_by_score(self):
        """测试按热度过滤。"""
        topics = [
            HotTopic(title="高热度", source="weibo", hot_score=200),
            HotTopic(title="低热度", source="weibo", hot_score=10),
        ]
        lst = HotTopicList(topics=topics, source="weibo")
        filtered = lst.filter_by_score(min_score=50)
        assert filtered.total >= 1
        assert filtered.topics[0].title == "高热度"

    def test_filter_by_keyword(self):
        """测试按关键词过滤。"""
        topics = [
            HotTopic(title="AI Agent 开发", source="weibo"),
            HotTopic(title="旅游度假", source="weibo"),
            HotTopic(title="AI 技术突破", source="zhihu"),
        ]
        lst = HotTopicList(topics=topics, source="all")
        filtered = lst.filter_by_keyword("AI")
        assert filtered.total == 2

    def test_filter_empty_keyword(self):
        """测试空关键词过滤返回所有。"""
        topics = [
            HotTopic(title="测试", source="weibo"),
        ]
        lst = HotTopicList(topics=topics, source="weibo")
        filtered = lst.filter_by_keyword("")
        # 空关键词应该返回所有
        assert filtered.total >= 1

    def test_fetched_at_auto(self):
        """测试自动设置抓取时间。"""
        lst = HotTopicList(topics=[], source="weibo")
        assert isinstance(lst.fetched_at, datetime)
