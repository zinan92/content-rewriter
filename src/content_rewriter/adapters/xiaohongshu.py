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
    """Formats content as a Xiaohongshu note."""

    platform = "xiaohongshu"

    def format_prompt(
        self, content: NormalizedContent, writing_style: str | None = None
    ) -> tuple[str, str]:
        system_parts = [
            "你是一个小红书内容创作专家。将以下内容改写为小红书笔记格式。",
            "",
            "格式要求：",
            "- 标题：不超过20个字，要有吸引力，可以用emoji",
            "- 正文：400-600字，口语化，分段清晰",
            "- 用短句和段落，适合手机阅读",
            "- 结尾加5个相关话题标签，格式为 #标签",
            "- 输出格式：第一行是标题（以 # 开头），空行后是正文，最后一段是hashtags",
        ]
        if writing_style:
            system_parts.extend(["", "写作风格要求：", writing_style])

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
        hashtags: list[str] = []

        for line in lines:
            stripped = line.strip()
            if not title and stripped.startswith("#") and not stripped.startswith("##"):
                title = stripped.lstrip("# ").strip()
            elif stripped.startswith("#") and len(stripped) < 20 and not stripped.startswith("##"):
                found = re.findall(r"#(\S+)", stripped)
                hashtags.extend(found)
            else:
                inline_tags = re.findall(r"#(\S+)", stripped)
                if inline_tags and not body_lines:
                    hashtags.extend(inline_tags)
                elif inline_tags and stripped == lines[-1].strip():
                    hashtags.extend(inline_tags)
                else:
                    body_lines.append(line)

        if not hashtags:
            for line in reversed(lines[-5:]):
                found = re.findall(r"#(\S+)", line)
                if found:
                    hashtags.extend(found)
                    if line in body_lines:
                        body_lines.remove(line)
                    break

        body = "\n".join(body_lines).strip()

        if len(title) > 20:
            title = title[:19] + "…"

        return RewriteResult(
            content_id=content.content_id,
            target_platform=self.platform,
            title=title,
            body=body,
            hashtags=hashtags[:10],
            status=RewriteStatus.SUCCESS,
        )


register_formatter("xiaohongshu", XiaohongshuFormatter())
