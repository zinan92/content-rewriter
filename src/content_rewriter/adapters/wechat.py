"""WeChat Official Account formatter — produces article format."""

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
            "- 正文800-1500字，比口语更书面化，但不要太学术",
            "- 每个小节用 ## 标记小标题",
            "- 段落简短，适合手机阅读",
            "- 最后一行写'封面图建议：'加上封面图描述（900x500px）",
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
            hashtags=[],
            cover_brief=cover_brief,
            status=RewriteStatus.SUCCESS,
        )


register_formatter("wechat", WeChatFormatter())
