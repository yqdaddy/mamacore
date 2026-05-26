"""MCP Server 注册测试。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mamacore.server import mcp


class TestMCPServerRegistration:
    """MCP Server 注册测试。"""

    def test_server_name(self):
        """测试服务器名称。"""
        assert mcp.name == "mamacore"

    def test_server_instructions(self):
        """测试服务器指令存在。"""
        assert mcp.instructions is not None
        assert len(mcp.instructions) > 50

    def test_tool_count(self):
        """测试工具数量至少 20 个。"""
        tools = mcp._tool_manager.list_tools()
        assert len(tools) >= 20, f"期望至少 20 个工具，实际 {len(tools)} 个"

    def test_expected_tools_exist(self):
        """测试关键工具已注册。"""
        tool_names = [t.name for t in mcp._tool_manager.list_tools()]
        expected = [
            "mama_health_check",
            "mama_hot_topics",
            "mama_write_article",
            "mama_generate_outline",
            "mama_score_title",
            "mama_format_article",
            "mama_check_sensitive",
            "mama_publish_draft",
            "mama_analyze_account",
            "mama_content_strategy",
        ]
        for name in expected:
            assert name in tool_names, f"缺少工具: {name}"

    def test_tool_descriptions(self):
        """测试工具描述不为空。"""
        for tool in mcp._tool_manager.list_tools():
            assert tool.description, f"工具 {tool.name} 缺少描述"
            assert len(tool.description) > 10, f"工具 {tool.name} 描述太短"

    def test_prompt_count(self):
        """测试 prompt 数量至少 3 个。"""
        prompts = mcp._prompt_manager.list_prompts()
        assert len(prompts) >= 3

    def test_prompt_titles(self):
        """测试 prompt 标题正确。"""
        titles = [p.title for p in mcp._prompt_manager.list_prompts()]
        expected_titles = [
            "公众号文章全流程工作流",
            "数据分析与内容策略工作流",
            "图片生成工作流",
        ]
        for title in expected_titles:
            assert title in titles, f"缺少 prompt: {title}"

    def test_resource_count(self):
        """测试 resource 数量至少 3 个。"""
        resources = mcp._resource_manager.list_resources()
        assert len(resources) >= 3

    def test_health_check_tool(self):
        """测试健康检查工具可调用。"""
        import asyncio
        async def _test():
            result = await mama_health_check()
            assert "M.A.M.A. Core" in result
            assert "模块状态" in result
        from mamacore.server import mama_health_check
        asyncio.run(_test())


class TestMCPProtocol:
    """MCP 协议测试。"""

    def test_stdio_entry_point(self):
        """测试 stdio 入口存在。"""
        from mamacore.server import main
        assert callable(main)

    def test_tool_schema_generation(self):
        """测试工具 schema 自动生成。"""
        for tool in mcp._tool_manager.list_tools():
            # FastMCP 自动从 docstring 生成 description
            assert tool.description
            # 工具名应该是 snake_case
            assert tool.name == tool.name.lower()
            assert " " not in tool.name
