#!/usr/bin/env python3
"""M.A.M.A. Core —— 公众号全流程自动化 MCP Server。

Harness + Model = Agent

提供以下能力：
- 热点抓取（DailyHotApi）
- 文章生成（框架/风格/大纲/初稿/增强/标题）
- 图片生成（DALL-E / 通义万相）
- 公众号排版（容器语法 + 排版主题 + SEO）
- 数据分析（采集/指标/选题/标题A/B/爆款模式/策略推荐）
- 安全检测（敏感词 + 广告法）
- 发布与多平台同步（公众号 + 知乎/头条/CSDN）
"""

import sys
import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# 初始化服务器，含详细 instructions 帮助 Claude Code 发现工具
mcp = FastMCP(
    "mamacore",
    instructions=(
        "M.A.M.A. Core 是公众号全流程自动化工具。当用户提到写公众号、"
        "写推文、公众号文章、热点抓取、内容策略、效果复盘时使用这些工具。"
        "核心流程：热点 → 选题 → 框架 → 大纲 → 写作 → 配图 → 排版 → "
        "敏感词检查 → 发布草稿 → 多平台同步 → 数据分析。"
        "使用 mama_hot_topics 查看热点，mama_write_article 生成文章，"
        "mama_content_strategy 获取内容策略，mama_analyze_account 分析账号数据。"
    ),
)


def _load_config() -> dict:
    """加载配置文件，返回合并后的配置字典。"""
    import yaml
    config_dir = Path(__file__).parent / "config"
    merged: dict = {}
    for name in ("style.yaml", "platform_rules.yaml", "image_config.yaml"):
        path = config_dir / name
        if path.exists():
            with open(path) as f:
                merged.update(yaml.safe_load(f) or {})
    return merged


# ============================================================
# 注册 Tools（按需导入，避免未实现模块阻塞启动）
# ============================================================

def _register_tools() -> None:
    """动态注册各模块的 MCP Tools。

    每个模块应导出 register_tools(mcp) 函数用于工具注册。
    """
    import importlib

    modules = [
        "mamacore.hot_topics",
        "mamacore.writer",
        "mamacore.image",
        "mamacore.adapter",
        "mamacore.analytics",
        "mamacore.safety",
        "mamacore.publisher",
    ]

    for mod_name in modules:
        try:
            mod = importlib.import_module(mod_name)
            if hasattr(mod, "register_tools"):
                mod.register_tools(mcp)
                print(f"[mamacore] 已注册模块: {mod_name}", file=sys.stderr)
        except Exception as e:
            print(f"[mamacore] 跳过模块 {mod_name}: {e}", file=sys.stderr)


_register_tools()


# ============================================================
# 健康检查
# ============================================================

@mcp.tool()
async def mama_health_check() -> str:
    """检查 M.A.M.A. Core 服务是否正常运行。返回版本和可用模块列表。"""
    import importlib
    modules = {
        "hot_topics": "mamacore.hot_topics",
        "writer": "mamacore.writer",
        "image": "mamacore.image",
        "adapter": "mamacore.adapter",
        "analytics": "mamacore.analytics",
        "safety": "mamacore.safety",
        "publisher": "mamacore.publisher",
    }
    status = {}
    for name, path in modules.items():
        try:
            importlib.import_module(path)
            status[name] = "可用"
        except Exception:
            status[name] = "不可用"

    version = "0.1.0"
    lines = [f"## M.A.M.A. Core v{version}", "", "模块状态：", ""]
    for name, st in status.items():
        lines.append(f"- {name}: {st}")
    return "\n".join(lines)


# ============================================================
# 注册 Resources
# ============================================================

@mcp.resource("config://style")
def get_style_config() -> str:
    """当前写作风格配置。"""
    import yaml
    path = Path(__file__).parent / "config" / "style.yaml"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return "未配置 style.yaml"


@mcp.resource("config://platform-rules")
def get_platform_rules() -> str:
    """公众号平台规则（字数限制、敏感词、SEO策略）。"""
    import yaml
    path = Path(__file__).parent / "config" / "platform_rules.yaml"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return "未配置 platform_rules.yaml"


@mcp.resource("themes://list")
def list_themes() -> str:
    """列出所有可用的排版主题。"""
    themes_dir = Path(__file__).parent / "config" / "themes"
    if not themes_dir.exists():
        return "无可用主题"
    themes = [f.name for f in themes_dir.iterdir() if f.suffix == ".json"]
    return "可用排版主题：\n\n" + "\n".join(f"- {t}" for t in sorted(themes))


