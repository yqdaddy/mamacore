"""热点数据 Pydantic 模型。"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class HotTopic(BaseModel):
    """单条热点数据。"""
    title: str = Field(description="标题")
    description: str = Field(default="", description="摘要/描述")
    url: str = Field(default="", description="链接")
    source: str = Field(description="来源平台，如 weibo/zhihu/toutiao")
    hot_score: int = Field(default=0, description="热度值")
    published_at: Optional[datetime] = Field(default=None, description="发布时间")
    related: bool = Field(default=False, description="是否与用户账号主题相关")
    related_score: float = Field(default=0.0, ge=0, le=1, description="相关度评分 0-1")


class HotTopicList(BaseModel):
    """热点列表。"""
    topics: list[HotTopic] = Field(default_factory=list)
    source: str = Field(description="数据来源")
    fetched_at: datetime = Field(default_factory=datetime.now, description="抓取时间")
    total: int = Field(default=0, description="总数")

    def filter_by_score(self, min_score: int = 0) -> "HotTopicList":
        """按热度值过滤。"""
        return HotTopicList(
            topics=[t for t in self.topics if t.hot_score >= min_score],
            source=self.source,
            fetched_at=self.fetched_at,
            total=sum(1 for t in self.topics if t.hot_score >= min_score),
        )

    def filter_by_keyword(self, keyword: str) -> "HotTopicList":
        """按关键词过滤标题和描述。"""
        filtered = [
            t for t in self.topics
            if keyword.lower() in t.title.lower() or keyword.lower() in t.description.lower()
        ]
        return HotTopicList(
            topics=filtered,
            source=self.source,
            fetched_at=self.fetched_at,
            total=len(filtered),
        )
