"""公众号排版适配器 —— 容器语法渲染 + Markdown 转公众号 HTML。

容器语法:
    :::dialogue ... :::end    → 对话气泡
    :::timeline ... :::end     → 时间线
    :::callout ... :::end      → 引用框/提示框
    :::code ... :::end         → 代码块（带语法高亮）
"""

import re
from typing import Optional

# 容器语法处理器
_CONTAINER_HANDLERS: dict = {}


def register_container(name: str):
    """注册容器语法处理器装饰器。"""
    def decorator(func):
        _CONTAINER_HANDLERS[name] = func
        return func
    return decorator


@register_container("dialogue")
def _render_dialogue(content: str, **kwargs) -> str:
    """对话气泡容器。

    输入:
    :::dialogue
    A: 你觉得 AI Agent 怎么样？
    B: 我觉得还需要更多实际案例。
    :::end

    输出: 带样式的对话气泡 HTML
    """
    lines = content.strip().split("\n")
    html_parts = ['<div class="mama-dialogue">']

    for line in lines:
        line = line.strip()
        if not line:
            continue
        # 匹配 "角色: 内容" 格式
        match = re.match(r"^(.+?):\s*(.*)", line)
        if match:
            speaker = match.group(1).strip()
            text = match.group(2).strip()
            html_parts.append(
                f'<div class="mama-dialogue-item">'
                f'<span class="mama-dialogue-speaker">{speaker}</span>'
                f'<span class="mama-dialogue-text">{text}</span>'
                f'</div>'
            )
        else:
            html_parts.append(
                f'<div class="mama-dialogue-item">'
                f'<span class="mama-dialogue-text">{line}</span>'
                f'</div>'
            )

    html_parts.append("</div>")
    return "\n".join(html_parts)


@register_container("timeline")
def _render_timeline(content: str, **kwargs) -> str:
    """时间线容器。

    输入:
    :::timeline
    2024.01: 项目启动
    2024.03: 第一个版本发布
    2024.06: 用户突破 10 万
    :::end
    """
    lines = content.strip().split("\n")
    html_parts = ['<div class="mama-timeline">']

    for line in lines:
        line = line.strip()
        if not line:
            continue
        # 匹配 "时间: 事件" 格式
        match = re.match(r"^([^:]+):\s*(.*)", line)
        if match:
            time_label = match.group(1).strip()
            event = match.group(2).strip()
            html_parts.append(
                f'<div class="mama-timeline-item">'
                f'<span class="mama-timeline-label">{time_label}</span>'
                f'<span class="mama-timeline-event">{event}</span>'
                f'</div>'
            )
        else:
            html_parts.append(
                f'<div class="mama-timeline-item">'
                f'<span class="mama-timeline-event">{line}</span>'
                f'</div>'
            )

    html_parts.append("</div>")
    return "\n".join(html_parts)


@register_container("callout")
def _render_callout(content: str, variant: str = "info", **kwargs) -> str:
    """引用框/提示框容器。

    变体: info / warning / success / tip

    输入:
    :::callout variant=warning
    注意：此操作不可逆！
    :::end
    """
    variant_classes = {
        "info": ("#e6f7ff", "#1890ff", "ℹ️"),
        "warning": ("#fff7e6", "#fa8c16", "⚠️"),
        "success": ("#f6ffed", "#52c41a", "✅"),
        "tip": ("#f9f0ff", "#722ed1", "💡"),
    }
    bg, border, icon = variant_classes.get(variant, variant_classes["info"])

    content_html = content.strip().replace("\n", "<br>")
    return (
        f'<div class="mama-callout" style="background:{bg};border-left:4px solid {border};padding:12px 16px;border-radius:4px;margin:16px 0;">'
        f'<div style="color:{border};font-weight:600;margin-bottom:8px;">{icon} {variant.upper()}</div>'
        f'<div>{content_html}</div>'
        f'</div>'
    )


@register_container("code")
def _render_code(content: str, language: str = "", **kwargs) -> str:
    """代码块容器（公众号不支持 JS 高亮，用样式模拟）。"""
    lang_label = f" {language}" if language else ""
    code_html = content.strip().replace("<", "&lt;").replace(">", "&gt;")
    return (
        f'<div class="mama-code" style="background:#f5f5f5;padding:16px;border-radius:6px;font-family:Menlo,Monaco,monospace;font-size:13px;line-height:1.6;margin:16px 0;">'
        f'<div style="color:#888;font-size:11px;margin-bottom:8px;">CODE{lang_label}</div>'
        f'<pre style="margin:0;white-space:pre-wrap;word-break:break-all;color:#333;">{code_html}</pre>'
        f'</div>'
    )


