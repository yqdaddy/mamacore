import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from mamacore.server import mcp

def test_server_name():
    assert mcp.name == 'mamacore'

def test_tool_count():
    tools = mcp._tool_manager.list_tools()
    assert len(tools) >= 10

def test_prompt_count():
    prompts = mcp._prompt_manager.list_prompts()
    assert len(prompts) >= 3

def test_resource_count():
    resources = mcp._resource_manager.list_resources()
    assert len(resources) >= 3
