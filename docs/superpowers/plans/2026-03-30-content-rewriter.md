# content-rewriter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a CLI tool that transforms content-extractor output into platform-native drafts for Xiaohongshu and WeChat, with voice profile matching.

**Architecture:** Adapter pattern with Normalizer (source platform) and Formatter (target platform) interfaces. Claude API handles the LLM transformation. Voice profile is an optional system prompt extracted from best-performing content. CLI accepts `--from`/`--to` flags and a content directory path.

**Tech Stack:** Python 3.13+, Pydantic 2.x (frozen models), Typer (CLI), anthropic SDK (LLM), pytest + pytest-cov (testing)

**Design doc:** `~/.gstack/projects/wendy/wendy-main-design-20260330-125509.md`

**Sibling projects (patterns to follow):**
- `~/work/content-co/content-downloader/` — ContentItem model, pyproject.toml, adapter pattern
- `~/work/content-co/content-extractor/` — Typer CLI, CLI Proxy API token, src/ layout

---

### Task 1: Project Scaffold + pyproject.toml

**Files:**
- Create: `pyproject.toml`
- Create: `src/content_rewriter/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `.gitignore`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "content-rewriter"
version = "0.1.0"
description = "Bidirectional platform content transformer with voice profile matching"
requires-python = ">=3.13"
dependencies = [
    "typer>=0.24",
    "rich>=14.0",
    "pydantic>=2.0",
    "anthropic>=0.80",
    "orjson>=3.10",
]

[project.scripts]
content-rewriter = "content_rewriter.cli:app"

[tool.setuptools.packages.find]
where = ["src"]
include = ["content_rewriter*"]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "ruff>=0.9",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--cov=content_rewriter --cov-report=term-missing"

[tool.ruff]
target-version = "py313"
line-length = 100
```

- [ ] **Step 2: Create __init__.py**

```python
"""content-rewriter: Bidirectional platform content transformer."""

__version__ = "0.1.0"
```

- [ ] **Step 3: Create tests/__init__.py and conftest.py**

`tests/__init__.py` — empty file.

```python
# tests/conftest.py
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
```

- [ ] **Step 4: Create .gitignore**

```
__pycache__/
*.egg-info/
.venv/
dist/
build/
.coverage
htmlcov/
.pytest_cache/
.ruff_cache/
output/
```

- [ ] **Step 5: Create test fixture — douyin sample**

Create `tests/fixtures/douyin_sample/extractor_output.json`:

```json
{
  "content_id": "douyin_7456789012345",
  "source_platform": "douyin",
  "title": "为什么散户总在高点买入？三个心��陷阱你必须知道",
  "transcript": "大家好，今天我们来聊一个很多人都会犯的错误。为什么散户总是���最高点买入？第一个原因是从众心理，当你看到身边所有人都在赚钱的时候，你就会觉得自己也应该进场。第二个原因是锚定效应，你会把之前的高点作为参考，觉得现在的价格还能更高。第三个原因是损��厌恶，当股票下跌的时候，你不愿意卖出，反而会加仓，因为你不���承认自己的错误。那么怎么避免这些陷阱呢？最简单的方法就是制定一个交易计划，在入场���前就确定好你的止���位和目标位。记住，市场不会因为你的情绪而改变方向。",
  "key_points": [
    "散��高点买入的三个心理原因",
    "从众心理：看到别人赚钱就跟��",
    "锚定效应：用过去高点作为参考",
    "损失厌恶：下跌时不愿卖出反而加仓",
    "解决方案：制定交易计划，预设止损和目标"
  ],
  "visual_descriptions": [
    "frame 1: 主播��面镜头，背景是交易软件���面",
    "frame 2: 屏幕上显示一���上涨的K线图",
    "frame 3: 三个心理陷阱的文字标注叠加在画面上"
  ],
  "metadata": {
    "duration_seconds": 95,
    "publish_date": "2026-03-20",
    "engagement": {
      "views": 12500,
      "likes": 830,
      "comments": 67,
      "shares": 45,
      "collects": 120
    }
  }
}
```

- [ ] **Step 6: Create venv and install**