# ============================================================
# 注册 Prompts（SKILL.md 风格工作流注入）
# ============================================================

from mcp.server.fastmcp.prompts import base as prompt_base


@mcp.prompt(title="公众号文章全流程工作流")
def wechat_article_workflow(
    topic: str,
    framework: str = "checklist",
    style: str = "default",
) -> list[prompt_base.Message]:
    """引导模型按步骤完成公众号文章：热点 → 选题 → 框架 → 写作 → 配图 → 排版 → 发布。"""
    skill_path = Path(__file__).parent.parent.parent / "skills" / "wechat_article" / "SKILL.md"
    if skill_path.exists():
        workflow_content = skill_path.read_text(encoding="utf-8")
    else:
        workflow_content = f"""
## 公众号文章全流程工作流

你正在执行公众号文章创作。请严格按以下步骤进行：

1. **热点分析**：调用 `mama_hot_topics` 获取当前热点，筛选与 "{topic}" 相关的话题
2. **选题确认**：结合热点和用户输入确定选题
3. **框架选择**：使用 {framework} 框架（checklist=清单型, pain=痛点型, compare=对比型, narrative=叙事型）
4. **大纲生成**：调用 `mama_generate_outline` 生成文章大纲
5. **初稿写作**：调用 `mama_write_article` 生成文章初稿
6. **内容增强**：添加案例、数据、金句
7. **标题生成**：生成 10 个候选标题并评分
8. **配图生成**：调用 `mama_generate_images` 生成封面和内文配图
9. **排版适配**：调用 `mama_format_article` 转为公众号格式
10. **敏感词检查**：调用 `mama_check_sensitive` 检测敏感词
11. **发布草稿**：调用 `mama_publish_draft` 发布到公众号草稿箱

参数：
- 主题: {topic}
- 框架: {framework}
- 风格: {style}
"""

    return [
        prompt_base.UserMessage(workflow_content),
        prompt_base.AssistantMessage("我理解了公众号文章全流程。从第 1 步热点分析开始。"),
    ]


@mcp.prompt(title="数据分析与内容策略工作流")
def analytics_workflow(
    account_id: str,
    days: int = 30,
) -> list[prompt_base.Message]:
    """引导模型完成数据采集 → 指标计算 → 爆款模式识别 → 内容策略推荐。"""
    skill_path = Path(__file__).parent.parent.parent / "skills" / "wechat_analytics" / "SKILL.md"
    if skill_path.exists():
        workflow_content = skill_path.read_text(encoding="utf-8")
    else:
        workflow_content = f"""
## 数据分析与内容策略工作流

你正在执行公众号数据分析。请按以下步骤进行：

1. **数据采集**：调用 `mama_analyze_account` 获取最近 {days} 天的文章数据
2. **指标计算**：分析阅读率、互动率、分享率等核心指标
3. **选题热力图**：调用 `mama_topic_heatmap` 找出表现最好的话题
4. **爆款模式**：调用 `mama_content_strategy` 生成内容策略报告
5. **竞品分析**：调用 `mama_competitor_gap` 对比竞品账号
6. **策略输出**：输出"下周该写什么"的具体建议

参数：
- 账号: {account_id}
- 时间范围: {days} 天
"""

    return [
        prompt_base.UserMessage(workflow_content),
        prompt_base.AssistantMessage("我理解了数据分析工作流。从第 1 步数据采集开始。"),
    ]


@mcp.prompt(title="图片生成工作流")
def image_workflow(
    article_id: str,
    image_count: int = 3,
) -> list[prompt_base.Message]:
    """引导模型完成图片生成：选择模板 → 生成 → 关联文章。"""
    return [
        prompt_base.UserMessage(
            f"请为文章 {article_id} 生成 {image_count} 张配图。"
            "流程：1. 读取文章确定主题和情绪 2. 选择合适的图片提示词模板 "
            "3. 调用 mama_generate_images 生成图片 4. 将图片关联到文章对应段落"
        ),
        prompt_base.AssistantMessage("我理解了图片生成工作流。先读取文章内容确定风格。"),
    ]


# ============================================================
# 入口
# ============================================================

def main():
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    if transport == "stdio":
        mcp.run(transport="stdio")
    elif transport == "streamable-http":
        mcp.run(transport="streamable-http")
    else:
        print(f"不支持的传输方式: {transport}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
