import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from mamacore.orchestrator.providers import get_provider, list_providers, ClaudeCodeProvider
from mamacore.orchestrator.task_manager import TaskManager
from mamacore.orchestrator.runner import get_project_root, get_workflow_prompt, get_mcp_config

def test_list_providers():
    providers = list_providers()
    assert len(providers) == 3

def test_get_claude():
    provider = get_provider('claude')
    assert isinstance(provider, ClaudeCodeProvider)

def test_claude_cmd():
    provider = get_provider('claude')
    cmd = provider.build_command('测试', {'mcpServers':{}}, '/tmp', {})
    assert cmd[0] == 'claude'
    assert '-p' in cmd

def test_invalid_provider():
    import pytest
    with pytest.raises(ValueError):
        get_provider('nonexistent')

def test_task_create():
    tm = TaskManager()
    t = tm.create('claude', '测试')
    assert t.status == 'running'
    tm.cleanup(t.id)

def test_task_kill():
    tm = TaskManager()
    assert tm.kill('nonexistent') is False

def test_project_root():
    root = get_project_root()
    assert Path(root).exists()

def test_workflow_prompt():
    prompt = get_workflow_prompt('测试任务', framework='checklist')
    assert '测试任务' in prompt
    assert 'checklist' in prompt

def test_mcp_config():
    config = get_mcp_config(get_project_root())
    assert 'mamacore' in config.get('mcpServers', {})
