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
