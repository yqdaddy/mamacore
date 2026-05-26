"""编排器测试。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mamacore.orchestrator.providers import (
    get_provider, list_providers, PROVIDERS,
    ClaudeCodeProvider, OpenClawProvider, CodexProvider,
)
from mamacore.orchestrator.task_manager import TaskManager, Task
from mamacore.orchestrator.runner import (
    get_project_root, get_workflow_prompt, get_mcp_config,
)


class TestProviders:
    """Provider 测试。"""

    def test_list_providers(self):
        """测试列出所有 Provider。"""
        providers = list_providers()
        assert len(providers) == 3
        names = [p["name"] for p in providers]
        assert "claude" in names
        assert "codex" in names
        assert "openclaw" in names

    def test_get_provider_claude(self):
        """测试获取 Claude Provider。"""
        provider = get_provider("claude")
        assert isinstance(provider, ClaudeCodeProvider)
        assert provider.name == "claude"

    def test_get_provider_openclaw(self):
        """测试获取 OpenClaw Provider。"""
        provider = get_provider("openclaw")
        assert isinstance(provider, OpenClawProvider)
        assert provider.name == "openclaw"

    def test_get_provider_invalid(self):
        """测试获取不存在的 Provider 抛出异常。"""
        import pytest
        with pytest.raises(ValueError):
            get_provider("nonexistent")

    def test_claude_build_command(self):
        """测试 Claude 命令构建。"""
        provider = get_provider("claude")
        cmd = provider.build_command(
            "写一篇关于AI的文章",
            {"mcpServers": {}},
            "/tmp",
            {"model": "opus-4.7"},
        )
        assert cmd[0] == "claude"
        assert "--dangerously-skip-permissions" in cmd
        assert "--mcp-config" in cmd
        assert "-p" in cmd
        assert "--model" in cmd
        assert "opus-4.7" in cmd

    def test_openclaw_build_command(self):
        """测试 OpenClaw 命令构建。"""
        provider = get_provider("openclaw")
        cmd = provider.build_command(
            "写一篇关于AI的文章",
            {"mcpServers": {}},
            "/tmp",
            {},
        )
        assert cmd[0] == "openclaw"
        assert "agent" in cmd
        assert "--local" in cmd
        assert "--message" in cmd
        assert "写一篇关于AI的文章" in cmd

    def test_openclaw_build_command_with_model(self):
        """测试 OpenClaw 带模型的命令构建。"""
        provider = get_provider("openclaw")
        cmd = provider.build_command(
            "测试",
            {"mcpServers": {}},
            "/tmp",
            {"model": "sonnet-4-6"},
        )
        assert "--model" in cmd
        assert "sonnet-4-6" in cmd


class TestTaskManager:
    """TaskManager 测试。"""

    def test_create_task(self):
        """测试创建任务。"""
        tm = TaskManager()
        task = tm.create("claude", "测试任务")
        assert task.id is not None
        assert task.status == "running"
        assert task.provider == "claude"
        tm.cleanup(task.id)

    def test_list_tasks(self):
        """测试列出任务。"""
        tm = TaskManager()
        task1 = tm.create("claude", "任务1")
        task2 = tm.create("openclaw", "任务2")
        tasks = tm.list_tasks()
        assert len(tasks) >= 2
        tm.cleanup(task1.id)
        tm.cleanup(task2.id)

    def test_update_status(self):
        """测试更新状态。"""
        tm = TaskManager()
        task = tm.create("claude", "测试")
        tm.update_status(task.id, "completed")
        updated = tm.get_task(task.id)
        assert updated["status"] == "completed"
        assert updated["completed_at"] is not None
        tm.cleanup(task.id)

    def test_kill_nonexistent(self):
        """测试终止不存在的任务返回 False。"""
        tm = TaskManager()
        assert tm.kill("nonexistent_task_id") is False


class TestRunner:
    """Runner 测试。"""

    def test_get_project_root(self):
        """测试获取项目根目录。"""
        root = get_project_root()
        assert Path(root).exists()
        assert Path(root, "pyproject.toml").exists()

    def test_get_workflow_prompt(self):
        """测试提示词生成。"""
        prompt = get_workflow_prompt("写一篇关于AI的文章")
        assert "用户任务: 写一篇关于AI的文章" in prompt

    def test_get_workflow_prompt_with_framework(self):
        """测试带框架的提示词。"""
        prompt = get_workflow_prompt("测试", framework="checklist")
        assert "强制使用框架: checklist" in prompt

    def test_get_workflow_prompt_with_style(self):
        """测试带风格的提示词。"""
        prompt = get_workflow_prompt("测试", style="satire")
        assert "强制使用风格: satire" in prompt

    def test_get_mcp_config(self):
        """测试 MCP 配置生成。"""
        root = get_project_root()
        config = get_mcp_config(root)
        assert "mcpServers" in config
        assert "mamacore" in config["mcpServers"]
        assert "command" in config["mcpServers"]["mamacore"]