Run:
```bash
cd ~/work/content-co/content-rewriter
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```
Expected: installation succeeds, `content-rewriter --help` prints help text (will fail until cli.py exists)

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml src/ tests/ .gitignore
git commit -m "chore: project scaffold with pyproject.toml, fixtures, test infra"
```

---

### Task 2: Pydantic Models (models.py)

**Files:**
- Create: `src/content_rewriter/models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_models.py
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
            title="测试��题",
            body="测试正文内容，这是一篇��红书文章。",
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/work/content-co/content-rewriter && source .venv/bin/activate && pytest tests/test_models.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'content_rewriter.models'`

- [ ] **Step 3: Write models.py**

```python
# src/content_rewriter/models.py
"""Pydantic data models for content-rewriter input and output."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class EngagementMetrics(BaseModel):
    """Engagement metrics from the source platform."""

    model_config = {"frozen": True}

    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    collects: int = 0


class ContentMetadata(BaseModel):
    """Metadata about the source content."""

    model_config = {"frozen": True}

    duration_seconds: int | None = None
    publish_date: str | None = None
    engagement: EngagementMetrics = Field(default_factory=EngagementMetrics)


class ExtractorOutput(BaseModel):
    """Structured output from content-extractor. This is the rewriter's input."""

    model_config = {"frozen": True}

    content_id: str
    source_platform: str
    title: str
    transcript: str
    key_points: list[str] = Field(default_factory=list)
    visual_descriptions: list[str] = Field(default_factory=list)
    metadata: ContentMetadata = Field(default_factory=ContentMetadata)


class RewriteStatus(StrEnum):
    """Status of a rewrite operation."""

    SUCCESS = "success"
    FAILED = "failed"
    NO_VOICE_PROFILE = "no_voice_profile"


class RewriteResult(BaseModel):
    """Output of a rewrite operation for one target platform."""

    model_config = {"frozen": True}

    content_id: str
    target_platform: str
    title: str
    body: str
    hashtags: list[str] = Field(default_factory=list)
    cover_brief: str | None = None
    status: RewriteStatus = RewriteStatus.SUCCESS
    error_message: str | None = None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_models.py -v`
Expected: all 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/content_rewriter/models.py tests/test_models.py
git commit -m "feat: add Pydantic input/output models (ExtractorOutput, RewriteResult)"
```

---

### Task 3: LLM Client (llm.py)

**Files:**
- Create: `src/content_rewriter/llm.py`
- Create: `tests/test_llm.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_llm.py
"""Tests for Claude API client wrapper."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from content_rewriter.llm import (
    LLMClient,
    LLMError,
    load_cli_proxy_token,
)


class TestLoadCliProxyToken:
    def test_loads_token_from_file(self, tmp_path: Path) -> None:
        token_file = tmp_path / "claude-test.json"
        token_file.write_text(json.dumps({"access_token": "sk-test-123"}))
        token = load_cli_proxy_token(config_dir=tmp_path)
        assert token == "sk-test-123"

    def test_returns_none_when_no_files(self, tmp_path: Path) -> None:
        token = load_cli_proxy_token(config_dir=tmp_path)
        assert token is None

    def test_returns_none_when_missing_access_token(self, tmp_path: Path) -> None:
        token_file = tmp_path / "claude-bad.json"
        token_file.write_text(json.dumps({"other_key": "value"}))
        token = load_cli_proxy_token(config_dir=tmp_path)
        assert token is None


class TestLLMClient:
    def test_init_with_api_key(self) -> None:
        client = LLMClient(api_key="sk-direct-key")
        assert client.api_key == "sk-direct-key"

    def test_init_raises_without_credentials(self, tmp_path: Path) -> None:
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(LLMError, match="No Claude API credentials"):
                LLMClient(config_dir=tmp_path)

    def test_generate_calls_api(self) -> None:
        client = LLMClient(api_key="sk-test")
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Generated text")]
        with patch.object(client._client, "messages") as mock_messages:
            mock_messages.create.return_value = mock_response
            result = client.generate(
                system="You are a helper.",
                user_message="Hello",
            )
            assert result == "Generated text"
            mock_messages.create.assert_called_once()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_llm.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write llm.py**

```python
# src/content_rewriter/llm.py
"""Claude API client wrapper with CLI Proxy API support."""

from __future__ import annotations

import json
import os
from pathlib import Path

import anthropic


class LLMError(Exception):
    """Raised when LLM operations fail."""


DEFAULT_CONFIG_DIR = Path.home() / ".cli-proxy-api"
DEFAULT_MODEL = "claude-sonnet-4-6"


def load_cli_proxy_token(config_dir: Path = DEFAULT_CONFIG_DIR) -> str | None:
    """Load access token from CLI Proxy API config files."""
    if not config_dir.exists():
        return None
    for f in sorted(config_dir.glob("claude-*.json"), reverse=True):
        try:
            data = json.loads(f.read_text())
            token = data.get("access_token")
            if token:
                return token
        except (json.JSONDecodeError, OSError):
            continue
    return None


