"""Provider 抽象层 —— 统一接口调度 Claude Code / Codex / OpenClaw。

每个 Provider 的核心职责：
1. 检查 CLI 是否安装 (is_available)
2. 构建启动命令 (build_command)
3. 启动 Agent 进程 (run)
4. 终止进程 (stop)
"""

import json
import os
import subprocess
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ProviderResult:
    """Agent 执行结果。"""
    returncode: int
    stdout: str
    stderr: str
    log_file: str


class BaseProvider(ABC):
    """Provider 抽象基类。"""

    name: str = "base"
    cli_name: str = ""

    @abstractmethod
    def is_available(self) -> bool:
        """检查 CLI 是否已安装。"""
        pass

    @abstractmethod
    def build_command(
        self,
        prompt: str,
        mcp_config: dict,
        work_dir: str,
        extra_args: dict,
    ) -> list[str]:
        """构建启动 Agent 的命令。"""
        pass

    def run(
        self,
        prompt: str,
        mcp_config: dict,
        work_dir: str,
        extra_args: Optional[dict] = None,
        log_file: Optional[str] = None,
    ) -> ProviderResult:
        """启动 Agent 进程并等待完成。"""
        extra_args = extra_args or {}
        cmd = self.build_command(prompt, mcp_config, work_dir, extra_args)

        if log_file:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            with open(log_file, "w", encoding="utf-8") as f:
                proc = subprocess.run(
                    cmd,
                    cwd=work_dir,
                    env={**os.environ, **extra_args.get("env", {})},
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    timeout=extra_args.get("timeout", 1800),
                )
                return ProviderResult(
                    returncode=proc.returncode,
                    stdout="",
                    stderr="",
                    log_file=log_file,
                )
        else:
            proc = subprocess.run(
                cmd,
                cwd=work_dir,
                env={**os.environ, **extra_args.get("env", {})},
                capture_output=True,
                text=True,
                timeout=extra_args.get("timeout", 1800),
            )
            return ProviderResult(
                returncode=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                log_file="",
            )


class ClaudeCodeProvider(BaseProvider):
    """Claude Code Provider。

    启动方式：
        claude --dangerously-skip-permissions -p "{prompt}"

    MCP 连接：通过 --mcp-config 参数传入 JSON 配置。
    """

    name = "claude"
    cli_name = "claude"

    def is_available(self) -> bool:
        try:
            subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                timeout=10,
            )
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def build_command(
        self,
        prompt: str,
        mcp_config: dict,
        work_dir: str,
        extra_args: dict,
    ) -> list[str]:
        # 将 MCP 配置写入临时文件
        mcp_file = os.path.join(work_dir, ".mcp.json")
        with open(mcp_file, "w") as f:
            json.dump(mcp_config, f)

        cmd = [
            "claude",
            "--dangerously-skip-permissions",
            "--allowedTools", "Bash,Read,Write,Edit,Glob,Grep,mama_*",
            "--output-format", "stream-json",
            "--mcp-config", mcp_file,
            "-p", prompt,
        ]

        if extra_args.get("model"):
            cmd.extend(["--model", extra_args["model"]])

        return cmd


class CodexProvider(BaseProvider):
    """OpenAI Codex CLI Provider。

    启动方式：
        codex exec -p "{prompt}" --approval-mode danger-full-speed

    MCP 连接：Codex 自动读取项目根目录的 .codex/mcp.json。
    """

    name = "codex"
    cli_name = "codex"

    def is_available(self) -> bool:
        try:
            subprocess.run(
                ["codex", "--version"],
                capture_output=True,
                timeout=10,
            )
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def build_command(
        self,
        prompt: str,
        mcp_config: dict,
        work_dir: str,
        extra_args: dict,
    ) -> list[str]:
        # Codex 读取 .codex/mcp.json
        codex_dir = os.path.join(work_dir, ".codex")
        os.makedirs(codex_dir, exist_ok=True)
        mcp_file = os.path.join(codex_dir, "mcp.json")
        with open(mcp_file, "w") as f:
            json.dump(mcp_config, f)

        cmd = [
            "codex",
            "exec",
            "-p", prompt,
            "--approval-mode", "danger-full-speed",
        ]

        return cmd


class OpenClawProvider(BaseProvider):
    """OpenClaw Provider。

    启动方式：
        openclaw --prompt "{prompt}" --no-interactive

    MCP 连接：OpenClaw 读取项目的 .mcp.json 或 ~/.openclaw/config。
    """

    name = "openclaw"
    cli_name = "openclaw"

    def is_available(self) -> bool:
        try:
            subprocess.run(
                ["openclaw", "--version"],
                capture_output=True,
                timeout=10,
            )
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def build_command(
        self,
        prompt: str,
        mcp_config: dict,
        work_dir: str,
        extra_args: dict,
    ) -> list[str]:
        cmd = [
            "openclaw",
            "--prompt", prompt,
            "--no-interactive",
        ]

        return cmd


# ── Provider 注册表 ─────────────────────────────────────────

PROVIDERS: dict[str, BaseProvider] = {
    "claude": ClaudeCodeProvider(),
    "codex": CodexProvider(),
    "openclaw": OpenClawProvider(),
}


def get_provider(name: str) -> BaseProvider:
    """获取指定 Provider。"""
    provider = PROVIDERS.get(name.lower())
    if not provider:
        available = ", ".join(PROVIDERS.keys())
        raise ValueError(f"未知的 Provider: {name}。可用: {available}")
    return provider


def list_providers() -> list[dict]:
    """列出所有可用的 Provider 及安装状态。"""
    result = []
    for name, provider in PROVIDERS.items():
        result.append({
            "name": name,
            "cli": provider.cli_name,
            "available": provider.is_available(),
        })
    return result
