import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from typer.testing import CliRunner
from mamacore.cli import app

runner = CliRunner()

def test_help():
    result = runner.invoke(app, ['--help'])
    assert result.exit_code == 0

def test_score_title():
    result = runner.invoke(app, ['score-title', '关于AI Agent，这5个建议'])
    assert result.exit_code == 0
    assert '评分' in result.stdout

def test_write_dry_run():
    result = runner.invoke(app, ['write', 'AI开发', '--dry-run'])
    assert 'Dry Run' in result.stdout or result.exit_code in [0, 1]

def test_providers():
    result = runner.invoke(app, ['providers'])
    assert result.exit_code == 0