class LLMClient:
    """Wrapper around the Anthropic SDK with CLI Proxy API fallback."""

    def __init__(
        self,
        api_key: str | None = None,
        config_dir: Path = DEFAULT_CONFIG_DIR,
        model: str = DEFAULT_MODEL,
    ) -> None:
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY") or load_cli_proxy_token(config_dir)
        if not self.api_key:
            raise LLMError(
                "No Claude API credentials found. Set ANTHROPIC_API_KEY or "
                "ensure CLI Proxy API tokens exist in ~/.cli-proxy-api/"
            )
        self.model = model
        self._client = anthropic.Anthropic(api_key=self.api_key)

    def generate(
        self,
        system: str,
        user_message: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> str:
        """Generate a response from Claude."""
        try:
            response = self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user_message}],
                temperature=temperature,
            )
            return response.content[0].text
        except anthropic.APIError as e:
            raise LLMError(f"Claude API error: {e}") from e
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_llm.py -v`
Expected: all 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/content_rewriter/llm.py tests/test_llm.py
git commit -m "feat: add Claude API client with CLI Proxy API token support"
```

---

### Task 4: Adapter Base Classes + DouyinNormalizer

**Files:**
- Create: `src/content_rewriter/adapters/__init__.py`
- Create: `src/content_rewriter/adapters/douyin.py`
- Create: `tests/test_adapters/__init__.py`
- Create: `tests/test_adapters/test_douyin.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_adapters/test_douyin.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_adapters/test_douyin.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write adapters/__init__.py with base classes and registry**

```python
# src/content_rewriter/adapters/__init__.py
"""Platform adapter registry and base classes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from content_rewriter.models import EngagementMetrics, ExtractorOutput, RewriteResult


@dataclass(frozen=True)
class NormalizedContent:
    """Platform-agnostic intermediate representation."""

    content_id: str
    source_platform: str
    title: str
    core_text: str
    key_points: list[str] = field(default_factory=list)
    visual_context: list[str] = field(default_factory=list)
    engagement: EngagementMetrics | None = None


class Normalizer(ABC):
    """Strips platform-specific framing from source content."""

    @abstractmethod
    def normalize(self, source: ExtractorOutput) -> NormalizedContent: ...


class Formatter(ABC):
    """Produces a platform-native prompt for the target platform."""

    platform: str

    @abstractmethod
    def format_prompt(self, content: NormalizedContent, voice_profile: str | None = None) -> tuple[str, str]:
        """Return (system_prompt, user_message) for LLM generation."""
        ...

    @abstractmethod
    def parse_output(self, content: NormalizedContent, llm_output: str) -> RewriteResult:
        """Parse LLM output into a RewriteResult."""
        ...


NORMALIZERS: dict[str, Normalizer] = {}
FORMATTERS: dict[str, Formatter] = {}


def register_normalizer(platform: str, normalizer: Normalizer) -> None:
    NORMALIZERS[platform] = normalizer


def register_formatter(platform: str, formatter: Formatter) -> None:
    FORMATTERS[platform] = formatter


def get_normalizer(platform: str) -> Normalizer:
    if platform not in NORMALIZERS:
        raise ValueError(f"No normalizer for platform: {platform}. Available: {list(NORMALIZERS.keys())}")
    return NORMALIZERS[platform]


def get_formatter(platform: str) -> Formatter:
    if platform not in FORMATTERS:
        raise ValueError(f"No formatter for platform: {platform}. Available: {list(FORMATTERS.keys())}")
    return FORMATTERS[platform]
```

- [ ] **Step 4: Write adapters/douyin.py**

```python
# src/content_rewriter/adapters/douyin.py
"""Douyin (抖音) normalizer — strips video-specific framing."""

from __future__ import annotations

from content_rewriter.adapters import (
    NormalizedContent,
    Normalizer,
    register_normalizer,
)
from content_rewriter.models import ExtractorOutput


class DouyinNormalizer(Normalizer):
    """Normalizes Douyin video content into platform-agnostic form."""

    def normalize(self, source: ExtractorOutput) -> NormalizedContent:
        return NormalizedContent(
            content_id=source.content_id,
            source_platform=source.source_platform,
            title=source.title,
            core_text=source.transcript,
            key_points=list(source.key_points),
            visual_context=list(source.visual_descriptions),
            engagement=source.metadata.engagement,
        )


register_normalizer("douyin", DouyinNormalizer())
```

- [ ] **Step 5: Create tests/test_adapters/__init__.py**

Empty file.

- [ ] **Step 6: Run tests to verify they pass**

Run: `pytest tests/test_adapters/test_douyin.py -v`
Expected: all 3 tests PASS

- [ ] **Step 7: Commit**

```bash
git add src/content_rewriter/adapters/ tests/test_adapters/
git commit -m "feat: add adapter base classes, registry, and DouyinNormalizer"
```

---

### Task 5: XiaohongshuFormatter

**Files:**
- Create: `src/content_rewriter/adapters/xiaohongshu.py`
- Create: `tests/test_adapters/test_xiaohongshu.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_adapters/test_xiaohongshu.py
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
        assert "小��书" in system
        assert "20" in system  # title length constraint
        assert "400" in system  # body length guidance
        assert sample_content.core_text in user

    def test_format_prompt_includes_voice_profile(self, sample_content: NormalizedContent) -> None:
        formatter = XiaohongshuFormatter()
        system, _ = formatter.format_prompt(sample_content, voice_profile="说话直接，用短句")
        assert "说话直接" in system

    def test_parse_output_extracts_title_body_hashtags(self, sample_content: NormalizedContent) -> None:
        formatter = XiaohongshuFormatter()
        llm_output = """# ���户为啥总买在最高点？

