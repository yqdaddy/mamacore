"""Pydantic data models for the writing framework engine."""

from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from typing import Optional


class FrameworkType(str, Enum):
    CHECKLIST = "checklist"
    PAIN = "pain"
    COMPARE = "compare"
    NARRATIVE = "narrative"


class WritingStyle(str, Enum):
    SATIRE = "satire"
    TONGUE = "tongue"
    ANALYTICAL = "analytical"
    EXPERIENCE = "experience"
    SCIENCE = "science"


class ArticleSection(BaseModel):
    """A single section within an article."""
    title: str
    content: str
    order: int = 0


class Article(BaseModel):
    """Complete article data."""
    topic: str
    framework: FrameworkType
    style: WritingStyle
    outline: list[dict]  # [{"section": "xxx", "key_points": ["xxx"]}]
    draft: str           # Initial draft Markdown
    enhanced: str = ""   # Enhanced content
    title_candidates: list[dict] = []  # [{"text": "...", "score": 85}]
    selected_title: str = ""
    images: list[dict] = []  # [{"url": "...", "caption": "...", "position": "cover|inline"}]
    formatted_html: str = ""  # WeChat formatted HTML
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: dict = Field(default_factory=dict)
