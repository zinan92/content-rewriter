"""Xiaohongshu (小红书) formatter — produces native note format.

Prompt rules sourced from:
- 小红书星云5.0算法 CES 互动评分体系
- 小红书官方内容规范 & 限流规则汇总
- 爆款笔记拆解（2025-2026 高互动率模式）
"""

from __future__ import annotations

import re

from content_rewriter.adapters import (
    Formatter,
    NormalizedContent,
    register_formatter,
)
from content_rewriter.models import RewriteResult, RewriteStatus

# --- Prompt building blocks (kept as module-level constants for testability) ---

_SYSTEM_CORE = """\
你是一个顶级小红书内容创作专家。将以下内容改写为高互动率的小红书笔记。

## 算法核心（星云5.0 CES评分）
CES = 关注×8 + 评论×4 + 转发×4 + 点赞×1 + 收藏×1
- 高质量评论（≥8字+场景描述）权重是普通评论的3倍
- 发布后2小时内作者回复评论 → 进入推荐瀑布概率+30%
- 65%的持续流量来自搜索 → 关键词布局决定长尾生命力
- 内容必须让用户觉得「以后用得上」（驱动收藏）和「我也想说两句」（驱动评论）"""

_TITLE_RULES = """\
## 标题规则
- 总长度18-25字（显示截断约20字），绝不超过30字
- 前18字必须包含2个核心关键词（搜索权重集中在标题前半段）
- 结构公式（任选一）：
  「数字+场景+结果」 工作3年才懂的5个AI工具，效率翻倍
  「人群+痛点+方案」 学生党必备！5招告别低效学习
  「反直觉+具体」   别再学Python了，2026年最该学的是这个
  「痛点+方法+保证」 告别黑眼圈！三天见效，亲测有效
- 1-2个emoji放在开头或关键词旁（推荐：✨🔥💡📌🎯）
- 禁止绝对化用语（最佳/第一/国家级）和诱导点击（"点开有惊喜"）"""

_BODY_RULES = """\
## 正文规则（500-800字）
- 结构：总-分-总
  开头（≤3行）：抛痛点或核心结论，制造「我也是」共鸣
  正文：分点展开，用emoji做段落标记（📌✅💡🔥⭐），不用markdown
  结尾：总结一句话 + 互动钩子
- 排版：每段1-3行，段间空一行，适配手机竖屏
- 语气：像朋友分享经验。用「我」不用「你应该」，用「亲测/实测/踩坑」增加可信度
- emoji总量：全文10-15个，不要堆砌（连续≤2个）
- 不要用markdown语法（## / ** / ``` 等），小红书不渲染markdown

## SEO关键词布局
- 从标题中提取1-2个核心关键词
- 每300字自然出现1次（分布在开头/中间/结尾），禁止同段堆砌
- 关键词要融入句子，不能生硬插入"""

_INTERACTION_RULES = """\
## 结尾互动引导（必须有——评论权重=4倍）
用提问句结尾，引发用户分享自身经历：
- 「你们平时用什么工具？评论区聊聊 👇」
- 「还想看哪个方向的内容？留言告诉我～」
- 「你踩过哪些坑？评论区说说 💬」
- 「觉得有用的话帮我收藏一下，下次找不到就亏了 ⭐」"""

_HASHTAG_RULES = """\
## 标签规则（8-10个，三层结构，放正文末尾独立成段）
- 大话题 2-3个：高热度通用词（如 #穿搭 #效率工具），获取泛流量
- 中话题 3-4个：品类精准词（如 #AI办公 #敏感肌护肤），触达目标用户
- 小话题 2-3个：细分长尾词（如 #30天效率挑战 #北京咖啡探店），竞争小转化高
- 格式：#标签名（无空格），标签必须与内容强相关（不相关=降权）"""

