import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from mamacore.safety.sensitive_words import check_sensitive, SensitiveWordDetector

def test_ad_law():
    result = check_sensitive('这是我们最好的产品')
    assert result['total_issues'] >= 1

def test_multiple_words():
    result = check_sensitive('最好、第一、完美无缺')
    assert result['total_issues'] >= 2

def test_singleton():
    d1 = SensitiveWordDetector()
    d2 = SensitiveWordDetector()
    assert d1 is d2

def test_dedup():
    result = check_sensitive('最好最好最好')
    words = [i['word'] for i in result['issues']]
    assert len(words) == len(set(words))

def test_risk_level():
    result = check_sensitive('最好的产品')
    assert any(i['risk'] in ('medium','high','low') for i in result['issues'])
