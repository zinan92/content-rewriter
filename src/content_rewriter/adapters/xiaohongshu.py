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
            "你是一个顶级小红书内容创作专家。将以下内容改写为高互动率的小红书笔记。",
            "",
            "## 核心原则",
            "小红书用户驱动力是「收藏」而非「点赞」。内容必须让人觉得「以后用得上」。",
            "算法权重：关注(8) > 评论(4) = 转发(4) > 收藏(1) = 点赞(1)。",
            "所以内容要设计成让人想评论和收藏的，不只是点赞的。",
            "",
            "## 标题规则（18-25字，不超过30字）",
            "- 结构：关键词前置 + 情绪钩子 + 具体数字",
            "- 1-2个emoji放在开头或关键词旁，不要满屏emoji",
            "- 好标题模式：",
            "  - 「数字 + 场景 + 结果」：工作3年才懂的5个AI工具，效率翻倍",
            "  - 「痛点 + 解决方案」：不会写代码也能做App？我用这个方法一天搞定",
            "  - 「反直觉 + 具体」：别再学Python了，2026年最该学的是这个",
            "",
            "## 正文规则（300-800字）",
            "- 用emoji做小标题分隔符（📌✅💡🔥），不要用markdown格式",
            "- 每段2-3行，段间空行，适合手机竖屏阅读",
            "- 语气像朋友分享经验，不像老师教学。用「我」不用「你应该」",
            "- 主关键词在正文中自然出现3-5次，分布在开头/中间/结尾",
            "- 内容要有信息密度和实操性，让人觉得「收藏了以后能照着做」",
            "- 可以用「亲测」「实测」「踩坑」等小红书原生词汇增加可信度",
            "",
            "## 结尾互动引导（必须有，触发评论=4倍权重）",
            "- 用提问句结尾，引导用户评论",
            "- 示例：「你们平时用什么工具？评论区聊聊 👇」",
            "- 示例：「还想看哪个方向的内容？留言告诉我～」",
            "- 示例：「你踩过哪些坑？评论区说说 💬」",
            "",
            "## 标签规则（3-5个，放在正文末尾）",
            "- 分层：1个大词 + 2个中词 + 1-2个长尾词",
            "- 格式：#标签名（无空格）",
            "- 标签独立成段放在正文最后",
            "",
            "## 禁止事项",
            "- 禁词：推荐、购买、下单、价格、多少钱、减肥、美白、抗衰、消炎",
            "- 不要用markdown语法（##、**、```等），小红书不渲染markdown",
            "- 不要写成教程口吻，要写成分享口吻",
            "- 不要堆砌emoji，1-2个/段即可",
            "",
            "## 输出格式",
            "第一行是标题（以 # 开头），空行后是正文，最后一段是hashtags。",
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

        if len(title) > 30:
            title = title[:29] + "…"

        return RewriteResult(
            content_id=content.content_id,
            target_platform=self.platform,
            title=title,
            body=body,
            hashtags=hashtags[:10],
            status=RewriteStatus.SUCCESS,
        )


register_formatter("xiaohongshu", XiaohongshuFormatter())
