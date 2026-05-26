"""分析数据 Pydantic 模型。"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class ArticleMetrics(BaseModel):
    """单篇文章的指标数据。"""

    article_id: str
    title: str
    url: str = ""
    published_at: datetime
    read_count: int = 0  # 阅读量
    like_count: int = 0  # 点赞数
    comment_count: int = 0  # 评论数
    share_count: int = 0  # 转发数（如果有）
    is_original: bool = False
    topic_tags: list[str] = Field(default_factory=list)

    @property
    def interaction_rate(self) -> float:
        """互动率 = (点赞 + 评论) / 阅读"""
        if self.read_count == 0:
            return 0.0
        return (self.like_count + self.comment_count) / self.read_count

    @property
    def share_rate(self) -> float:
        """分享率 = 转发 / 阅读"""
        if self.read_count == 0:
            return 0.0
        return self.share_count / self.read_count


class AccountProfile(BaseModel):
    """公众号账号画像。"""

    account_id: str
    account_name: str
    total_articles: int = 0
    avg_reads: float = 0.0
    avg_likes: float = 0.0
    avg_interaction_rate: float = 0.0
    best_publish_hour: int = 12
    best_framework: str = "checklist"
    data_range_days: int = 30
