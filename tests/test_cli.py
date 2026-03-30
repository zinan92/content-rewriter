"""Tests for the Typer CLI."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from content_rewriter.cli import app


runner = CliRunner()


class TestRewriteCommand:
    def test_help(self) -> None:
        result = runner.invoke(app, ["rewrite", "--help"])
        assert result.exit_code == 0
        assert "--from" in result.stdout
        assert "--to" in result.stdout

    def test_rejects_nonexistent_path(self) -> None:
        result = runner.invoke(app, ["rewrite", "--from", "douyin", "--to", "xiaohongshu", "/nonexistent/path"])
        assert result.exit_code != 0

    def test_rejects_missing_extractor_output(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["rewrite", "--from", "douyin", "--to", "xiaohongshu", str(tmp_path)])
        assert result.exit_code != 0

    @patch("content_rewriter.cli.LLMClient")
    @patch("content_rewriter.cli.rewrite_content")
    def test_success_writes_output(
        self,
        mock_rewrite: MagicMock,
        mock_llm_cls: MagicMock,
        douyin_extractor_output: dict,
        tmp_path: Path,
    ) -> None:
        from content_rewriter.models import RewriteResult, RewriteStatus

        content_dir = tmp_path / "douyin_123"
        content_dir.mkdir()
        (content_dir / "extractor_output.json").write_text(json.dumps(douyin_extractor_output))

        mock_rewrite.return_value = [
            RewriteResult(
                content_id="douyin_123",
                target_platform="xiaohongshu",
                title="测试标题",
                body="测试正文",
                hashtags=["标签1"],
                status=RewriteStatus.SUCCESS,
            )
        ]

        result = runner.invoke(app, [
            "rewrite", "--from", "douyin", "--to", "xiaohongshu",
            str(content_dir),
        ])
        assert result.exit_code == 0
        mock_rewrite.assert_called_once()