你是不是也有这种经历？看到身边的人都在赚钱，忍不住就冲进去了，结果一买就跌。

这其实是三个心理陷阱在作怪：
1. 从众心理 — 别人赚钱你就急
2. 锚定效应 — 觉得还能更高
3. 损失厌恶 — 跌了不肯卖

解决方案很简单：入场前定好止损��目标，不要让情绪做决定。

#交易心理 #投资入门 #散户必看 #股票 #理财"""
        result = formatter.parse_output(sample_content, llm_output)
        assert result.content_id == "douyin_123"
        assert result.target_platform == "xiaohongshu"
        assert len(result.title) <= 20
        assert len(result.hashtags) >= 3
        assert result.status == RewriteStatus.SUCCESS
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_adapters/test_xiaohongshu.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write xiaohongshu.py**

```python
# src/content_rewriter/adapters/xiaohongshu.py
"""Xiaohongshu (小红书) formatter — produces native note format."""

from __future__ import annotations

import re

from content_rewriter.adapters import (
    Formatter,
    NormalizedContent,
    register_formatter,
)
from content_rewriter.models import RewriteResult, RewriteStatus


class XiaohongshuFormatter(Formatter):
    """Formats content as a Xiaohongshu note (图文笔记)."""

    platform = "xiaohongshu"

    def format_prompt(
        self, content: NormalizedContent, voice_profile: str | None = None
    ) -> tuple[str, str]:
        system_parts = [
            "你是一个小红书内容创作专家。将以下内容改写为小红书笔记格式。",
            "",
            "格式要求：",
            "- 标题：不超过20个字，要有吸引力，可以用emoji",
            "- 正文：400-600字，口语化，分段清晰",
            "- 用短���和段落，适合手机阅读",
            "- 结尾加5��相关话���标签，格式为 #标签",
            "- 输出格式：第一行是标题（以 # 开头），空行后是正文，最后一段是hashtags",
        ]
        if voice_profile:
            system_parts.extend(["", "写作风格要求：", voice_profile])

        key_points_text = "\n".join(f"- {p}" for p in content.key_points) if content.key_points else "无"

        user_message = (
            f"原始标题：{content.title}\n\n"
            f"原始内容：\n{content.core_text}\n\n"
            f"核���要点：\n{key_points_text}"
        )

        return "\n".join(system_parts), user_message

    def parse_output(self, content: NormalizedContent, llm_output: str) -> RewriteResult:
        lines = llm_output.strip().split("\n")

        # Extract title (first line starting with #)
        title = ""
        body_lines: list[str] = []
        hashtags: list[str] = []

        for line in lines:
            stripped = line.strip()
            if not title and stripped.startswith("#") and not stripped.startswith("##"):
                title = stripped.lstrip("# ").strip()
            elif stripped.startswith("#") and len(stripped) < 20 and not stripped.startswith("##"):
                # Likely a hashtag line
                found = re.findall(r"#(\S+)", stripped)
                hashtags.extend(found)
            else:
                # Check for inline hashtags in the last paragraph
                inline_tags = re.findall(r"#(\S+)", stripped)
                if inline_tags and not body_lines:
                    hashtags.extend(inline_tags)
                elif inline_tags and stripped == lines[-1].strip():
                    hashtags.extend(inline_tags)
                else:
                    body_lines.append(line)

        # If no hashtags found in structured way, extract from last few lines
        if not hashtags:
            for line in reversed(lines[-5:]):
                found = re.findall(r"#(\S+)", line)
                if found:
                    hashtags.extend(found)
                    if line in body_lines:
                        body_lines.remove(line)
                    break

        body = "\n".join(body_lines).strip()

        # Truncate title to 20 chars if needed
        if len(title) > 20:
            title = title[:19] + "…"

        return RewriteResult(
            content_id=content.content_id,
            target_platform=self.platform,
            title=title,
            body=body,
            hashtags=hashtags[:10],  # Cap at 10 hashtags
            status=RewriteStatus.SUCCESS,
        )


register_formatter("xiaohongshu", XiaohongshuFormatter())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_adapters/test_xiaohongshu.py -v`
Expected: all 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/content_rewriter/adapters/xiaohongshu.py tests/test_adapters/test_xiaohongshu.py
git commit -m "feat: add XiaohongshuFormatter with title/body/hashtag parsing"
```

---

### Task 6: WeChatFormatter

**Files:**
- Create: `src/content_rewriter/adapters/wechat.py`
- Create: `tests/test_adapters/test_wechat.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_adapters/test_wechat.py
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
        assert "13" in system  # title length constraint
        assert sample_content.core_text in user

    def test_parse_output_extracts_sections(self, sample_content: NormalizedContent) -> None:
        formatter = WeChatFormatter()
        llm_output = """# 高点买入的心理陷阱

## 引言

你有没有发现，自己总是在最不该买��时候买入？

## 三个心理陷阱

### 从众心理
当身边所有人都在赚钱的时候，你很难忍住不进场���

### 锚定效应
你会不自觉地用过去的高点作为参考。

### 损失厌恶
股票跌了你不愿意卖，反而加仓。

## 解决方案

制定交易计划，在入场之前��定止损位和目标位。

## 总结

市场不会因为你的情绪而改变方向。做好���划，严格执行。

封面图建议：一个投资者看着下跌的K线图，表情焦虑"""
        result = formatter.parse_output(sample_content, llm_output)
        assert result.content_id == "douyin_123"
        assert result.target_platform == "wechat"
        assert len(result.title) <= 13 or result.title == "高点买入的心理陷阱"
        assert result.status == RewriteStatus.SUCCESS
        assert result.cover_brief is not None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_adapters/test_wechat.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write wechat.py**

