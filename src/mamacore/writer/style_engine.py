"""Style engine —— 读取 Persona 配置和写作指南，生成 LLM 风格提示词。

整合了 wewrite 的 6 个 Persona 和反 AI 检测写作指南。
"""

import os
from pathlib import Path

import yaml

from mamacore.writer.models import WritingStyle

# 新增：6 个精细 Persona（替代原来的简单字符串）
_PERSONA_DIR = Path(__file__).parent.parent / "config" / "personas"

# 反 AI 检测写作指南路径
_ANTI_AI_GUIDE = Path(__file__).parent / "references" / "writing-guide.md"

# 内容增强策略路径
_CONTENT_ENHANCE = Path(__file__).parent / "references" / "content-enhance.md"

# 阅读钩子指南路径
_READING_HOOKS = Path(__file__).parent / "references" / "reading-hooks.md"

# 框架选择指南路径
_FRAMEWORKS = Path(__file__).parent / "references" / "frameworks.md"

# 微信约束路径
_WECHAT_CONSTRAINTS = Path(__file__).parent.parent / "adapter" / "references" / "wechat-constraints.md"


def load_persona(name: str) -> dict:
    """加载指定 Persona 配置。"""
    persona_file = _PERSONA_DIR / f"{name}.yaml"
    if not persona_file.exists():
        # Fallback: try to find any matching persona
        for f in _PERSONA_DIR.glob("*.yaml"):
            with open(f) as pf:
                data = yaml.safe_load(pf)
                if data and data.get("name") == name:
                    return data
        raise ValueError(f"Persona not found: {name}. Available: {list_personas()}")
    with open(persona_file, encoding="utf-8") as f:
        return yaml.safe_load(f)


def list_personas() -> list[str]:
    """列出所有可用的 Persona 名称。"""
    if not _PERSONA_DIR.exists():
        return []
    return [f.stem for f in _PERSONA_DIR.glob("*.yaml")]


def get_persona_prompt(name: str) -> str:
    """将 Persona YAML 转换为 LLM 可理解的 prompt。"""
    persona = load_persona(name)

    lines = [f"## 写作人格：{persona.get('name', name)}", f"{persona.get('description', '')}", ""]

    # 核心参数
    if "voice_density" in persona:
        lines.append(f"- 人称密度：{persona['voice_density']}（{0.6 if persona['voice_density'] > 0.5 else '较低'}）")
    if "uncertainty_rate" in persona:
        lines.append(f"- 不确定性表达率：{persona['uncertainty_rate']}")
    if "paragraph_max_length" in persona:
        lines.append(f"- 段落最大长度：{persona['paragraph_max_length']} 字")
    if "single_sentence_paragraph_rate" in persona:
        lines.append(f"- 单句成段比例：{persona['single_sentence_paragraph_rate']}")

    # 情绪弧线
    if "emotional_arc" in persona:
        lines.append(f"- 情绪弧线：{persona['emotional_arc']}")
    if "opening_style" in persona:
        lines.append(f"- 开头风格：{persona['opening_style']}")
    if "closing_tendency" in persona:
        lines.append(f"- 结尾倾向：{persona['closing_tendency']}")

    # 语气词
    if "particles" in persona:
        lines.append(f"- 常用语气词：{', '.join(persona['particles'])}")

    # 经典句式
    if "sentence_patterns" in persona:
        lines.append("- 可适度使用的经典句式：")
        for p in persona["sentence_patterns"][:3]:  # 只取前 3 个
            lines.append(f"  - {p}")

    # 破句风格
    if "broken_sentence_styles" in persona:
        lines.append(f"- 破句风格：{', '.join(persona['broken_sentence_styles'])}")

    # 禁止事项
    if "avoid" in persona:
        lines.append("- 禁止事项：")
        for a in persona["avoid"]:
            lines.append(f"  - {a}")

    lines.append("")
    return "\n".join(lines)


def get_anti_ai_rules() -> str:
    """加载反 AI 检测写作指南。"""
    if not _ANTI_AI_GUIDE.exists():
        return ""
    with open(_ANTI_AI_GUIDE, encoding="utf-8") as f:
        content = f.read()
    # 提取核心规则（去掉冗长的示例）
    rules = []
    in_rule = False
    for line in content.split("\n"):
        if line.startswith("###") or line.startswith("####") or line.startswith("- "):
            rules.append(line)
            in_rule = True
        elif in_rule and line.startswith(">") :
            rules.append(line)
        elif in_rule and line.strip() == "":
            in_rule = False
    return "\n".join(rules[:50])  # 限制长度


def get_content_enhance_strategy(framework: str = "") -> str:
    """获取内容增强策略。"""
    if not _CONTENT_ENHANCE.exists():
        return ""
    with open(_CONTENT_ENHANCE, encoding="utf-8") as f:
        return f.read()


def get_reading_hooks() -> str:
    """获取阅读钩子指南。"""
    if not _READING_HOOKS.exists():
        return ""
    with open(_READING_HOOKS, encoding="utf-8") as f:
        return f.read()


def get_frameworks_guide() -> str:
    """获取框架选择指南。"""
    if not _FRAMEWORKS.exists():
        return ""
    with open(_FRAMEWORKS, encoding="utf-8") as f:
        return f.read()


def get_wechat_constraints() -> str:
    """获取微信公众号约束规则。"""
    if not _WECHAT_CONSTRAINTS.exists():
        return ""
    with open(_WECHAT_CONSTRAINTS, encoding="utf-8") as f:
        return f.read()


def build_system_prompt(
    style: str = "analytical",
    persona: str = "",
    framework: str = "",
    include_anti_ai: bool = True,
    include_hooks: bool = True,
) -> str:
    """构建完整的系统提示词，整合 Persona + 框架 + 反 AI 规则 + 阅读钩子。

    Args:
        style: 写作风格（兼容旧版，如果提供了 persona 则忽略）
        persona: Persona 名称（如 "luxun-style", "warm-editor" 等）
        framework: 框架类型
        include_anti_ai: 是否包含反 AI 检测规则
        include_hooks: 是否包含阅读钩子指南

    Returns:
        完整的系统提示词字符串
    """
    parts = []

    # 1. Persona（优先级最高）
    if persona:
        parts.append(get_persona_prompt(persona))
    elif style:
        # 兼容旧版：如果没有指定 persona，使用 style
        from mamacore.writer.style_prompts import STYLE_PROMPTS
        if style in STYLE_PROMPTS:
            parts.append(STYLE_PROMPTS[style])

    # 2. 框架
    if framework:
        from mamacore.writer.framework import get_framework_prompt
        fw_prompt = get_framework_prompt(framework)
        if fw_prompt:
            parts.append(fw_prompt)

    # 3. 反 AI 检测规则
    if include_anti_ai:
        anti_ai = get_anti_ai_rules()
        if anti_ai:
            parts.append("\n## 反 AI 检测写作规范\n" + anti_ai)

    # 4. 阅读钩子
    if include_hooks:
        hooks = get_reading_hooks()
        if hooks:
            parts.append("\n## 阅读钩子指南\n" + hooks)

    # 5. 微信约束
    wc = get_wechat_constraints()
    if wc:
        parts.append("\n## 微信公众号发布约束\n" + wc)

    return "\n".join(parts)
