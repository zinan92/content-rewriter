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
    NO_WRITING_STYLE = "no_writing_style"


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
