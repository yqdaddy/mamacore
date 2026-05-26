#!/usr/bin/env python3
"""M.A.M.A. Core CLI -- 独立命令行入口，不依赖 Claude Code。"""

import typer
import asyncio
import sys
from pathlib import Path

app = typer.Typer(
    name="mama",
    help="公众号全流程自动化 CLI",
    add_completion=False,
)

# ============================================================
# 热点
# ============================================================

@app.command("hot-today")
def hot_today(
    source: str = typer.Option("gzh", "-s", "--source", help="数据源: gzh=公众号爆款, weibo/zhihu/toutiao=DailyHotApi"),
    keyword: str = typer.Option("", "-k", "--keyword", help="搜索关键词（仅 source=gzh 时有效）"),
    count: int = typer.Option(10, "-n", "--count", help="返回数量"),
    days: int = typer.Option(7, "-d", "--days", help="时间范围（天），仅 source=gzh 时有效"),
):
    """查看今日热点 / 公众号爆款文章。"""
    from mamacore.hot_topics import register_tools
    from mamacore.server import mcp

    register_tools(mcp)

    async def _run():
        from mamacore.hot_topics import _query_gzh_explosive, _query_dailyhot
        if source == "gzh":
            result = await _query_gzh_explosive(keyword, count, days)
        else:
            result = await _query_dailyhot(source, count)
        typer.echo(result)

    asyncio.run(_run())


# ============================================================
# 写作
# ============================================================

def _generate_title_candidates(topic: str, framework: str, count: int = 5) -> list[dict]:
    """Generate title candidates for the given topic and framework.

    This is a placeholder that will be replaced once LLM integration is complete.
    Returns simulated title options with scores and pattern tags.
    """
    # Simulated title patterns based on framework
    patterns_map = {
        "checklist": ["数字", "清单"],
        "pain": ["痛点", "悬念"],
        "compare": ["对比", "数字"],
        "narrative": ["情绪", "人称"],
    }
    patterns = patterns_map.get(framework, ["数字", "悬念"])

    candidates = [
        {"text": f"{topic}：{count} 个你必须知道的真相", "score": 85, "patterns": patterns},
        {"text": f"为什么越来越多人都在关注{topic}？", "score": 72, "patterns": ["悬念", "情绪"]},
        {"text": f"关于{topic}，这篇可能是最全面的指南", "score": 68, "patterns": ["数字", "痛点"]},
        {"text": f"我研究了 100 篇{topic}相关文章，总结出这份清单", "score": 78, "patterns": ["数字", "清单"]},
        {"text": f"别再被{topic}骗了！真相在这里", "score": 82, "patterns": ["痛点", "情绪"]},
    ]
    return sorted(candidates, key=lambda x: x["score"], reverse=True)[:count]


@app.command("write")
def write_article(
    topic: str = typer.Argument(..., help="文章主题"),
    framework: str = typer.Option("checklist", "-f", "--framework", help="文章框架"),
    style: str = typer.Option("default", "-s", "--style", help="写作风格"),
    output: str = typer.Option("", "-o", "--output", help="输出文件路径"),
    dry_run: bool = typer.Option(False, "--dry-run", help="仅打印生成的 prompt，不执行 LLM 调用"),
):
    """生成公众号文章。"""
    from mamacore.writer.framework import get_framework_prompt
    from mamacore.writer.style import build_style_system_prompt

    framework_prompt = get_framework_prompt(framework)
    style_prompt = build_style_system_prompt(style)
    titles = _generate_title_candidates(topic, framework, count=5)
    best_title = titles[0]["text"] if titles else topic

    if dry_run:
        typer.echo("=== Dry Run: 即将发送给 LLM 的 Prompt ===\n")
        typer.echo(f"System:\n{framework_prompt}\n{style_prompt}\n")
        typer.echo(f"User:\n生成一篇关于「{topic}」的文章，框架: {framework}\n")
        typer.echo(f"\n=== 预计 Token 消耗: ~{len(framework_prompt + style_prompt + topic) // 3} tokens ===")
        return

    article = f"""# {best_title}

> 本文基于 {framework} 框架生成。

（此处为模拟输出，接入 LLM 后将生成完整内容。）

## 推荐标题选项:
"""
    for i, t in enumerate(titles, 1):
        article += f"\n{i}. 【{t['score']}分】{t['text']} ({', '.join(t['patterns'])})"

    if output:
        Path(output).write_text(article, encoding="utf-8")
        typer.echo(f"文章已保存到: {output}")
    else:
        typer.echo(article)


# ============================================================
# 排版
# ============================================================

@app.command("format")
def format_article(
    input_file: str = typer.Argument(..., help="输入文件路径"),
    theme: str = typer.Option("default", "-t", "--theme", help="排版主题"),
    output: str = typer.Option("", "-o", "--output", help="输出文件路径"),
):
    """将 Markdown 文章转为公众号 HTML。"""
    from mamacore.adapter.wechat_format import markdown_to_wechat_html
    from mamacore.adapter.theme import load_theme

    content = Path(input_file).read_text(encoding="utf-8")
    theme_config = load_theme(theme)
    html = markdown_to_wechat_html(content, theme_config)

    if output:
        Path(output).write_text(html, encoding="utf-8")
        typer.echo(f"HTML 已保存到: {output}")
    else:
        typer.echo(html)


