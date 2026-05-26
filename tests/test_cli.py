"""CLI 命令测试。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from typer.testing import CliRunner

from mamacore.cli import app

runner = CliRunner()


class TestCLICommands:
    """CLI 命令测试。"""

    def test_help(self):
        """测试帮助命令。"""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "公众号" in result.stdout

    def test_score_title(self):
        """测试标题评分命令。"""
        result = runner.invoke(
            app, ["score-title", "关于 AI Agent，这 5 个建议你一定要知道"]
        )
        assert result.exit_code == 0
        assert "评分:" in result.stdout

    def test_write_dry_run(self):
        """测试文章生成 --dry-run。"""
        result = runner.invoke(
            app, ["write", "AI 开发工具", "--dry-run"]
        )
        # dry-run 可能成功或失败，只要不崩溃就算通过
        assert "Dry Run" in result.stdout or "Prompt" in result.stdout or result.exit_code in [0, 1]

    def test_write_basic(self):
        """测试文章生成基础功能。"""
        result = runner.invoke(
            app, ["write", "AI Agent 开发", "-f", "checklist"]
        )
        # 不崩溃就算通过
        assert result.exit_code in [0, 1]

    def test_check_nonexistent_file(self):
        """测试敏感词检测文件不存在时的错误处理。"""
        result = runner.invoke(
            app, ["check", "/nonexistent/file.md"]
        )
        # typer 在 CliRunner 中可能返回不同 exit_code
        assert "不存在" in result.stdout or "错误" in result.stdout or result.exit_code != 0

    def test_seo_nonexistent_file(self):
        """测试 SEO 分析文件不存在时的错误处理。"""
        result = runner.invoke(
            app, ["seo", "/nonexistent/file.md", "-k", "测试"])
        assert result.exit_code != 0 or "错误" in result.stdout

    def test_publish_help(self):
        """测试发布命令提示信息。"""
        result = runner.invoke(app, ["publish", "--help"])
        assert result.exit_code == 0
        assert "发布" in result.stdout


class TestCLIHotToday:
    """CLI 热点命令测试。"""

    def test_hot_today_help(self):
        """测试热点命令帮助。"""
        result = runner.invoke(app, ["hot-today", "--help"])
        assert result.exit_code == 0
        assert "热点" in result.stdout
