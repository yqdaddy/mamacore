"""LLM 客户端测试。"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mamacore.llm.client import (
    get_openai_client,
    llm_generate,
    estimate_cost,
    MODEL_COST,
)


class TestLLMClient:
    """LLM 客户端测试。"""

    def test_no_api_key_returns_none(self):
        """测试无 API Key 时返回 None。"""
        # 确保没有 API Key
        orig_openai = os.environ.get("OPENAI_API_KEY")
        orig_anthropic = os.environ.get("ANTHROPIC_API_KEY")
        try:
            os.environ.pop("OPENAI_API_KEY", None)
            os.environ.pop("ANTHROPIC_API_KEY", None)
            client = get_openai_client()
            assert client is None
        finally:
            if orig_openai:
                os.environ["OPENAI_API_KEY"] = orig_openai
            if orig_anthropic:
                os.environ["ANTHROPIC_API_KEY"] = orig_anthropic

    def test_llm_generate_no_api_key(self):
        """测试无 API Key 时 llm_generate 返回空字符串。"""
        import asyncio
        orig_openai = os.environ.get("OPENAI_API_KEY")
        orig_anthropic = os.environ.get("ANTHROPIC_API_KEY")
        try:
            os.environ.pop("OPENAI_API_KEY", None)
            os.environ.pop("ANTHROPIC_API_KEY", None)
            result = asyncio.run(llm_generate("test prompt"))
            assert result == ""
        finally:
            if orig_openai:
                os.environ["OPENAI_API_KEY"] = orig_openai
            if orig_anthropic:
                os.environ["ANTHROPIC_API_KEY"] = orig_anthropic


class TestCostEstimation:
    """成本估算测试。"""

    def test_chinese_token_count(self):
        """测试中文 token 估算。"""
        text = "这是一篇测试文章"
        result = estimate_cost(text)
        assert result["tokens"] > 0

    def test_cost_positive(self):
        """测试成本为正数。"""
        text = "这是一篇测试文章"
        result = estimate_cost(text)
        assert result["cost_usd"] > 0

    def test_cost_model_gpt4o(self):
        """测试 GPT-4o 模型成本。"""
        text = "test content"
        result = estimate_cost(text, model="gpt-4o")
        assert result["model"] == "gpt-4o"
        assert "cost_usd" in result
        assert "tokens" in result

    def test_model_cost_dict_complete(self):
        """测试模型成本字典包含所有预期模型。"""
        # MODEL_COST 键格式为 model:input 或 model:output
        keys = list(MODEL_COST.keys())
        assert any("gpt-4o" in k for k in keys)
        assert any("gpt-4o-mini" in k for k in keys)
