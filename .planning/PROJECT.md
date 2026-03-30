# content-rewriter

Content pipeline Step 05: 双向平台内容转换器。接收 content-extractor 输出的结构化 JSON（转录文本、分析结果、元数据），通过 adapter 模式转换为目标平台原生格式。支持任意平台间转换（如抖音→小红书、抖音→微信公众号）。Voice Profile 系统确保输出匹配用户个人风格。CLI + Python library 形态，无 HTTP 服务。

**Core Value:** 把已提取的结构化内容变成可直接发布的平台原生内容 — 解决"内容已有但分发摩擦太大"的问题。用户的抖音视频不再只活在一个平台上。

## Constraints

- **Tech stack**: Python 3.13+ / Pydantic / pytest / Typer — 与 content-extractor 保持一致
- **LLM**: Claude API（通过 CLI Proxy API 或 ANTHROPIC_API_KEY）
- **输入**: content-extractor 输出的 structured JSON（transcript.json + analysis.json + structured_text.md）
- **输出**: 平台原生 markdown 草稿，写入 output/<content-id>/<platform>_draft.md
- **Adapter pattern**: 与 content-downloader 一致的 adapter 架构
- **Voice Profile**: voice-profile.md 文件，通过分析最佳内容提取风格特征

## Design Doc

完整设计文档: `~/.gstack/projects/wendy/wendy-main-design-20260330-125509.md`
- 经过 /office-hours 完整流程产出
- 2 轮 adversarial review, 10 issues fixed, quality 7.5/10
- Status: APPROVED

## Platform Format Specs

### 小红书 (Xiaohongshu)
- 标题: ≤20 字
- 正文: 400-600 字最佳（上限 1000 字）
- 图片: 6-9 张，3:4 竖版，最多 9 张
- 话题: 正文下方选 1 个话题
- 标签: 正文内 #hashtag + 图片标签

### 微信公众号 (WeChat Official Account)
- 标题: ≤13 字最佳（避免遮挡封面图）
- 封面图: 900x500px (一级), 200x200px (二级)
- 正文字号: 14-16px，注释 12px
- 正文配图: 宽度 ≤640px，建议 900x600px
- 支持富文本 HTML 排版