# ============================================================
# 安全检测
# ============================================================

@app.command("check")
def check_sensitive(
    input_file: str = typer.Argument(..., help="输入文件路径"),
    strict: bool = typer.Option(False, "--strict", help="严格模式"),
):
    """检测文章敏感词。"""
    from mamacore.safety.sensitive_words import check_sensitive

    if not Path(input_file).exists():
        typer.echo(f"错误: 文件不存在: {input_file}", err=True)
        raise typer.Exit(1)

    content = Path(input_file).read_text(encoding="utf-8")
    result = check_sensitive(content, strict)

    status = "通过" if result["passed"] else "未通过"
    typer.echo(f"\n敏感词检测: {status}")
    typer.echo(f"问题数: {result['total_issues']} (高:{result['high']} 中:{result['medium']} 低:{result['low']})")

    if result["issues"]:
        for issue in result["issues"]:
            risk_icon = {"high": "[!]", "medium": "[~]", "low": "[i]"}.get(issue["risk"], "[ ]")
            typer.echo(f"  {risk_icon} {issue['word']}: {issue['suggestion']}")


# ============================================================
# SEO 分析
# ============================================================

@app.command("seo")
def seo_check(
    input_file: str = typer.Argument(..., help="输入文件路径"),
    keywords: str = typer.Argument(..., help="目标关键词"),
):
    """微信搜一搜 SEO 分析。

    USAGE: mama seo <文章文件> <关键词1,关键词2,...>
    """
    from mamacore.adapter.seo import analyze_seo

    content = Path(input_file).read_text(encoding="utf-8")
    kw_list = [k.strip() for k in keywords.split(",")]
    result = analyze_seo(content, kw_list)

    typer.echo(f"\nSEO 评分: {result['score']}/100")
    for dim, ok in result["checklist"].items():
        icon = "通过" if ok else "未通过"
        typer.echo(f"  [{icon}] {dim}")

    if result.get("suggestions"):
        typer.echo("\n建议:")
        for s in result["suggestions"]:
            typer.echo(f"  - {s}")


# ============================================================
# 数据分析
# ============================================================

@app.command("analyze")
def analyze(
    account: str = typer.Option(..., "-a", "--account", help="公众号 ID"),
    days: int = typer.Option(30, "-d", "--days", help="分析天数"),
    csv: str = typer.Option("", "--csv", help="导入 CSV 文件路径"),
):
    """分析公众号数据。"""
    from mamacore.analytics.metrics import calculate_account_profile, get_top_articles
    from mamacore.analytics.scraper import import_csv, load_articles

    if csv:
        count = import_csv(csv, account)
        typer.echo(f"已导入 {count} 篇文章数据。")

    articles = load_articles(account, days)
    if not articles:
        typer.echo("暂无数据。请先运行数据导入或连接 API。")
        raise typer.Exit(1)

    profile = calculate_account_profile(account, days)
    typer.echo(f"\n账号画像 ({account}, {days}天)")
    typer.echo(f"  文章总数: {profile.total_articles}")
    typer.echo(f"  平均阅读: {profile.avg_reads}")
    typer.echo(f"  平均点赞: {profile.avg_likes}")
    typer.echo(f"  平均互动率: {profile.avg_interaction_rate:.2%}")
    typer.echo(f"  最佳发文时间: {profile.best_publish_hour}:00")

    typer.echo(f"\n阅读排行 Top 5:")
    for i, a in enumerate(get_top_articles(account, days, limit=5), 1):
        typer.echo(f"  {i}. {a['title']} -- 阅读 {a['reads']}")


# ============================================================
# 发布
# ============================================================

@app.command("publish")
def publish(
    input_file: str = typer.Argument(..., help="文章文件路径 (HTML)"),
    title: str = typer.Option("", "-t", "--title", help="文章标题（默认使用文件名）"),
):
    """发布文章到公众号草稿箱。"""
    typer.echo("发布功能需要配置 MAMA_WECHAT_APP_ID 和 MAMA_WECHAT_APP_SECRET")
    typer.echo("请先在公众号后台获取 AppID 和 AppSecret，然后：")
    typer.echo("  export MAMA_WECHAT_APP_ID=xxx")
    typer.echo("  export MAMA_WECHAT_APP_SECRET=xxx")


# ============================================================
# 标题评分
# ============================================================

@app.command("score-title")
def score_title(title: str = typer.Argument(..., help="要评分的标题")):
    """给标题打分。"""
    from mamacore.writer.title import score_title as _score

    result = _score(title)
    typer.echo(f"\n标题: {title}")
    typer.echo(f"评分: {result['score']}/100")
    typer.echo(f"模式: {', '.join(result['patterns'])}")
    for dim, pts in result["breakdown"].items():
        typer.echo(f"  {dim}: {pts}/25")
    if result.get("suggestions"):
        typer.echo("\n建议:")
        for s in result["suggestions"]:
            typer.echo(f"  - {s}")


