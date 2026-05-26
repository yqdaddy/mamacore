"""Framework selector — returns prompt templates based on article framework type."""

from mamacore.writer.models import FrameworkType


FRAMEWORK_PROMPTS: dict[str, str] = {
    "checklist": """你是公众号清单型文章专家。
清单型文章的特点是结构清晰、信息密度高、读者容易消化。

文章结构：
1. 开头：用痛点或现象引入，说明为什么需要这份清单
2. 主体：5-10 个条目，每个条目包含：
   - 小标题（观点鲜明）
   - 具体说明（2-3 句话）
   - 案例或数据（支撑观点）
3. 结尾：总结清单核心价值，引导行动

写作要点：
- 条目之间要有逻辑递进或分类体系
- 不要简单罗列，每个条目都要有独特价值
- 标题要有冲击力，内容要有干货
""",
    "pain": """你是公众号痛点型文章专家。
痛点型文章的核心是戳中读者最在意的焦虑和困扰，然后给出解决方案。

文章结构：
1. 开头：描绘一个具体痛点场景，让读者产生"这就是我"的共鸣
2. 分析：为什么这个痛点存在（根因分析），打破常见认知误区
3. 方案：给出 2-3 个可执行的解决方案
4. 案例：真实案例或数据证明方案有效
5. 结尾：行动号召 + 金句收尾

写作要点：
- 痛点描述要具体到场景，不要抽象说教
- 分析要颠覆认知（"不是你想的那样"）
- 方案要有可执行的第一步
""",
    "compare": """你是公众号对比型文章专家。
对比型文章通过多维度对比帮助读者做出判断。

文章结构：
1. 开头：说明为什么需要对比（选型困境/信息混乱）
2. 对比维度：3-5 个关键维度（性能/价格/体验/生态/风险）
3. 逐项对比：每个维度详细分析 + 真实体感
4. 结论：不同场景下的最佳选择
5. 建议：读者如何根据自己的情况做选择

写作要点：
- 对比维度必须是读者真正关心的
- 要有明确的结论，不要和稀泥
- 加入真实使用体感，增加可信度
""",
    "narrative": """你是公众号叙事型文章专家。
叙事型文章通过讲故事传递观点，读者在故事中获得启发。

文章结构：
1. 开头：用一个引人入胜的场景或冲突开场
2. 展开：故事发展（遇到挑战 → 探索 → 转折 → 领悟）
3. 升华：从故事中提炼出核心观点
4. 延伸：将观点扩展为更广泛的启示
5. 结尾：回到开头场景，形成闭环

写作要点：
- 细节要真实可信，不要过度戏剧化
- 观点要从故事中自然浮现，不要生硬插入
- 结尾要有回甘，让读者思考
""",
}


def get_framework_prompt(framework: FrameworkType | str) -> str:
    """Return the system prompt for the given framework type."""
    key = framework.value if isinstance(framework, FrameworkType) else framework
    prompt = FRAMEWORK_PROMPTS.get(key)
    if prompt is None:
        raise ValueError(
            f"Unknown framework type: {key!r}. "
            f"Valid options: {', '.join(FRAMEWORK_PROMPTS)}"
        )
    return prompt


def get_framework_structure(framework: FrameworkType | str) -> list[str]:
    """Return a list of section names for the given framework."""
    structures: dict[str, list[str]] = {
        "checklist": ["开头引入", "主体条目", "结尾总结"],
        "pain": ["痛点场景", "根因分析", "解决方案", "案例证明", "行动号召"],
        "compare": ["选型困境", "对比维度", "逐项分析", "场景结论", "选择建议"],
        "narrative": ["场景开场", "故事展开", "观点升华", "延伸启示", "闭环结尾"],
    }
    key = framework.value if isinstance(framework, FrameworkType) else framework
    return structures.get(key, [])