```python
# src/content_rewriter/adapters/wechat.py
"""WeChat Official Account (微信公众号) formatter — produces article format."""

from __future__ import annotations

import re

from content_rewriter.adapters import (
    Formatter,
    NormalizedContent,
    register_formatter,
)
from content_rewriter.models import RewriteResult, RewriteStatus


class WeChatFormatter(Formatter):
    """Formats content as a WeChat Official Account article."""

    platform = "wechat"

    def format_prompt(
        self, content: NormalizedContent, voice_profile: str | None = None
    ) -> tuple[str, str]:
        system_parts = [
            "你是一个微信公众号内容创作专家。将以下内容改写为公众号文章格式。",
            "",
            "格式要求：",
            "- 标题：不超过13个字，简洁有力",
            "- 文章结构：引言 → 正文（分小节，每节有小标题）→ 总结",
            "- 正��800-1500字，比口语更书面化，但不要太学术",
            "- 每个小节用 ## 标记小标题",
            "- 段落简短，适合手机阅读",
            "- 最后一行写'封面图建议：'加上封面图描���（900x500px）",
            "- 输出格式：第一行是标题（以 # 开头），后面是完整文章",
        ]
        if voice_profile:
            system_parts.extend(["", "写作风格要求：", voice_profile])

        key_points_text = "\n".join(f"- {p}" for p in content.key_points) if content.key_points else "无"

        user_message = (
            f"原始标题：{content.title}\n\n"
            f"原始内容：\n{content.core_text}\n\n"
            f"核心要点：\n{key_points_text}"
        )

        return "\n".join(system_parts), user_message

    def parse_output(self, content: NormalizedContent, llm_output: str) -> RewriteResult:
        lines = llm_output.strip().split("\n")

        title = ""
        body_lines: list[str] = []
        cover_brief: str | None = None

        for line in lines:
            stripped = line.strip()
            if not title and stripped.startswith("# ") and not stripped.startswith("## "):
                title = stripped.lstrip("# ").strip()
            elif stripped.startswith("封面图建议") or stripped.startswith("封面图："):
                cover_brief = stripped.split("：", 1)[-1].strip() if "：" in stripped else stripped.split(":", 1)[-1].strip()
            else:
                body_lines.append(line)

        body = "\n".join(body_lines).strip()

        if len(title) > 13:
            title = title[:12] + "…"

        return RewriteResult(
            content_id=content.content_id,
            target_platform=self.platform,
            title=title,
            body=body,
            hashtags=[],  # WeChat articles don't use hashtags
            cover_brief=cover_brief,
            status=RewriteStatus.SUCCESS,
        )


register_formatter("wechat", WeChatFormatter())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_adapters/test_wechat.py -v`
Expected: all 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/content_rewriter/adapters/wechat.py tests/test_adapters/test_wechat.py
git commit -m "feat: add WeChatFormatter with article structure and cover brief"
```

---

### Task 7: Voice Profile (voice.py)

**Files:**
- Create: `src/content_rewriter/voice.py`
- Create: `tests/test_voice.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_voice.py
"""Tests for voice profile loading and extraction."""