def render_containers(markdown: str) -> str:
    """渲染所有容器语法，返回替换后的 Markdown。"""
    # 匹配 :::container_name [args] ... :::end
    pattern = r":::(\w+)(.*?)\n(.*?):::end"

    def replacer(match):
        container_name = match.group(1)
        args_str = match.group(2).strip()
        content = match.group(3)

        # 解析参数 key=value
        args = {}
        if args_str:
            for part in args_str.split():
                if "=" in part:
                    k, v = part.split("=", 1)
                    args[k] = v

        handler = _CONTAINER_HANDLERS.get(container_name)
        if handler:
            return handler(content, **args)
        else:
            # 未知容器，保留原文
            return match.group(0)

    return re.sub(pattern, replacer, markdown, flags=re.DOTALL)


def markdown_to_wechat_html(markdown: str, theme: Optional[dict] = None) -> str:
    """将 Markdown 转换为公众号 HTML。

    流程:
    1. 先渲染容器语法
    2. 处理 Markdown 基本语法（标题/列表/链接/粗体/斜体）
    3. 应用排版主题

    Args:
        markdown: Markdown 格式文章
        theme: 排版主题配置字典

    Returns:
        公众号可用的 HTML 字符串
    """
    # 第一步: 渲染容器
    html = render_containers(markdown)

    # 第二步: Markdown 基本语法转换
    # 代码块（保留 pre 标签）
    html = re.sub(
        r"```(\w*)\n(.*?)```",
        lambda m: f'<pre><code>{m.group(2).strip()}</code></pre>',
        html,
        flags=re.DOTALL,
    )

    # 行内代码
    html = re.sub(
        r"`([^`]+)`",
        r'<code style="background:#f5f5f5;padding:2px 6px;border-radius:3px;font-family:Menlo,monospace;font-size:13px;color:#e83e8c;">\1</code>',
        html,
    )

    # 标题 (h1-h3)
    html = re.sub(r"^### (.+)$", r'<h3 style="font-size:16px;font-weight:600;margin:20px 0 10px;">\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r"^## (.+)$", r'<h2 style="font-size:17px;font-weight:600;margin:24px 0 12px;border-bottom:1px solid #eee;padding-bottom:8px;">\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r"^# (.+)$", r'<h1 style="font-size:18px;font-weight:700;margin:28px 0 14px;">\1</h1>', html, flags=re.MULTILINE)

    # 引用块
    html = re.sub(
        r"^> (.+)$",
        r'<blockquote style="border-left:4px solid #e0e0e0;padding:8px 16px;margin:16px 0;color:#888;background:#f7f7f7;">\1</blockquote>',
        html,
        flags=re.MULTILINE,
    )

    # 粗体和斜体
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)

    # 链接
    html = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" style="color:#576b95;text-decoration:none;">\1</a>', html)

    # 无序列表
    html = re.sub(
        r"^- (.+)$",
        r'<li style="margin:4px 0;list-style:disc;margin-left:20px;">\1</li>',
        html,
        flags=re.MULTILINE,
    )

    # 有序列表
    html = re.sub(
        r"^\d+\. (.+)$",
        r'<li style="margin:4px 0;list-style:decimal;margin-left:20px;">\1</li>',
        html,
        flags=re.MULTILINE,
    )

    # 分隔线
    html = re.sub(r"^---$", '<hr style="border:none;border-top:1px solid #eee;margin:24px 0;">', html, flags=re.MULTILINE)

    # 段落（简单换行处理）
    html = html.replace("\n\n", "</p><p>")
    html = html.replace("\n", "<br>")

    # 第三步: 应用主题
    if theme:
        font_family = theme.get("font_family", "-apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif")
        font_size = theme.get("font_size", "15px")
        line_height = theme.get("line_height", "1.75")
        color = theme.get("color", "#3f3f3f")

        html = (
            f'<section style="font-family:{font_family};font-size:{font_size};'
            f'line-height:{line_height};color:{color};padding:0 8px;">'
            f"{html}"
            f"</section>"
        )
    else:
        # 默认样式包裹
        html = (
            f'<section style="font-family:-apple-system,BlinkMacSystemFont,'
            f"'PingFang SC','Microsoft YaHei',sans-serif;"
            f'font-size:15px;line-height:1.75;color:#3f3f3f;padding:0 8px;">'
            f"{html}"
            f"</section>"
        )

    return html
