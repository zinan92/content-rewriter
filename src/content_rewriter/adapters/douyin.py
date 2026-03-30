"""Douyin normalizer — strips video-specific framing."""

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
