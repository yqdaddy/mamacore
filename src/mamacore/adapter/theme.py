"""排版主题管理 —— 从 adapter/themes/ 加载和管理排版主题。

整合了 wewrite 的 18 个排版主题。
"""

import json
import yaml
from pathlib import Path
from typing import Optional

THEMES_DIR = Path(__file__).parent / "themes"


def list_themes() -> list[str]:
    """列出所有可用排版主题名称。"""
    if not THEMES_DIR.exists():
        return ["professional-clean"]
    names = []
    for f in THEMES_DIR.iterdir():
        if f.suffix in (".yaml", ".yml", ".json"):
            names.append(f.stem)
    return sorted(names)


def load_theme(name: str) -> Optional[dict]:
    """加载指定主题的 YAML 配置。

    Args:
        name: 主题名称（不含后缀）
    """
    for ext in (".yaml", ".yml", ".json"):
        theme_path = THEMES_DIR / f"{name}{ext}"
        if theme_path.exists():
            with open(theme_path, encoding="utf-8") as f:
                if ext == ".json":
                    return json.load(f)
                return yaml.safe_load(f)
    return None