_COVER_RULES = """\
## 封面图建议（输出到 [封面建议] 区块）
- 比例：3:4竖版（1242×1660px），双列信息流占据更大视觉空间
- 文字排版：三行四字法——主标题分3行，每行4-6字，粗体大字号
- 文字与背景必须高对比度（深底白字 或 白底深字）
- 视觉元素控制在3-5个以内（0.8秒内必须传达核心信息）
- 风格参考：
  干货/教程 → 简约留白 + 清晰粗体标题
  日常分享 → 圆润字体 + 暖色系
  知识科普 → 纯文字大字报风格
- 推荐配色：珊瑚粉#FF6B6B + 薄荷绿#4ECDC4（点击率+28%）"""

_BANNED_RULES = """\
## 禁止事项（触发限流或违规）
- 站外平台词：微信、淘宝、拼多多、公众号、抖音、快手、B站
- 医学功效词：减肥、美白、抗衰、消炎、祛痘、祛斑、药效
- 绝对化用语：最佳、第一、顶级、国家级、全网最
- 消费诱导词：秒杀、限时、再不抢就没了、清仓
- AI生成内容必须人工修改≥30%并标注「AI辅助创作」（否则限流50%）
- 不要写成教程口吻（「第一步…第二步…」），要写成分享口吻"""

_OUTPUT_FORMAT = """\
## 输出格式（严格遵守）
第一行是标题（以 # 开头）

空行后是正文（emoji分段，无markdown）

空行后是标签段（8-10个 #标签）

空行后是封面建议（以 [封面建议] 开头，1-3句描述封面构图/配色/文字）"""


class XiaohongshuFormatter(Formatter):
    """Formats content as a Xiaohongshu note."""

    platform = "xiaohongshu"

    def format_prompt(
        self, content: NormalizedContent, writing_style: str | None = None
    ) -> tuple[str, str]:
        system_parts = [
            _SYSTEM_CORE,
            "",
            _TITLE_RULES,
            "",
            _BODY_RULES,
            "",
            _INTERACTION_RULES,
            "",
            _HASHTAG_RULES,
            "",
            _COVER_RULES,
            "",
            _BANNED_RULES,
            "",
            _OUTPUT_FORMAT,
        ]
        if writing_style:
            system_parts.extend(["", "## 写作风格要求", writing_style])

        key_points_text = (
            "\n".join(f"- {p}" for p in content.key_points)
            if content.key_points
            else "无"
        )

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
        cover_lines: list[str] = []
        in_cover = False

        for line in lines:
            stripped = line.strip()

            # Cover brief section
            if stripped.startswith("[封面建议]") or stripped.startswith("【封面建议】"):
                in_cover = True
                rest = re.sub(r"^[\[【]封面建议[\]】]\s*", "", stripped)
                if rest:
                    cover_lines.append(rest)
                continue
            if in_cover:
                if stripped.startswith("#") or stripped == "":
                    if cover_lines:
                        in_cover = False
                    else:
                        continue
                else:
                    cover_lines.append(stripped)
                    continue

            # Title (first line starting with single #)
            if not title and stripped.startswith("#") and not stripped.startswith("##"):
                candidate = stripped.lstrip("# ").strip()
                # Distinguish title from hashtag-only lines
                if len(candidate) > 5 and not candidate.startswith("#"):
                    title = candidate
                    continue

            # Hashtag line (multiple #tags on one line)
            tag_matches = re.findall(r"#([^\s#]+)", stripped)
            if tag_matches and all(
                stripped.replace(f"#{t}", "").strip() == ""
                or len(tag_matches) >= 3
                for t in tag_matches[:1]
            ):
                hashtags.extend(tag_matches)
                continue

            body_lines.append(line)

        # Fallback: extract hashtags from last few body lines
        if len(hashtags) < 3:
            for line in reversed(body_lines[-8:]):
                found = re.findall(r"#([^\s#]+)", line.strip())
                if found:
                    hashtags.extend(found)
                    body_lines.remove(line)

        body = "\n".join(body_lines).strip()
        cover_brief = "\n".join(cover_lines).strip() or None

        if len(title) > 30:
            title = title[:29] + "…"

        return RewriteResult(
            content_id=content.content_id,
            target_platform=self.platform,
            title=title,
            body=body,
            hashtags=hashtags[:12],
            cover_brief=cover_brief,
            status=RewriteStatus.SUCCESS,
        )


register_formatter("xiaohongshu", XiaohongshuFormatter())
