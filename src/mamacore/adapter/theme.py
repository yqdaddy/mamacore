"""排版主题管理 —— 从 config/themes/ 加载和管理排版主题。"""

import json
from pathlib import Path
from typing import Optional

THEMES_DIR = Path(__file__).parent.parent / "config" / "themes"


def list_themes() -> list[str]:
    """列出所有可用排版主题名称。"""
    if not THEMES_DIR.exists():
        return ["default"]
    return [f.stem for f in THEMES_DIR.iterdir() if f.suffix == ".json"]


def load_theme(name: str) -> Optional[dict]:
    """加载指定主题的 JSON 配置。

    Args:
        name: 主题名称（不含 .json 后缀）
    """
    theme_path = THEMES_DIR / f"{name}.json"
    if theme_path.exists():
        with open(theme_path, encoding="utf-8") as f:
            return json.load(f)
    return None


def get_theme_css(theme_name: str = "default") -> str:
    """获取主题 CSS 变量声明，用于内联样式。"""
    theme = load_theme(theme_name)
    if not theme:
        return ""

    css = theme.get("css", {})
    styles = []
    for key, value in css.items():
        css_key = key.replace("_", "-")
        styles.append(f"--{css_key}: {value}")
    return "; ".join(styles)
