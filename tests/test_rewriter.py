"""Tests for the core rewrite orchestration."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from content_rewriter.models import ExtractorOutput, RewriteResult, RewriteStatus
from content_rewriter.rewriter import rewrite_content


class TestRewriteContent:
    def test_rewrite_single_target(self, douyin_extractor_output: dict) -> None:
        source = ExtractorOutput.model_validate(douyin_extractor_output)
        mock_client = MagicMock()
        mock_client.generate.return_value = (
            "# 散户为啥总买在最高点？\n\n"
            "你是不是也有这种经历？\n\n"
            "#交易心理 #投资 #散户"
        )
        results = rewrite_content(
            source=source,
            from_platform="douyin",
            to_platforms=["xiaohongshu"],
            llm_client=mock_client,
        )
        assert len(results) == 1
        assert results[0].target_platform == "xiaohongshu"
        assert results[0].status == RewriteStatus.SUCCESS
        mock_client.generate.assert_called_once()

    def test_rewrite_multiple_targets(self, douyin_extractor_output: dict) -> None:
        source = ExtractorOutput.model_validate(douyin_extractor_output)
        mock_client = MagicMock()
        mock_client.generate.side_effect = [
            "# 散户心理\n\n正文\n\n#标签1 #标签2 #标签3",
            "# 散户心理陷阱\n\n## 引言\n\n正文\n\n封面图建议：K线图",
        ]
        results = rewrite_content(
            source=source,
            from_platform="douyin",
            to_platforms=["xiaohongshu", "wechat"],
            llm_client=mock_client,
        )
        assert len(results) == 2
        assert results[0].target_platform == "xiaohongshu"
        assert results[1].target_platform == "wechat"

    def test_rewrite_with_writing_style(self, douyin_extractor_output: dict) -> None:
        source = ExtractorOutput.model_validate(douyin_extractor_output)
        mock_client = MagicMock()
        mock_client.generate.return_value = "# 标题\n\n正文\n\n#标签"
        rewrite_content(
            source=source,
            from_platform="douyin",
            to_platforms=["xiaohongshu"],
            llm_client=mock_client,
            writing_style="说话直接",
        )
        call_args = mock_client.generate.call_args
        assert "说话直接" in call_args.kwargs["system"]

    def test_rewrite_returns_failed_on_llm_error(self, douyin_extractor_output: dict) -> None:
        source = ExtractorOutput.model_validate(douyin_extractor_output)
        mock_client = MagicMock()
        from content_rewriter.llm import LLMError
        mock_client.generate.side_effect = LLMError("API down")
        results = rewrite_content(
            source=source,
            from_platform="douyin",
            to_platforms=["xiaohongshu"],
            llm_client=mock_client,
        )
        assert len(results) == 1
        assert results[0].status == RewriteStatus.FAILED
        assert "API down" in (results[0].error_message or "")
