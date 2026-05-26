"""排版适配器测试。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mamacore.adapter.wechat_format import (
    render_containers,
    markdown_to_wechat_html,
)
from mamacore.adapter.theme import list_themes, load_theme


class TestContainerRendering:
    """容器语法渲染测试。"""

    def test_dialogue_container(self):
        """测试对话气泡容器。"""
        md = ":::dialogue\nA: 你好\nB: 你好\n:::end"
        html = render_containers(md)
        assert "mama-dialogue" in html
        assert "mama-dialogue-speaker" in html

    def test_timeline_container(self):
        """测试时间线容器。"""
        md = ":::timeline\n2024.01: 项目启动\n2024.03: 发布\n:::end"
        html = render_containers(md)
        assert "mama-timeline" in html
        assert "mama-timeline-label" in html

    def test_callout_container(self):
        """测试引用框容器。"""
        md = ":::callout variant=warning\n注意\n:::end"
        html = render_containers(md)
        assert "mama-callout" in html

    def test_code_container(self):
        """测试代码块容器。"""
        md = ':::code language=python\nprint("hello")\n:::end'
        html = render_containers(md)
        # 代码容器会生成 mama-code class
        assert "mama-code" in html.lower() or "code" in html.lower()

    def test_unknown_container_preserved(self):
        """测试未知容器保留原文。"""
        md = ":::unknown\ntest\n:::end"
        html = render_containers(md)
        assert ":::unknown" in html

    def test_multiple_containers(self):
        """测试多个容器。"""
        md = """
:::dialogue
A: 你好
:::end

:::callout
提示
:::end
"""
        html = render_containers(md)
        assert html.count("mama-dialogue") >= 1
        assert html.count("mama-callout") >= 1


class TestMarkdownToHTML:
    """Markdown 转 HTML 测试。"""

    def test_heading_h1(self):
        """测试 h1 标题。"""
        html = markdown_to_wechat_html("# 标题")
        assert "<h1" in html

    def test_heading_h2(self):
        """测试 h2 标题。"""
        html = markdown_to_wechat_html("## 标题")
        assert "<h2" in html

    def test_heading_h3(self):
        """测试 h3 标题。"""
        html = markdown_to_wechat_html("### 标题")
        assert "<h3" in html

    def test_bold_text(self):
        """测试粗体。"""
        html = markdown_to_wechat_html("**粗体**")
        assert "<strong>粗体</strong>" in html

    def test_italic_text(self):
        """测试斜体。"""
        html = markdown_to_wechat_html("*斜体*")
        assert "<em>斜体</em>" in html

    def test_inline_code(self):
        """测试行内代码。"""
        html = markdown_to_wechat_html("`code`")
        assert "<code" in html

    def test_link(self):
        """测试链接。"""
        html = markdown_to_wechat_html("[链接](https://example.com)")
        assert '<a href="https://example.com"' in html

    def test_blockquote(self):
        """测试引用块。"""
        html = markdown_to_wechat_html("> 引用内容")
        assert "<blockquote" in html

    def test_unordered_list(self):
        """测试无序列表。"""
        html = markdown_to_wechat_html("- 项目一\n- 项目二")
        assert "list-style:disc" in html

    def test_hr(self):
        """测试分隔线。"""
        html = markdown_to_wechat_html("---")
        assert "<hr" in html

    def test_container_in_markdown(self):
        """测试 Markdown 中的容器。"""
        md = "# 标题\n\n:::callout\n提示\n:::end"
        html = markdown_to_wechat_html(md)
        assert "mama-callout" in html
        assert "<h1" in html

    def test_theme_wrapping(self):
        """测试主题包裹。"""
        html = markdown_to_wechat_html("测试")
        assert 'font-family:' in html
        assert 'line-height:' in html


class TestThemeManagement:
    """排版主题管理测试。"""

    def test_list_themes(self):
        """测试列出主题。"""
        themes = list_themes()
        assert "default" in themes

    def test_load_default_theme(self):
        """测试加载默认主题。"""
        theme = load_theme("default")
        assert theme is not None
        assert "css" in theme

    def test_load_nonexistent_theme(self):
        """测试加载不存在的主题。"""
        theme = load_theme("nonexistent_theme_xyz")
        assert theme is None
