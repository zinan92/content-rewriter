"""Shared test fixtures for content-rewriter."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture
def douyin_sample_dir(fixtures_dir: Path) -> Path:
    return fixtures_dir / "douyin_sample"


@pytest.fixture
def douyin_extractor_output(douyin_sample_dir: Path) -> dict:
    return json.loads((douyin_sample_dir / "extractor_output.json").read_text())
