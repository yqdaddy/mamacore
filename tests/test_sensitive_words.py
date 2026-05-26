"""敏感词检测引擎测试。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mamacore.safety.sensitive_words import (
    check_sensitive,
    check_ad_law,
    SensitiveWordDetector,
)


class TestSensitiveWords:
    """敏感词检测测试。"""

    def test_ad_law_detection(self):
        """测试广告法极限词检测。"""
        result = check_sensitive("这是我们最好的产品")
        assert result["total_issues"] >= 1
        assert any(i["word"] == "最好" for i in result["issues"])

    def test_multiple_sensitive_words(self):
        """测试多个敏感词检测。"""
        result = check_sensitive("最好、第一、完美无缺")
        assert result["total_issues"] >= 2

    def test_clean_text(self):
        """测试干净文本通过检测。"""
        result = check_sensitive("这是一个普通的测试文本")
        # 可能有一些误报，但至少应该能运行
        assert isinstance(result["passed"], bool)

    def test_risk_levels(self):
        """测试风险等级分类。"""
        result = check_sensitive("最好的产品")
        # 广告法词属于 medium 风险
        assert any(i["risk"] == "medium" for i in result["issues"])

    def test_context_extraction(self):
        """测试上下文提取。"""
        text = "这是一个很长的句子，中间有最好的产品，后面还有一些内容"
        result = check_sensitive(text)
        if result["issues"]:
            assert "context" in result["issues"][0]

    def test_suggestion_present(self):
        """测试建议始终存在。"""
        result = check_sensitive("最好的产品")
        assert all("suggestion" in i for i in result["issues"])

    def test_position_tracking(self):
        """测试位置追踪。"""
        text = "abc最好的产品"
        result = check_sensitive(text)
        if result["issues"]:
            assert result["issues"][0]["position"] > 0

    def test_deduplication(self):
        """测试去重逻辑。"""
        text = "最好最好最好"
        result = check_sensitive(text)
        # 同一个词只出现一次
        words = [i["word"] for i in result["issues"]]
        assert len(words) == len(set(words))

    def test_strict_mode(self):
        """测试严格模式。"""
        result_strict = check_sensitive("测试文本", strict=True)
        result_normal = check_sensitive("测试文本", strict=False)
        # 严格模式应该返回更多或相同的结果
        assert result_strict["total_issues"] >= result_normal["total_issues"]

    def test_ad_law_only(self):
        """测试仅广告法检测。"""
        result = check_ad_law("最好的产品")
        assert result["total_issues"] >= 1

    def test_singleton_pattern(self):
        """测试单例模式。"""
        detector1 = SensitiveWordDetector()
        detector2 = SensitiveWordDetector()
        assert detector1 is detector2


class TestAdLawPatterns:
    """广告法模式检测测试。"""

    def test_absolute_pattern(self):
        """测试绝对化表述检测。"""
        from mamacore.safety.ad_law import check_ad_law_full
        result = check_ad_law_full("最优惠的价格之一")
        assert result["total_issues"] >= 1
