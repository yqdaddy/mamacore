"""标题评分引擎测试。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mamacore.writer.title import score_title


class TestTitleScore:
    """标题评分测试。"""

    def test_number_pattern(self):
        """测试数字维度。"""
        result = score_title("这 5 个 AI 工具你必须要知道")
        assert result["breakdown"]["数字"] > 0
        assert "数字" in result["patterns"]

    def test_suspense_pattern(self):
        """测试悬念维度。"""
        result = score_title("AI 的真相到底是什么？")
        assert result["breakdown"]["悬念"] > 0
        assert "悬念" in result["patterns"] or "悬念词" in result["patterns"]

    def test_pain_pattern(self):
        """测试痛点维度。"""
        result = score_title("别再被 AI 工具坑了")
        assert result["breakdown"]["痛点"] > 0
        assert "痛点" in result["patterns"]

    def test_emotion_pattern(self):
        """测试情绪维度。"""
        result = score_title("我终于搞懂了 AI Agent")
        assert result["breakdown"]["情绪"] > 0

    def test_high_score_title(self):
        """测试高分标题（多维度组合）。"""
        result = score_title("关于 AI Agent，这 5 个坑你千万别踩")
        assert result["score"] >= 40  # 至少包含数字 + 痛点 + 情绪

    def test_low_score_title(self):
        """测试低分标题（缺乏吸引力元素）。"""
        result = score_title("AI 技术简介")
        assert result["score"] <= 25  # 纯描述性标题分数低

    def test_suggestions_present(self):
        """测试评分建议始终存在。"""
        result = score_title("测试标题")
        assert isinstance(result["suggestions"], list)
        assert len(result["suggestions"]) > 0

    def test_breakdown_keys(self):
        """测试评分维度键名正确。"""
        result = score_title("测试")
        expected_keys = {"数字", "悬念", "痛点", "情绪"}
        assert set(result["breakdown"].keys()) == expected_keys

    def test_max_score_100(self):
        """测试分数不超过 100。"""
        result = score_title("最震撼的 10 个 AI 真相！")
        assert result["score"] <= 100

    def test_patterns_is_list(self):
        """测试 patterns 是列表。"""
        result = score_title("测试")
        assert isinstance(result["patterns"], list)
