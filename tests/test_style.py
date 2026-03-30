"""Tests for writing style loading and extraction."""

from __future__ import annotations

from pathlib import Path

import pytest

from content_rewriter.style import load_writing_style, WRITING_STYLE_FILENAME


class TestLoadWritingStyle:
    def test_loads_existing_style(self, tmp_path: Path) -> None:
        style_path = tmp_path / WRITING_STYLE_FILENAME
        style_path.write_text("说话直接，用短句。喜欢用反问句开头。")
        result = load_writing_style(config_dir=tmp_path)
        assert result == "说话直接，用短句。喜欢用反问句开头。"

    def test_returns_none_when_missing(self, tmp_path: Path) -> None:
        result = load_writing_style(config_dir=tmp_path)
        assert result is None

    def test_returns_none_for_empty_file(self, tmp_path: Path) -> None:
        style_path = tmp_path / WRITING_STYLE_FILENAME
        style_path.write_text("")
        result = load_writing_style(config_dir=tmp_path)
        assert result is None
