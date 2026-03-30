# Roadmap: content-rewriter v1

## Phase 1: Core Models & Infrastructure
**Goal:** Pydantic 数据模型 + CLI ��架 + LLM client + 测试基础设施
- 定义 input schema (ExtractorOutput) 和 output schema (RewriteResult)
- Typer CLI with `rewrite` command
- Claude API client wrapper (CLI Proxy API + fallback)
- pyproject.toml, pytest config, fixtures

## Phase 2: Platform Adapters
**Goal:** DouyinNormalizer + XiaohongshuFormatter + WeChatFormatter
- Base adapter interfaces (Normalizer, Formatter)
- Douyin normalizer: 去除视频特有语境，提取核心内容
- Xiaohongshu formatter: 标题≤20字、正文400-600字、carousel 结构、hashtags
- WeChat formatter: 文章结构、标题≤13字、封面图 brief、段落排版

## Phase 3: Voice Profile & Rewrite Engine
**Goal:** 声音特征提取 + 核心转换引擎 + 端到端测试
- Voice profile extraction (`--extract-voice`)
- Rewrite orchestration: normalizer → LLM + voice + formatter → output
- Feedback loop (`--feedback reject/accept`)
- End-to-end integration tests with stub data

## Phase 4: Polish & Eval
**Goal:** 错误处理完善 + 质量评估 + 文档
- Failure modes (API failure, malformed input, missing voice profile)
- Batch rewrite support
- Success criteria validation: accept rate tracking
- README + usage examples
