# Requirements: content-rewriter

**Defined:** 2026-03-30
**Source:** /office-hours design doc + platform research

## v1 Requirements

### Foundation (Phase 1)

- [ ] **FOUND-01**: Define ExtractorOutput Pydantic model matching content-extractor provisional schema (content_id, source_platform, title, transcript, key_points, visual_descriptions, metadata)
- [ ] **FOUND-02**: Define RewriteResult Pydantic model (content_id, target_platform, title, body, hashtags, metadata, status)
- [ ] **FOUND-03**: Claude API client wrapper supporting CLI Proxy API token + ANTHROPIC_API_KEY fallback
- [ ] **FOUND-04**: Typer CLI with `rewrite` command accepting `--from`, `--to`, `<content-id>` arguments
- [ ] **FOUND-05**: Input JSON validation against ExtractorOutput schema, exit non-zero on malformed input
- [ ] **FOUND-06**: Output markdown drafts to `output/<content-id>/<platform>_draft.md`
- [ ] **FOUND-07**: pyproject.toml with project metadata, dependencies, CLI entry point

### Platform Adapters (Phase 2)

- [ ] **ADPT-01**: Base Normalizer abstract class with `normalize(ExtractorOutput) -> NormalizedContent`
- [ ] **ADPT-02**: Base Formatter abstract class with `format(NormalizedContent, VoiceProfile?) -> RewriteResult`
- [ ] **ADPT-03**: DouyinNormalizer — strip video-specific framing, extract core content
- [ ] **ADPT-04**: XiaohongshuFormatter — title ≤20 chars, body 400-600 chars, 5 hashtags, carousel structure
- [ ] **ADPT-05**: WeChatFormatter — article structure, title ≤13 chars, section headings, cover image brief
- [ ] **ADPT-06**: Router matching `--from` to Normalizer and `--to` to Formatter(s)

### Voice Profile & Engine (Phase 3)

- [ ] **VOICE-01**: Voice profile stored as `voice-profile.md` in config directory
- [ ] **VOICE-02**: `--extract-voice` command analyzing 5+ transcripts to extract style patterns
- [ ] **VOICE-03**: Graceful degradation: warn + `[NO_VOICE_PROFILE]` marker when profile missing
- [ ] **VOICE-04**: Rewrite orchestration: normalizer → LLM(voice + formatter prompt) → output
- [ ] **VOICE-05**: Retry on API failure with increased temperature, fallback to raw transcript with `[REWRITE_FAILED]`

### Feedback & Polish (Phase 4)

- [ ] **FDBK-01**: `--feedback reject|accept <draft-path>` appending to `~/.content-rewriter/feedback.jsonl`
- [ ] **FDBK-02**: Feedback log format: JSONL with draft_path, platform, content_id, timestamp, action
- [ ] **FDBK-03**: Batch rewrite support for multiple content IDs
- [ ] **FDBK-04**: Accept rate tracking from feedback log

## Phase → Requirement Mapping

| Phase | Requirements |
|-------|-------------|
| 1 | FOUND-01 through FOUND-07 |
| 2 | ADPT-01 through ADPT-06 |
| 3 | VOICE-01 through VOICE-05 |
| 4 | FDBK-01 through FDBK-04 |
