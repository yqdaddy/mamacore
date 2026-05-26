"""Runner —— 核心编排器，启动 Agent 并连接 MCP Server 完成全流程。

工作流：
1. 读取 SKILL.md 工作流指令
2. 构建 MCP Server 配置（指向本地 server.py）
3. 启动指定的 Agent CLI（Claude Code / Codex / OpenClaw）
4. Agent 通过 MCP 调用 M.A.M.A. Core 工具完成全流程
5. 任务完成后更新状态
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

from .providers import get_provider, list_providers, BaseProvider
from .task_manager import TaskManager


def get_project_root() -> str:
    """获取项目根目录。"""
    return str(Path(__file__).parent.parent.parent.parent)


def get_workflow_prompt(task_desc: str, framework: str = "", style: str = "") -> str:
    """构建注入给 Agent 的系统提示词。"""
    prompt_file = Path(__file__).parent / "prompts" / "article_workflow.txt"
    if prompt_file.exists():
        workflow = prompt_file.read_text(encoding="utf-8")
    else:
        workflow = ""

    extra = ""
    if framework:
        extra += f"\n\n强制使用框架: {framework}"
    if style:
        extra += f"\n强制使用风格: {style}"

    return f"{workflow}\n\n用户任务: {task_desc}{extra}"


def get_mcp_config(project_root: str) -> dict:
    """构建 MCP Server 配置。"""
    return {
        "mcpServers": {
            "mamacore": {
                "command": sys.executable,
                "args": ["-m", "mamacore.server"],
                "env": {
                    "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", ""),
                    "DASHSCOPE_API_KEY": os.environ.get("DASHSCOPE_API_KEY", ""),
                    "MAMA_WECHAT_APP_ID": os.environ.get("MAMA_WECHAT_APP_ID", ""),
                    "MAMA_WECHAT_APP_SECRET": os.environ.get("MAMA_WECHAT_APP_SECRET", ""),
                    "MAMA_ACCOUNT_TYPE": os.environ.get("MAMA_ACCOUNT_TYPE", "personal"),
                },
            }
        }
    }


def run_task(
    task_desc: str,
    provider_name: str = "claude",
    framework: str = "",
    style: str = "",
    model: str = "",
    timeout: int = 1800,
    no_confirm: bool = False,
) -> dict:
    """执行一个完整的公众号文章任务。

    Args:
        task_desc: 任务描述
        provider_name: Agent Provider (claude/codex/openclaw)
        framework: 强制使用的框架
        style: 强制使用的风格
        model: 指定模型
        timeout: 超时时间（秒）
        no_confirm: 跳过确认

    Returns:
        任务信息字典
    """
    provider = get_provider(provider_name)

    if not provider.is_available():
        return {
            "error": f"Provider '{provider_name}' 未安装。请先安装 {provider.cli_name} CLI。",
            "status": "error",
        }

    project_root = get_project_root()
    prompt = get_workflow_prompt(task_desc, framework, style)
    mcp_config = get_mcp_config(project_root)

    # 创建任务日志目录
    tm = TaskManager()
    project_root = get_project_root()
    log_dir = Path(project_root) / "data" / "tasks"
    log_dir.mkdir(parents=True, exist_ok=True)
    safe_name = task_desc[:30].replace("/", "_").replace("\\", "_").replace(" ", "_")
    log_file = str(log_dir / f"{provider_name}_{safe_name}.log")

    cmd = provider.build_command(prompt, mcp_config, project_root, {
        "timeout": timeout,
        "model": model,
    })

    # 确认
    if not no_confirm:
        print(f"即将使用 {provider_name} 执行任务: {task_desc}")
        print(f"命令: {' '.join(cmd[:3])}...")
        confirm = input("确认执行? (y/N): ").strip().lower()
        if confirm not in ("y", "yes"):
            return {"status": "cancelled"}

    # 启动
    proc = subprocess.Popen(
        cmd,
        cwd=project_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    task = tm.create(
        provider=provider_name,
        task_desc=task_desc,
        pid=proc.pid,
        log_file=log_file,
        work_dir=project_root,
    )

    print(f"任务已启动 (ID: {task.id}, PID: {proc.pid})")
    print(f"日志: {log_file}")
    print(f"等待完成...")

    # 等待完成
    stdout, _ = proc.communicate(timeout=timeout)
    tm.update_status(task.id, "completed" if proc.returncode == 0 else "failed")

    return {
        "status": "completed" if proc.returncode == 0 else "failed",
        "task_id": task.id,
        "returncode": proc.returncode,
        "log_file": log_file,
    }


def list_available_providers() -> list[dict]:
    """列出所有可用的 Provider。"""
    return list_providers()
