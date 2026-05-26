"""定时发布 -- 基于推荐发文时间的调度器。"""
import asyncio
from datetime import datetime, timedelta
from typing import Optional

# 简化的调度器，生产环境应使用 APScheduler 或 Celery

_scheduled_tasks: dict[str, dict] = {}


def schedule_publish(
    task_id: str,
    title: str,
    content: str,
    publish_time: Optional[datetime] = None,
    cover_path: str = "",
) -> str:
    """预约发布任务。

    Args:
        task_id: 任务唯一 ID
        title: 文章标题
        content: 文章 HTML 内容
        publish_time: 发布时间（默认当前时间 + 1小时）
        cover_path: 封面图路径
    """
    if publish_time is None:
        publish_time = datetime.now() + timedelta(hours=1)

    delay = (publish_time - datetime.now()).total_seconds()
    if delay < 0:
        delay = 0

    _scheduled_tasks[task_id] = {
        "title": title,
        "content": content,
        "cover_path": cover_path,
        "publish_time": publish_time.isoformat(),
        "delay_seconds": delay,
        "status": "scheduled",
    }

    return task_id


def list_scheduled_tasks() -> list[dict]:
    """列出所有预约发布任务。"""
    return [
        {"task_id": tid, **info}
        for tid, info in _scheduled_tasks.items()
        if info["status"] == "scheduled"
    ]


def cancel_publish(task_id: str) -> bool:
    """取消预约发布。"""
    if task_id in _scheduled_tasks:
        _scheduled_tasks[task_id]["status"] = "cancelled"
        return True
    return False
