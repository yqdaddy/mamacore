"""任务管理 —— 注册/查看/连接/终止运行中的 Agent 任务。"""

import json
import os
import signal
import subprocess
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional


DATA_DIR = Path(__file__).parent.parent.parent.parent / "data" / "tasks"
TASKS_FILE = DATA_DIR / "tasks.json"


@dataclass
class Task:
    """运行中的任务。"""
    id: str
    provider: str
    task_desc: str
    status: str  # running / completed / failed / killed
    pid: Optional[int] = None
    log_file: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    work_dir: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


class TaskManager:
    """任务管理器。"""

    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def _load_tasks(self) -> list[dict]:
        if TASKS_FILE.exists():
            with open(TASKS_FILE) as f:
                return json.load(f)
        return []

    def _save_tasks(self, tasks: list[dict]) -> None:
        with open(TASKS_FILE, "w") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)

    def create(
        self,
        provider: str,
        task_desc: str,
        pid: Optional[int] = None,
        log_file: Optional[str] = None,
        work_dir: Optional[str] = None,
    ) -> Task:
        """注册新任务。"""
        task = Task(
            id=str(uuid.uuid4())[:8],
            provider=provider,
            task_desc=task_desc,
            status="running",
            pid=pid,
            log_file=log_file,
            started_at=datetime.now().isoformat(),
            work_dir=work_dir,
        )
        tasks = self._load_tasks()
        tasks.append(task.to_dict())
        self._save_tasks(tasks)
        return task

    def list_tasks(self, status: str = "all") -> list[dict]:
        """列出任务。"""
        tasks = self._load_tasks()
        if status != "all":
            tasks = [t for t in tasks if t["status"] == status]
        return tasks

    def get_task(self, task_id: str) -> Optional[dict]:
        """获取单个任务。"""
        tasks = self._load_tasks()
        for t in tasks:
            if t["id"] == task_id:
                return t
        return None

    def update_status(self, task_id: str, status: str) -> bool:
        """更新任务状态。"""
        tasks = self._load_tasks()
        for t in tasks:
            if t["id"] == task_id:
                t["status"] = status
                t["completed_at"] = datetime.now().isoformat()
                self._save_tasks(tasks)
                return True
        return False

    def kill(self, task_id: str) -> bool:
        """终止运行中的任务。"""
        task = self.get_task(task_id)
        if not task or task["status"] != "running":
            return False

        pid = task.get("pid")
        if pid:
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass

        self.update_status(task_id, "killed")
        return True

    def cleanup(self, task_id: str) -> bool:
        """清理已完成的任务。"""
        tasks = self._load_tasks()
        tasks = [t for t in tasks if t["id"] != task_id]
        self._save_tasks(tasks)
        return True
