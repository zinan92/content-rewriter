"""Tests for voice profile loading and extraction."""

from __future__ import annotations

from pathlib import Path

import pytest

from content_rewriter.voice import load_voice_profile, VOICE_PROFILE_FILENAME


class TestLoadVoiceProfile:
    def test_loads_existing_profile(self, tmp_path: Path) -> None:
        profile_path = tmp_path / VOICE_PROFILE_FILENAME
        profile_path.write_text("说话直接，用短句。喜欢用反问句开头。")
        result = load_voice_profile(config_dir=tmp_path)
        assert result == "说话直接，用短句。喜欢用反问句开头。"

    def test_returns_none_when_missing(self, tmp_path: Path) -> None:
        result = load_voice_profile(config_dir=tmp_path)
        assert result is None

    def test_returns_none_for_empty_file(self, tmp_path: Path) -> None:
        profile_path = tmp_path / VOICE_PROFILE_FILENAME
        profile_path.write_text("")
        result = load_voice_profile(config_dir=tmp_path)
        assert result is None
