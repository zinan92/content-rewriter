"""Tests for Pydantic data models."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from content_rewriter.models import (
    EngagementMetrics,
    ExtractorOutput,
    ContentMetadata,
    RewriteResult,
    RewriteStatus,
)


class TestExtractorOutput:
    def test_loads_from_fixture(self, douyin_extractor_output: dict) -> None:
        result = ExtractorOutput.model_validate(douyin_extractor_output)
        assert result.content_id == "douyin_7456789012345"
        assert result.source_platform == "douyin"
        assert len(result.key_points) == 5
        assert result.metadata.duration_seconds == 95
        assert result.metadata.engagement.views == 12500

    def test_frozen(self, douyin_extractor_output: dict) -> None:
        result = ExtractorOutput.model_validate(douyin_extractor_output)
        with pytest.raises(ValidationError):
            result.title = "new title"

    def test_rejects_missing_required_fields(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ExtractorOutput.model_validate({"content_id": "test"})
        errors = exc_info.value.errors()
        missing_fields = {e["loc"][0] for e in errors if e["type"] == "missing"}
        assert "source_platform" in missing_fields
        assert "transcript" in missing_fields

    def test_empty_optional_fields(self, douyin_extractor_output: dict) -> None:
        data = {**douyin_extractor_output, "key_points": [], "visual_descriptions": []}
        result = ExtractorOutput.model_validate(data)
        assert result.key_points == []
        assert result.visual_descriptions == []


class TestRewriteResult:
    def test_creates_valid_result(self) -> None:
        result = RewriteResult(
            content_id="douyin_123",
            target_platform="xiaohongshu",
            title="测试标题",
            body="测试正文内容，这是一篇小红书文章。",
            hashtags=["交易", "投资", "心理学"],
            status=RewriteStatus.SUCCESS,
        )
        assert result.target_platform == "xiaohongshu"
        assert len(result.hashtags) == 3
        assert result.status == RewriteStatus.SUCCESS

    def test_frozen(self) -> None:
        result = RewriteResult(
            content_id="test",
            target_platform="wechat",
            title="t",
            body="b",
            hashtags=[],
            status=RewriteStatus.SUCCESS,
        )
        with pytest.raises(ValidationError):
            result.title = "changed"
