"""Tests for WeChatFormatter."""

from __future__ import annotations

import pytest

from content_rewriter.adapters import get_formatter, FORMATTERS, NormalizedContent
from content_rewriter.adapters.wechat import WeChatFormatter
from content_rewriter.models import EngagementMetrics, RewriteStatus


@pytest.fixture
def sample_content() -> NormalizedContent:
    return NormalizedContent(
        content_id="douyin_123",
        source_platform="douyin",
        title="为什么散户总在高点买入",
        core_text="大家好，今天来聊聊散户为什么总在高点买入...",
        key_points=["从众心理", "锚定效应", "损失厌恶"],
        engagement=EngagementMetrics(views=12500),
    )


class TestWeChatFormatter:
    def test_registered(self) -> None:
        assert "wechat" in FORMATTERS
        formatter = get_formatter("wechat")
        assert isinstance(formatter, WeChatFormatter)

    def test_format_prompt_returns_article_instructions(self, sample_content: NormalizedContent) -> None:
        formatter = WeChatFormatter()
        system, user = formatter.format_prompt(sample_content)
        assert "微信公众号" in system
        assert "13" in system
        assert sample_content.core_text in user

    def test_parse_output_extracts_sections(self, sample_content: NormalizedContent) -> None:
        formatter = WeChatFormatter()
        llm_output = """# 高点买入的心理陷阱

## 引言

你有没有发现，自己总是在最不该买的时候买入？

## 三个心理陷阱

### 从众心理
当身边所有人都在赚钱的时候，你很难忍住不进场。

### 锚定效应
你会不自觉地用过去的高点作为参考。

### 损失厌恶
股票跌了你不愿意卖，反而加仓。

## 总结

市场不会因为你的情绪而改变方向。做好计划，严格执行。

封面图建议：一个投资者看着下跌的K线图，表情焦虑"""
        result = formatter.parse_output(sample_content, llm_output)
        assert result.content_id == "douyin_123"
        assert result.target_platform == "wechat"
        assert result.status == RewriteStatus.SUCCESS
        assert result.cover_brief is not None
