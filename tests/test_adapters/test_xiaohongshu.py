"""Tests for XiaohongshuFormatter."""

from __future__ import annotations

import pytest

from content_rewriter.adapters import get_formatter, FORMATTERS, NormalizedContent
from content_rewriter.adapters.xiaohongshu import XiaohongshuFormatter
from content_rewriter.models import EngagementMetrics, RewriteStatus


@pytest.fixture
def sample_content() -> NormalizedContent:
    return NormalizedContent(
        content_id="douyin_123",
        source_platform="douyin",
        title="为什么散户总在高点买入？三个心理陷阱你必须知道",
        core_text="大家好，今天我们来聊一个很多人都会犯的错误...",
        key_points=["从众心理", "锚定效应", "损失厌恶"],
        engagement=EngagementMetrics(views=12500, likes=830),
    )


class TestXiaohongshuFormatter:
    def test_registered(self) -> None:
        assert "xiaohongshu" in FORMATTERS
        formatter = get_formatter("xiaohongshu")
        assert isinstance(formatter, XiaohongshuFormatter)

    def test_format_prompt_returns_system_and_user(self, sample_content: NormalizedContent) -> None:
        formatter = XiaohongshuFormatter()
        system, user = formatter.format_prompt(sample_content)
        assert "小红书" in system
        assert "20" in system
        assert "400" in system
        assert sample_content.core_text in user

    def test_format_prompt_includes_writing_style(self, sample_content: NormalizedContent) -> None:
        formatter = XiaohongshuFormatter()
        system, _ = formatter.format_prompt(sample_content, writing_style="说话直接，用短句")
        assert "说话直接" in system

    def test_parse_output_extracts_title_body_hashtags(self, sample_content: NormalizedContent) -> None:
        formatter = XiaohongshuFormatter()
        llm_output = """# 散户为啥总买在最高点？

你是不是也有这种经历？看到身边的人都在赚钱，忍不住就冲进去了，结果一买就跌。

这其实是三个心理陷阱在作怪：
1. 从众心理 — 别人赚钱你就急
2. 锚定效应 — 觉得还能更高
3. 损失厌恶 — 跌了不肯卖

解决方案很简单：入场前定好止损和目标，不要让情绪做决定。

#交易心理 #投资入门 #散户必看 #股票 #理财"""
        result = formatter.parse_output(sample_content, llm_output)
        assert result.content_id == "douyin_123"
        assert result.target_platform == "xiaohongshu"
        assert len(result.title) <= 20
        assert len(result.hashtags) >= 3
        assert result.status == RewriteStatus.SUCCESS