from __future__ import annotations

from pathlib import Path

import pytest

from content_rewriter.voice import load_voice_profile, VOICE_PROFILE_FILENAME


class TestLoadVoiceProfile:
    def test_loads_existing_profile(self, tmp_path: Path) -> None:
        profile_path = tmp_path / VOICE_PROFILE_FILENAME
        profile_path.write_text("��话直接，用短句。喜欢用反问句开头。")
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_voice.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write voice.py**

```python
# src/content_rewriter/voice.py
"""Voice profile loading and extraction."""

from __future__ import annotations

from pathlib import Path


DEFAULT_CONFIG_DIR = Path.home() / ".content-rewriter"
VOICE_PROFILE_FILENAME = "voice-profile.md"


def load_voice_profile(config_dir: Path = DEFAULT_CONFIG_DIR) -> str | None:
    """Load the voice profile from the config directory."""
    profile_path = config_dir / VOICE_PROFILE_FILENAME
    if not profile_path.exists():
        return None
    content = profile_path.read_text().strip()
    return content if content else None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_voice.py -v`
Expected: all 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/content_rewriter/voice.py tests/test_voice.py
git commit -m "feat: add voice profile loading from ~/.content-rewriter/"
```

---

### Task 8: Rewrite Engine (rewriter.py)

**Files:**
- Create: `src/content_rewriter/rewriter.py`
- Create: `tests/test_rewriter.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_rewriter.py
"""Tests for the core rewrite orchestration."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

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
            "#交易心理 #投资 #���户"
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

    def test_rewrite_with_voice_profile(self, douyin_extractor_output: dict) -> None:
        source = ExtractorOutput.model_validate(douyin_extractor_output)
        mock_client = MagicMock()
        mock_client.generate.return_value = "# 标题\n\n正文\n\n#标签"
        rewrite_content(
            source=source,
            from_platform="douyin",
            to_platforms=["xiaohongshu"],
            llm_client=mock_client,
            voice_profile="说话直接",
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_rewriter.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write rewriter.py**

```python
# src/content_rewriter/rewriter.py
"""Core rewrite orchestration: normalizer -> LLM -> formatter -> output."""

from __future__ import annotations

import sys

from content_rewriter.adapters import get_formatter, get_normalizer
from content_rewriter.llm import LLMClient, LLMError
from content_rewriter.models import ExtractorOutput, RewriteResult, RewriteStatus


def rewrite_content(
    source: ExtractorOutput,
    from_platform: str,
    to_platforms: list[str],
    llm_client: LLMClient,
    voice_profile: str | None = None,
) -> list[RewriteResult]:
    """Rewrite source content for each target platform."""
    # Import adapters to trigger registration
    import content_rewriter.adapters.douyin  # noqa: F401
    import content_rewriter.adapters.xiaohongshu  # noqa: F401
    import content_rewriter.adapters.wechat  # noqa: F401

    normalizer = get_normalizer(from_platform)
    normalized = normalizer.normalize(source)

    results: list[RewriteResult] = []
    for target in to_platforms:
        formatter = get_formatter(target)
        system_prompt, user_message = formatter.format_prompt(normalized, voice_profile)

        try:
            llm_output = llm_client.generate(system=system_prompt, user_message=user_message)
            result = formatter.parse_output(normalized, llm_output)
            results.append(result)
        except LLMError as e:
            results.append(
                RewriteResult(
                    content_id=source.content_id,
                    target_platform=target,
                    title="",
                    body=source.transcript,
                    status=RewriteStatus.FAILED,
                    error_message=str(e),
                )
            )

    return results
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_rewriter.py -v`
Expected: all 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/content_rewriter/rewriter.py tests/test_rewriter.py
git commit -m "feat: add rewrite engine with normalizer -> LLM -> formatter pipeline"
```

---

### Task 9: CLI (cli.py)

**Files:**
- Create: `src/content_rewriter/cli.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_cli.py
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
        assert "not found" in result.stdout.lower() or "not found" in (result.stderr or "").lower()

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

        # Set up fixture directory
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_cli.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write cli.py**

```python
# src/content_rewriter/cli.py
"""Typer CLI entry point for content-rewriter."""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import typer
from rich.console import Console

from content_rewriter.llm import LLMClient, LLMError
from content_rewriter.models import ExtractorOutput, RewriteStatus
from content_rewriter.rewriter import rewrite_content
from content_rewriter.voice import load_voice_profile

app = typer.Typer(help="Bidirectional platform content transformer.")
console = Console()


@app.command("rewrite")
def rewrite_command(
    content_path: Path = typer.Argument(..., help="Path to content directory with extractor_output.json"),
    from_platform: str = typer.Option(..., "--from", "-f", help="Source platform (e.g. douyin)"),
    to_platforms: str = typer.Option(..., "--to", "-t", help="Target platform(s), comma-separated (e.g. xiaohongshu,wechat)"),
    output_dir: Path = typer.Option(Path("output"), "--output-dir", "-o", help="Output directory for drafts"),
    voice_config_dir: Path = typer.Option(Path.home() / ".content-rewriter", "--voice-dir", help="Voice profile directory"),
) -> None:
    """Rewrite extracted content for target platform(s)."""
    # Validate input
    if not content_path.exists():
        console.print(f"[red]Error: Content path not found: {content_path}[/red]")
        raise typer.Exit(code=1)

    extractor_file = content_path / "extractor_output.json"
    if not extractor_file.exists():
        console.print(f"[red]Error: extractor_output.json not found in {content_path}[/red]")
        raise typer.Exit(code=1)

    # Load input
    try:
        raw = json.loads(extractor_file.read_text())
        source = ExtractorOutput.model_validate(raw)
    except Exception as e:
        console.print(f"[red]Error: Invalid extractor output: {e}[/red]")
        raise typer.Exit(code=1)

    # Load voice profile
    voice_profile = load_voice_profile(config_dir=voice_config_dir)
    if voice_profile is None:
        console.print("[yellow]Warning: No voice profile found. Output will use generic style.[/yellow]")
        console.print(f"[dim]Create {voice_config_dir / 'voice-profile.md'} or run --extract-voice[/dim]")

    # Initialize LLM client
    try:
        llm_client = LLMClient()
    except LLMError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)

    # Parse targets
    targets = [t.strip() for t in to_platforms.split(",")]

    # Rewrite
    console.print(f"[bold]Rewriting {source.content_id} from {from_platform} to {', '.join(targets)}...[/bold]")
    results = rewrite_content(
        source=source,
        from_platform=from_platform,
        to_platforms=targets,
        llm_client=llm_client,
        voice_profile=voice_profile,
    )

    # Write outputs
    today = date.today().isoformat()
    for result in results:
        draft_dir = output_dir / source.content_id
        draft_dir.mkdir(parents=True, exist_ok=True)
        draft_file = draft_dir / f"{result.target_platform}_draft.md"

        if result.status == RewriteStatus.FAILED:
            content = f"[REWRITE_FAILED]\n\nError: {result.error_message}\n\n---\n\nRaw transcript:\n{result.body}"
        elif voice_profile is None:
            content = f"[NO_VOICE_PROFILE]\n\n# {result.title}\n\n{result.body}"
            if result.hashtags:
                content += "\n\n" + " ".join(f"#{tag}" for tag in result.hashtags)
        else:
            content = f"# {result.title}\n\n{result.body}"
            if result.hashtags:
                content += "\n\n" + " ".join(f"#{tag}" for tag in result.hashtags)

        if result.cover_brief:
            content += f"\n\n---\n封面图建议: {result.cover_brief}"

        draft_file.write_text(content)
        status_icon = "✓" if result.status == RewriteStatus.SUCCESS else "✗"
        console.print(f"  {status_icon} {result.target_platform} → {draft_file}")

    failed = sum(1 for r in results if r.status == RewriteStatus.FAILED)
    if failed:
        console.print(f"\n[yellow]{failed}/{len(results)} rewrites failed[/yellow]")
        raise typer.Exit(code=1)
    else:
        console.print(f"\n[green]Done! {len(results)} draft(s) written.[/green]")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_cli.py -v`
Expected: all 4 tests PASS

- [ ] **Step 5: Run full test suite**

Run: `pytest -v`
Expected: all tests PASS, coverage report printed

- [ ] **Step 6: Commit**

```bash
git add src/content_rewriter/cli.py tests/test_cli.py
git commit -m "feat: add Typer CLI with rewrite command, output writing, error handling"
```

---

### Task 10: Feedback Loop

**Files:**
- Modify: `src/content_rewriter/cli.py`
- Create: `tests/test_feedback.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_feedback.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_feedback.py -v`
Expected: FAIL

- [ ] **Step 3: Add feedback command to cli.py**

Add to `src/content_rewriter/cli.py`:

```python
@app.command("feedback")
def feedback_command(
    action: str = typer.Argument(..., help="Action: accept or reject"),
    draft_path: Path = typer.Argument(..., help="Path to the draft file"),
    content_id: str = typer.Option(..., "--content-id", help="Content ID"),
    platform: str = typer.Option(..., "--platform", help="Target platform"),
    feedback_dir: Path = typer.Option(
        Path.home() / ".content-rewriter", "--feedback-dir", help="Feedback log directory"
    ),
) -> None:
    """Record feedback (accept/reject) for a rewrite draft."""
    if action not in ("accept", "reject"):
        console.print(f"[red]Error: action must be 'accept' or 'reject', got '{action}'[/red]")
        raise typer.Exit(code=1)

    feedback_dir.mkdir(parents=True, exist_ok=True)
    log_file = feedback_dir / "feedback.jsonl"

    from datetime import datetime

    entry = {
        "draft_path": str(draft_path),
        "platform": platform,
        "content_id": content_id,
        "timestamp": datetime.now().isoformat(),
        "action": action,
    }

    with log_file.open("a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    icon = "✓" if action == "accept" else "✗"
    console.print(f"  {icon} Recorded {action} for {content_id} ({platform})")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_feedback.py -v`
Expected: all 2 tests PASS

- [ ] **Step 5: Run full test suite**

Run: `pytest -v`
Expected: all tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/content_rewriter/cli.py tests/test_feedback.py
git commit -m "feat: add feedback command for accept/reject tracking"
```

---

## Self-Review Checklist

| Requirement | Task | Covered |
|------------|------|---------|
| FOUND-01: ExtractorOutput model | Task 2 | Yes |
| FOUND-02: RewriteResult model | Task 2 | Yes |
| FOUND-03: Claude API client | Task 3 | Yes |
| FOUND-04: Typer CLI rewrite command | Task 9 | Yes |
| FOUND-05: Input JSON validation | Task 9 (cli.py) | Yes |
| FOUND-06: Output to output/<id>/<platform>_draft.md | Task 9 | Yes |
| FOUND-07: pyproject.toml | Task 1 | Yes |
| ADPT-01: Normalizer base class | Task 4 | Yes |
| ADPT-02: Formatter base class | Task 4 | Yes |
| ADPT-03: DouyinNormalizer | Task 4 | Yes |
| ADPT-04: XiaohongshuFormatter | Task 5 | Yes |
| ADPT-05: WeChatFormatter | Task 6 | Yes |
| ADPT-06: Router | Task 4 (registry) | Yes |
| VOICE-01: Voice profile file | Task 7 | Yes |
| VOICE-03: Graceful degradation | Task 9 (cli.py) | Yes |
| VOICE-04: Rewrite orchestration | Task 8 | Yes |
| VOICE-05: Retry/fallback on API failure | Task 8 | Yes |
| FDBK-01: --feedback command | Task 10 | Yes |
| FDBK-02: JSONL format | Task 10 | Yes |

**Not covered (deferred):**
- VOICE-02: `--extract-voice` command (requires real content examples, deferred to manual prerequisite)
- FDBK-03: Batch rewrite (simple loop extension, defer)
- FDBK-04: Accept rate tracking (read feedback.jsonl, simple stats, defer)