def main():
    app()


# ============================================================
# 独立运行编排器 (Paseo 风格)
# ============================================================

@app.command("run")
def run_task(
    task: str = typer.Argument(..., help="任务描述，如：写一篇关于 AI Agent 的文章"),
    provider: str = typer.Option("claude", "-p", "--provider", help="Agent: claude/codex/openclaw"),
    framework: str = typer.Option("", "-f", "--framework", help="强制框架: checklist/pain/compare/narrative"),
    style: str = typer.Option("", "-s", "--style", help="强制风格: satire/tongue/analytical/experience/science"),
    model: str = typer.Option("", "--model", help="指定模型名称"),
    timeout: int = typer.Option(1800, "--timeout", help="超时时间（秒）"),
    yes: bool = typer.Option(False, "-y", "--yes", help="跳过确认"),
):
    """独立运行公众号文章任务，不依赖 Claude Code 宿主。

    通过 Claude Code / Codex / OpenClaw 等 CLI Agent 驱动全流程。

    示例:
        mama run "写一篇关于 AI Agent 的文章" -p claude
        mama run "写一篇关于职场成长的文章" -p claude -f pain -s experience
        mama run "写一篇关于大模型的对比评测" -p codex -f compare -y
    """
    from mamacore.orchestrator.runner import run_task as _run

    result = _run(
        task_desc=task,
        provider_name=provider,
        framework=framework,
        style=style,
        model=model,
        timeout=timeout,
        no_confirm=yes,
    )

    if result.get("error"):
        typer.echo(f"错误: {result['error']}", err=True)
        raise typer.Exit(1)

    if result.get("status") == "cancelled":
        typer.echo("任务已取消。")
        return

    status_icon = "完成" if result["status"] == "completed" else "失败"
    typer.echo(f"\n任务 {status_icon}")
    if result.get("task_id"):
        typer.echo(f"任务 ID: {result['task_id']}")
    if result.get("log_file"):
        typer.echo(f"日志文件: {result['log_file']}")


@app.command("ls")
def list_tasks(
    status: str = typer.Option("all", "-s", "--status", help="过滤: all/running/completed/failed/killed"),
):
    """查看运行中的任务列表。"""
    from mamacore.orchestrator.task_manager import TaskManager

    tm = TaskManager()
    tasks = tm.list_tasks(status)

    if not tasks:
        typer.echo("暂无任务。")
        return

    typer.echo(f"\n{'ID':<8} {'Provider':<10} {'状态':<10} {'任务描述':<40} {'开始时间'}")
    typer.echo("-" * 120)
    for t in tasks:
        typer.echo(
            f"{t['id']:<8} {t['provider']:<10} {t['status']:<10} "
            f"{t['task_desc'][:40]:<40} {t.get('started_at', '')[:19]}"
        )


@app.command("attach")
def attach_task(task_id: str = typer.Argument(..., help="任务 ID")):
    """连接到正在运行的任务，查看实时日志。"""
    from mamacore.orchestrator.task_manager import TaskManager

    tm = TaskManager()
    task = tm.get_task(task_id)
    if not task:
        typer.echo(f"任务 {task_id} 不存在。", err=True)
        raise typer.Exit(1)

    log_file = task.get("log_file")
    if not log_file or not Path(log_file).exists():
        typer.echo(f"任务 {task_id} 无日志文件。", err=True)
        return

    typer.echo(f"=== 任务 {task_id} 日志 ===")
    typer.echo(f"Provider: {task['provider']}")
    typer.echo(f"状态: {task['status']}")
    typer.echo(f"---\n")

    # 实时流式输出（tail -f）
    import subprocess
    subprocess.run(["tail", "-f", log_file])


@app.command("kill")
def kill_task(task_id: str = typer.Argument(..., help="任务 ID")):
    """终止正在运行的任务。"""
    from mamacore.orchestrator.task_manager import TaskManager

    tm = TaskManager()
    if tm.kill(task_id):
        typer.echo(f"任务 {task_id} 已终止。")
    else:
        typer.echo(f"任务 {task_id} 不存在或已结束。", err=True)


@app.command("providers")
def show_providers():
    """列出可用的 Agent Provider 及安装状态。"""
    from mamacore.orchestrator.runner import list_available_providers

    providers = list_available_providers()
    typer.echo(f"\n{'Provider':<12} {'CLI 命令':<12} {'状态'}")
    typer.echo("-" * 50)
    for p in providers:
        icon = "已安装" if p["available"] else "未安装"
        typer.echo(f"{p['name']:<12} {p['cli']:<12} {icon}")

    typer.echo("\n使用方式: mama run '任务描述' -p <provider>")


if __name__ == "__main__":
    main()
