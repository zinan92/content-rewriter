"""Tests for DouyinNormalizer."""

from __future__ import annotations

import pytest

from content_rewriter.adapters import get_normalizer, get_formatter, NORMALIZERS, FORMATTERS
from content_rewriter.adapters.douyin import DouyinNormalizer
from content_rewriter.models import ExtractorOutput


class TestDouyinNormalizer:
    def test_registered(self) -> None:
        assert "douyin" in NORMALIZERS
        normalizer = get_normalizer("douyin")
        assert isinstance(normalizer, DouyinNormalizer)

    def test_normalize_strips_video_framing(self, douyin_extractor_output: dict) -> None:
        source = ExtractorOutput.model_validate(douyin_extractor_output)
        normalizer = DouyinNormalizer()
        result = normalizer.normalize(source)
        assert result.content_id == source.content_id
        assert result.core_text == source.transcript
        assert result.key_points == source.key_points
        assert result.title == source.title
        assert result.engagement is not None
        assert result.engagement.views == 12500

    def test_normalize_handles_empty_key_points(self, douyin_extractor_output: dict) -> None:
        data = {**douyin_extractor_output, "key_points": []}
        source = ExtractorOutput.model_validate(data)
        normalizer = DouyinNormalizer()
        result = normalizer.normalize(source)
        assert result.key_points == []
