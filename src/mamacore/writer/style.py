"""Style engine — reads config/style.yaml and generates LLM style prompts."""

import os
from pathlib import Path

import yaml

from mamacore.writer.models import WritingStyle

# Style descriptions for LLM system prompts
STYLE_PROMPTS: dict[str, str] = {
    "satire": """写作风格：讽刺吐槽
- 语气：尖锐、带刺，用讽刺和反讽揭示荒谬
- 句式：多用反问、排比、对比句，节奏紧凑
- 视角：旁观者分析，冷眼旁观但不冷漠
- 特点：善用类比和比喻，把抽象问题具象化
- 避免：过度人身攻击、纯粹抱怨不提供价值
""",
    "tongue": """写作风格：毒舌调侃
- 语气：幽默中带刺，调侃但不恶意
- 句式：多用双关、俏皮话、网络热梗
- 视角：第一人称或旁观者，轻松但有深度
- 特点：善用自嘲和反转，让读者笑着接受观点
- 避免：低俗用语、纯粹搞笑没有干货
""",
    "analytical": """写作风格：理性分析
- 语气：客观、冷静、有逻辑
- 句式：多用因果分析、数据支撑、结构化表达
- 视角：第三方分析师视角
- 特点：善用图表、数据、对比，论证严密
- 避免：情绪化表达、主观臆断
""",
    "experience": """写作风格：亲历分享
- 语气：真诚、接地气、有温度
- 句式：多用第一人称叙述，像在和朋友聊天
- 视角：第一人称亲历者
- 特点：善用真实细节、踩坑经历、心路历程
- 避免：过度包装、虚构经历、炫耀式叙事
""",
    "science": """写作风格：科普讲解
- 语气：通俗易懂但不失专业
- 句式：多用比喻、举例、类比解释复杂概念
- 视角：老师/讲解者
- 特点：善用"你知道吗"、"其实"等引导句式，化繁为简
- 避免：学术腔、堆砌术语、居高临下
""",
}

# Mapping from Chinese config values to enum keys
_CHINESE_TO_STYLE: dict[str, str] = {
    "讽刺调侃": "satire",
    "毒舌调侃": "tongue",
    "理性分析": "analytical",
    "亲历分享": "experience",
    "科普讲解": "science",
}

# Default config when style.yaml is not found
_DEFAULT_CONFIG: dict = {
    "default_persona": "第一人称亲历",
    "default_style": "讽刺调侃",
    "default_framework": "checklist",
    "default_word_count": [1500, 2500],
}


def _resolve_config_path() -> Path:
    """Resolve path to style.yaml config file."""
    # Try project config directory first
    config_path = Path(__file__).parent.parent / "config" / "style.yaml"
    if config_path.exists():
        return config_path
    # Fallback: relative to package root
    config_path = Path(__file__).parent.parent.parent.parent / "config" / "style.yaml"
    if config_path.exists():
        return config_path
    return config_path


def load_style_config() -> dict:
    """Load style configuration from YAML file."""
    config_path = _resolve_config_path()
    if not config_path.exists():
        return _DEFAULT_CONFIG.copy()
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or _DEFAULT_CONFIG.copy()


def get_style_prompt(style: WritingStyle | str) -> str:
    """Return the style system prompt for the given writing style."""
    key = style.value if isinstance(style, WritingStyle) else style
    prompt = STYLE_PROMPTS.get(key)
    if prompt is None:
        raise ValueError(
            f"Unknown writing style: {key!r}. "
            f"Valid options: {', '.join(STYLE_PROMPTS)}"
        )
    return prompt


def get_default_style() -> WritingStyle:
    """Get the default writing style from config."""
    config = load_style_config()
    chinese_style = config.get("default_style", "讽刺调侃")
    enum_key = _CHINESE_TO_STYLE.get(chinese_style, "satire")
    return WritingStyle(enum_key)


def get_default_framework() -> str:
    """Get the default framework type from config."""
    config = load_style_config()
    return config.get("default_framework", "checklist")


def get_default_word_count() -> tuple[int, int]:
    """Get the default word count range from config."""
    config = load_style_config()
    wc = config.get("default_word_count", [1500, 2500])
    return (wc[0], wc[1])


def build_style_system_prompt(
    style: WritingStyle | str,
    framework_prompt: str = "",
    extra_instructions: str = "",
) -> str:
    """Build a complete system prompt combining style + framework + extras.

    This is the prompt template passed to the LLM for article generation.
    """
    style_prompt = get_style_prompt(style)
    parts = [style_prompt]
    if framework_prompt:
        parts.append(framework_prompt)
    if extra_instructions:
        parts.append(extra_instructions)
    return "\n".join(parts)
