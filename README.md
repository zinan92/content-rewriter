<div align="center">

# content-rewriter

**一条命令，把抖音视频变成小红书笔记 + 微信公众号文章**

[![Python](https://img.shields.io/badge/python-3.13+-blue.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-37%20passed-brightgreen.svg)]()
[![Coverage](https://img.shields.io/badge/coverage-88%25-brightgreen.svg)]()

</div>

---

```
in  content-extractor 输出的结构化 JSON（转录文本 + 关键点 + 元数据）
out 平台原生格式草稿（小红书笔记 / 微信公众号文章）

fail 平台不支持     → 报错 + 已支持平台列表
fail LLM API 失败   → 重试一次，仍失败则输出原始转录 + [REWRITE_FAILED] 标记
fail 输入 JSON 无效  → 打印缺失字段，exit 1
fail 无写作风格文件  → 使用通用风格，输出标记 [NO_WRITING_STYLE]

Adapters: douyin (normalizer), xiaohongshu (formatter), wechat (formatter)
```

## 示例输出

```bash
$ content-rewriter rewrite --from douyin --to xiaohongshu,wechat ./content_dir/

Warning: No writing style found. Output will use generic style.
Rewriting 7621048932151414054 from douyin to xiaohongshu, wechat...
  ✓ xiaohongshu → output/7621048932151414054/xiaohongshu_draft.md
  ✓ wechat → output/7621048932151414054/wechat_draft.md

Done! 2 draft(s) written.
```

**小红书草稿** — 标题 ≤20 字 + emoji，正文 400-600 字口语化，5 个话题标签：

```markdown
# 🔥 Sam Altman教我的成功第一课

看过上百篇成功学文章，只有这篇我反复读了十遍以上...

#成功学 #SamAltman #复利思维 #职业规划 #个人成长
```

**微信公众号草稿** — 标题 ≤13 字，引言→分节→总结结构，封面图建议：

```markdown
# 成功的秘密，藏在复利里

## 为什么这篇文章值得反复读
...
## 复利效应：不只是钱的事
...

封面图建议: 深色极简背景，中央放指数增长曲线...
```

## 架构

```
content-extractor output (structured JSON)
        │
        ▼
┌─────────────────────────────────────────┐
│            content-rewriter              │
│                                         │
│  ┌──────────────┐  ┌────────────────┐   │
│  │ Normalizer   │  │ Writing Style  │   │
│  │ (per source) │  │ (~/.content-   │   │
│  │              │  │  rewriter/     │   │
│  │ ▶ Douyin     │  │  writing-      │   │
│  └──────┬───────┘  │  style.md)     │   │
│         │          └───────┬────────┘   │
│         ▼                  │            │
│  ┌──────────────┐          │            │
│  │ Claude API   │◀─────────┘            │
│  │ (via CLI     │                       │
│  │  Proxy API)  │                       │
│  └──────┬───────┘                       │
│         │                               │
│         ▼                               │
│  ┌──────────────┐                       │
│  │ Formatter    │                       │
│  │ (per target) │                       │
│  │              │                       │
│  │ ▶ Xiaohongshu│                       │
│  │ ▶ WeChat     │                       │
│  └──────────────┘                       │
└─────────────────────────────────────────┘
        │
        ▼
  output/<content-id>/<platform>_draft.md
```

## 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/zinan92/content-rewriter.git
cd content-rewriter

# 2. 创建虚拟环境并安装
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 3. 确保 Claude API 可用（以下任选一种）
# 方式 A: CLI Proxy API（推荐，需要 cliproxyapi 运行在 localhost:8317）
# 方式 B: 直接设环境变量
export ANTHROPIC_API_KEY="your-key"

# 4. 运行改写
content-rewriter rewrite --from douyin --to xiaohongshu,wechat ./path/to/content_dir/
```

## 功能一览

| 功能 | 说明 | 状态 |
|------|------|------|
| 抖音 → 小红书 | 视频转录 → 小红书图文笔记（标题/正文/标签） | ✅ 已完成 |
| 抖音 → 微信公众号 | 视频转录 → 公众号文章（分节结构/封面图建议） | ✅ 已完成 |
| 写作风格匹配 | 从 `writing-style.md` 加载个人风格，注入 LLM prompt | ✅ 已完成 |
| 反馈追踪 | 记录 accept/reject 到 JSONL，用于风格优化 | ✅ 已完成 |
| CLI Proxy API | 自动检测本地 proxy，无需 API key | ✅ 已完成 |
| 风格提取 (`--extract-style`) | 从最佳内容自动提取写作风格 | 📋 计划中 |
| 批量改写 | 一次处理多个内容 | 📋 计划中 |
| 自动发布 | 集成 Social-Auto-Upload | 📋 计划中 |

## CLI 参考

```bash
# 改写内容
content-rewriter rewrite \
  --from douyin \
  --to xiaohongshu,wechat \
  --output-dir ./output \
  --style-dir ~/.content-rewriter \
  ./path/to/content_dir/

# 记录反馈
content-rewriter feedback accept ./output/draft.md \
  --content-id douyin_123 \
  --platform xiaohongshu
```

## 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| 运行时 | Python 3.13+ | 核心语言 |
| CLI | Typer + Rich | 命令行界面 |
| 数据模型 | Pydantic 2.x (frozen) | 输入/输出校验 |
| LLM | Claude API (Anthropic SDK) | 内容改写引擎 |
| 测试 | pytest + pytest-cov | 37 tests, 88% coverage |

## 项目结构

```
content-rewriter/
├── src/content_rewriter/
│   ├── cli.py              # Typer CLI (rewrite + feedback 命令)
│   ├── models.py           # ExtractorOutput, RewriteResult (frozen Pydantic)
│   ├── llm.py              # Claude API 客户端 (CLI Proxy + 直连)
│   ├── rewriter.py         # 核心引擎: normalizer → LLM → formatter
│   ├── style.py            # 写作风格加载
│   └── adapters/
│       ├── __init__.py     # Normalizer/Formatter 基类 + 注册表
│       ├── douyin.py       # 抖音 Normalizer
│       ├── xiaohongshu.py  # 小红书 Formatter (标题≤20字, 标签)
│       └── wechat.py       # 微信公众号 Formatter (文章结构, 封面图)
├── tests/                  # 37 个测试
└── pyproject.toml
```

## 配置

| 文件/变量 | 说明 | 必填 |
|-----------|------|------|
| CLI Proxy API (localhost:8317) | 本地 Claude API 代理 | 方式 A |
| `ANTHROPIC_API_KEY` | Anthropic API key | 方式 B |
| `~/.content-rewriter/writing-style.md` | 个人写作风格描述 | 否（无则用通用风格） |
| `~/.content-rewriter/feedback.jsonl` | 反馈日志（自动创建） | 否 |

## 在 Content Pipeline 中的位置

```
content-downloader → content-extractor → content-rewriter → [手动发布]
      (已有)            (在建)             (本项目)
```

## For AI Agents

```yaml
name: content-rewriter
version: 0.1.0
capability:
  summary: "Transform content-extractor output into platform-native drafts for Xiaohongshu and WeChat"
  in: "structured JSON (content_id, transcript, key_points, metadata)"
  out: "platform-native markdown drafts (xiaohongshu note + wechat article)"
  fail:
    - "unsupported platform → ValueError with supported list"
    - "LLM API error → retry once, fallback to raw transcript with [REWRITE_FAILED]"
    - "malformed input → ValidationError with missing fields"
    - "no writing style → proceed with generic style, mark [NO_WRITING_STYLE]"
  adapters: [douyin, xiaohongshu, wechat]
cli_command: content-rewriter
cli_args:
  - name: content_path
    type: path
    required: true
    description: "Path to directory containing extractor_output.json"
cli_flags:
  - name: --from
    type: string
    required: true
    description: "Source platform (e.g. douyin)"
  - name: --to
    type: string
    required: true
    description: "Target platform(s), comma-separated (e.g. xiaohongshu,wechat)"
  - name: --output-dir
    type: path
    description: "Output directory for drafts (default: ./output)"
  - name: --style-dir
    type: path
    description: "Writing style config directory (default: ~/.content-rewriter)"
```

### Agent 调用示例

```python
import subprocess

result = subprocess.run(
    [
        "content-rewriter", "rewrite",
        "--from", "douyin",
        "--to", "xiaohongshu,wechat",
        "./content_dir/",
    ],
    capture_output=True,
    text=True,
)

if result.returncode == 0:
    print("Drafts generated successfully")
    # Read output/content_id/xiaohongshu_draft.md
    # Read output/content_id/wechat_draft.md
else:
    print(f"Rewrite failed: {result.stderr}")
```

## 相关项目

| 项目 | 说明 | 链接 |
|------|------|------|
| content-downloader | 上游：统一下载多平台内容 | [zinan92/content-downloader](https://github.com/zinan92/content-downloader) |
| content-extractor | 上游：多模态内容提取（转录/OCR/分析） | 开发中 |

## License

MIT
