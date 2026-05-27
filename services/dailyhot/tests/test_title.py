"""标题评分测试。"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from mamacore.writer.title import score_title


def test_number_pattern():
    result = score_title('这5个AI工具你必须知道')
    assert result['patterns'] is not None
    assert result['score'] >= 0
    assert 'breakdown' in result


def test_breakdown_keys():
    result = score_title('测试')
    expected = {'数字', '悬念', '痛点', '情绪'}
    assert set(result['breakdown'].keys()) == expected


def test_suggestions_present():
    result = score_title('测试标题')
    assert isinstance(result['suggestions'], list)


def test_max_score_100():
    result = score_title('最震撼的10个AI真相！')
    assert result['score'] <= 100


def test_patterns_is_list():
    result = score_title('测试')
    assert isinstance(result['patterns'], list)


def test_high_score():
    result = score_title('关于AI Agent，这5个坑你千万别踩')
    assert result['score'] >= 30


def test_low_score():
    result = score_title('AI简介')
    assert result['score'] <= 25
