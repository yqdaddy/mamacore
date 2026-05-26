"""安全检测模块 —— 敏感词检测 + 广告法合规检查。"""

from .sensitive_words import SensitiveWordDetector, check_ad_law, check_sensitive
from .ad_law import check_ad_law_full


def register_tools(mcp) -> None:
    """向 MCP Server 注册本模块的所有 tools。"""

    @mcp.tool()
    async def mama_check_sensitive(
        text: str,
        strict: bool = False,
    ) -> str:
        """检测文章中的敏感词，包括广告法极限词、政治敏感词和平台特定敏感词。

        Args:
            text: 待检测的文章内容
            strict: 严格模式（包含低风险词，默认只返回中高风险）

        Returns:
            Markdown 格式的检测报告
        """
        result = check_sensitive(text, strict)

        lines = ["## 敏感词检测报告"]
        lines.append(f"\n**通过状态**: {'通过' if result['passed'] else '未通过'}")
        lines.append(f"\n**问题总数**: {result['total_issues']}")
        lines.append(f"  - 高风险: {result['high']}")
        lines.append(f"  - 中等风险: {result['medium']}")
        lines.append(f"  - 低风险: {result['low']}")

        if result["issues"]:
            lines.append("\n### 详细问题")
            for i, issue in enumerate(result["issues"], 1):
                risk_icon = {
                    "high": "高风险",
                    "medium": "中等风险",
                    "low": "低风险",
                }.get(issue["risk"], "未知")
                lines.append(
                    f"\n{i}. [{risk_icon}] **「{issue['word']}」** ({issue['risk']})"
                )
                lines.append(f"   位置: 第 {issue['position']} 字符")
                if issue.get("context"):
                    lines.append(f"   上下文: ...{issue['context']}...")
                lines.append(f"   建议: {issue['suggestion']}")
        else:
            lines.append("\n未发现敏感词，文章内容安全。")

        return "\n".join(lines)

    @mcp.tool()
    async def mama_check_ad_law(text: str) -> str:
        """专项检测广告法极限词。检测《中华人民共和国广告法》禁止使用的绝对化用语。

        Args:
            text: 待检测的文章内容
        """
        result = check_ad_law_full(text)

        lines = ["## 广告法极限词检测报告"]
        lines.append(
            f"\n**通过状态**: {'通过' if result['passed'] else '未通过'}"
        )
        lines.append(f"\n**问题数**: {result['total_issues']}")

        if result["issues"]:
            lines.append("\n### 违规词")
            for i, issue in enumerate(result["issues"], 1):
                lines.append(f"\n{i}. **「{issue['word']}」**")
                lines.append(f"   建议: {issue['suggestion']}")
                if issue.get("context"):
                    lines.append(f"   上下文: ...{issue['context']}...")
        else:
            lines.append("\n未发现广告法极限词。")

        return "\n".join(lines)
