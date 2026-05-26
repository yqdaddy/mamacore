"""数据采集 —— wechat-article-exporter API 封装 + 手动导入支持。"""
import os
import csv
import json
import sqlite3
import httpx
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .models import ArticleMetrics, AccountProfile

# 默认 wechat-article-exporter 实例地址
DEFAULT_EXPORTER_URL = os.environ.get("MAMA_EXPORTER_URL", "http://localhost:3000")

DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
DB_PATH = DATA_DIR / "mamacore_analytics.db"

# ── Schema 版本化 ─────────────────────────────────────────────

CURRENT_SCHEMA_VERSION = 1

_ARTICLES_SCHEMA = """
CREATE TABLE IF NOT EXISTS articles (
    article_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT DEFAULT '',
    published_at TEXT NOT NULL,
    read_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    share_count INTEGER DEFAULT 0,
    is_original INTEGER DEFAULT 0,
    topic_tags TEXT DEFAULT '[]',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
"""

_SCHEMA_VERSION_TABLE = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT DEFAULT CURRENT_TIMESTAMP
)
"""


def _migrate_db(conn: sqlite3.Connection, version: int) -> None:
    """数据库迁移。按版本顺序执行。

    Args:
        conn: 数据库连接
        version: 当前数据库版本号
    """
    # version 0 → 1: 初始 schema
    if version < 1:
        conn.execute(_ARTICLES_SCHEMA)
        conn.execute(_SCHEMA_VERSION_TABLE)
        conn.execute("INSERT INTO schema_version (version) VALUES (1)")
        conn.commit()


def _get_db() -> sqlite3.Connection:
    """获取 SQLite 连接，自动执行 schema 迁移。"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    # 检查当前 schema 版本
    try:
        row = conn.execute(
            "SELECT version FROM schema_version ORDER BY version DESC LIMIT 1"
        ).fetchone()
        current_version = row["version"] if row else 0
    except sqlite3.OperationalError:
        # schema_version 表不存在，说明是首次使用
        current_version = 0

    if current_version < CURRENT_SCHEMA_VERSION:
        _migrate_db(conn, current_version)

    return conn

# ── 业务逻辑 ──────────────────────────────────────────────────


async def fetch_account_articles(
    account_id: str, days: int = 30, exporter_url: str = ""
) -> list[ArticleMetrics]:
    """从 wechat-article-exporter API 获取公众号文章数据。

    Args:
        account_id: 公众号 ID 或名称
        days: 时间范围（天）
        exporter_url: 实例地址（默认 MAMA_EXPORTER_URL 环境变量）
    """
    url = exporter_url or DEFAULT_EXPORTER_URL
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            # wechat-article-exporter 的文章列表 API
            resp = await client.get(
                f"{url}/api/articles",
                params={"account_id": account_id, "days": days},
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        raise ConnectionError(f"无法连接 wechat-article-exporter ({url}): {e}")

    articles = []
    for item in data.get("articles", []):
        articles.append(
            ArticleMetrics(
                article_id=item.get("id", ""),
                title=item.get("title", ""),
                url=item.get("url", ""),
                published_at=datetime.fromisoformat(item["published_at"])
                if item.get("published_at")
                else datetime.now(),
                read_count=item.get("read_count", 0) or 0,
                like_count=item.get("like_count", 0) or 0,
                comment_count=item.get("comment_count", 0) or 0,
                share_count=item.get("share_count", 0) or 0,
                is_original=item.get("is_original", False),
                topic_tags=item.get("topic_tags", []) or [],
            )
        )

    # 存入本地数据库
    save_articles(account_id, articles)
    return articles


def save_articles(account_id: str, articles: list[ArticleMetrics]) -> None:
    """保存文章数据到 SQLite。"""
    conn = _get_db()
    for a in articles:
        conn.execute(
            "INSERT OR REPLACE INTO articles "
            "(article_id, account_id, title, url, published_at, "
            "read_count, like_count, comment_count, share_count, is_original, topic_tags) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                a.article_id,
                account_id,
                a.title,
                a.url,
                a.published_at.isoformat(),
                a.read_count,
                a.like_count,
                a.comment_count,
                a.share_count,
                int(a.is_original),
                json.dumps(a.topic_tags),
            ),
        )
    conn.commit()
    conn.close()


def load_articles(account_id: str, days: int = 30) -> list[ArticleMetrics]:
    """从本地 SQLite 加载文章数据。"""
    conn = _get_db()
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    rows = conn.execute(
        "SELECT * FROM articles WHERE account_id = ? AND published_at >= ?",
        (account_id, cutoff),
    ).fetchall()
    conn.close()

    articles = []
    for row in rows:
        articles.append(
            ArticleMetrics(
                article_id=row["article_id"],
                title=row["title"],
                url=row["url"],
                published_at=datetime.fromisoformat(row["published_at"]),
                read_count=row["read_count"],
                like_count=row["like_count"],
                comment_count=row["comment_count"],
                share_count=row["share_count"],
                is_original=bool(row["is_original"]),
                topic_tags=json.loads(row["topic_tags"])
                if row["topic_tags"]
                else [],
            )
        )
    return articles


def import_csv(csv_path: str, account_id: str) -> int:
    """从 CSV 导入文章数据。

    CSV 格式: article_id,title,url,published_at,read_count,like_count,comment_count,share_count,is_original
    """
    articles = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            articles.append(
                ArticleMetrics(
                    article_id=row.get("article_id", ""),
                    title=row.get("title", ""),
                    url=row.get("url", ""),
                    published_at=datetime.fromisoformat(row["published_at"]),
                    read_count=int(row.get("read_count", 0)),
                    like_count=int(row.get("like_count", 0)),
                    comment_count=int(row.get("comment_count", 0)),
                    share_count=int(row.get("share_count", 0)),
                    is_original=row.get("is_original", "false").lower() == "true",
                )
            )
    save_articles(account_id, articles)
    return len(articles)
