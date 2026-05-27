import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from mamacore.adapter.wechat_format import render_containers, markdown_to_wechat_html
from mamacore.adapter.theme import list_themes, load_theme
from mamacore.adapter.seo import analyze_seo

def test_dialogue():
    html = render_containers(':::dialogue\nA: 你好\n:::end')
    assert 'mama-dialogue' in html

def test_callout():
    html = render_containers(':::callout\n提示\n:::end')
    assert 'mama-callout' in html

def test_timeline():
    html = render_containers(':::timeline\n2024.01: 开始\n:::end')
    assert 'mama-timeline' in html

def test_md_to_html():
    html = markdown_to_wechat_html('# 标题\n\n**粗体**\n\n[链接](https://a.com)')
    assert '<h1' in html
    assert '<strong>' in html
    assert 'https://a.com' in html

def test_theme_list():
    themes = list_themes()
    assert 'default' in themes

def test_theme_load():
    theme = load_theme('default')
    assert theme is not None
    assert 'css' in theme

def test_seo():
    result = analyze_seo('# AI工具评测\n\nAI正在改变世界', ['AI'])
    assert result['score'] >= 0
