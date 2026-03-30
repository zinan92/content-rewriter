"""Core rewrite orchestration: normalizer -> LLM -> formatter -> output."""

from __future__ import annotations

from content_rewriter.adapters import get_formatter, get_normalizer
from content_rewriter.llm import LLMClient, LLMError
from content_rewriter.models import ExtractorOutput, RewriteResult, RewriteStatus


def rewrite_content(
    source: ExtractorOutput,
    from_platform: str,
    to_platforms: list[str],
    llm_client: LLMClient,
    writing_style: str | None = None,
) -> list[RewriteResult]:
    """Rewrite source content for each target platform."""
    import content_rewriter.adapters.douyin  # noqa: F401
    import content_rewriter.adapters.xiaohongshu  # noqa: F401
    import content_rewriter.adapters.wechat  # noqa: F401

    normalizer = get_normalizer(from_platform)
    normalized = normalizer.normalize(source)

    results: list[RewriteResult] = []
    for target in to_platforms:
        formatter = get_formatter(target)
        system_prompt, user_message = formatter.format_prompt(normalized, writing_style)

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
