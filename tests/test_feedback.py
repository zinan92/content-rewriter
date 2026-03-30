"""Tests for feedback recording."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from content_rewriter.cli import app

runner = CliRunner()


class TestFeedbackCommand:
    def test_record_reject(self, tmp_path: Path) -> None:
        feedback_dir = tmp_path / "config"
        result = runner.invoke(app, [
            "feedback", "reject",
            str(tmp_path / "draft.md"),
            "--content-id", "douyin_123",
            "--platform", "xiaohongshu",
            "--feedback-dir", str(feedback_dir),
        ])
        assert result.exit_code == 0
        log_file = feedback_dir / "feedback.jsonl"
        assert log_file.exists()
        entry = json.loads(log_file.read_text().strip())
        assert entry["action"] == "reject"
        assert entry["content_id"] == "douyin_123"

    def test_record_accept(self, tmp_path: Path) -> None:
        feedback_dir = tmp_path / "config"
        result = runner.invoke(app, [
            "feedback", "accept",
            str(tmp_path / "draft.md"),
            "--content-id", "douyin_123",
            "--platform", "xiaohongshu",
            "--feedback-dir", str(feedback_dir),
        ])
        assert result.exit_code == 0
        log_file = feedback_dir / "feedback.jsonl"
        entry = json.loads(log_file.read_text().strip())
        assert entry["action"] == "accept"
