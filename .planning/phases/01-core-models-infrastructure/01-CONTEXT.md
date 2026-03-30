# Phase 1: Core Models & Infrastructure - Context

**Gathered:** 2026-03-30
**Status:** Ready for planning
**Source:** /office-hours design doc (~/.gstack/projects/wendy/wendy-main-design-20260330-125509.md)

<domain>
## Phase Boundary

Phase 1 delivers the foundational layer: Pydantic data models, CLI skeleton, LLM client wrapper, and test infrastructure. After this phase, the project has a working CLI that can accept input JSON, validate it, and call Claude API. No platform-specific transformation yet (that's Phase 2).

</domain>

<decisions>
## Implementation Decisions

### Data Models
- ExtractorOutput: Pydantic model matching content-extractor provisional schema
- Must be compatible with content-downloader's ContentItem (same content_id, platform fields)
- All models use `frozen=True` (matching content-downloader convention)
- RewriteResult: content_id, target_platform, title, body, hashtags, metadata, status

### CLI Framework
- Typer (matching content-extractor, not Click like content-downloader)
- Entry point: `content-rewriter` command
- Core command: `rewrite --from <platform> --to <platform>[,<platform>] <content-id-or-path>`
- Input: path to ContentItem directory (containing extractor output JSON files)

### LLM Client
- Claude API via anthropic SDK
- Primary: CLI Proxy API token from `~/.cli-proxy-api/claude-*.json` (matching content-extractor pattern)
- Fallback: `ANTHROPIC_API_KEY` env var
- Token expiration handling with clear error message

### Project Structure
- `src/content_rewriter/` layout (matching content-extractor's src layout)
- pyproject.toml with setuptools backend (matching content-downloader)
- pytest with asyncio support and coverage

### Output Convention
- Drafts written to `output/<content-id>/<platform>_draft.md`
- Naming: `{content-id}_{platform}_{date}.md`

### Claude's Discretion
- Internal module organization within `src/content_rewriter/`
- Test fixture structure
- Error message formatting
- Logging approach

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Sibling Projects (patterns to follow)
- `~/work/content-co/content-downloader/content_downloader/models.py` — ContentItem Pydantic model (frozen=True pattern, field conventions)
- `~/work/content-co/content-downloader/pyproject.toml` — Project config pattern (setuptools, scripts entry)
- `~/work/content-co/content-extractor/CLAUDE.md` — Extractor tech stack decisions, CLI Proxy API pattern
- `~/work/content-co/content-extractor/.planning/REQUIREMENTS.md` — Extractor output schema (transcript.json, analysis.json)

### Design Document
- `~/.gstack/projects/wendy/wendy-main-design-20260330-125509.md` — Full approved design (provisional input schema, failure modes, success criteria)

</canonical_refs>

<specifics>
## Specific Ideas

### Provisional Input Schema (from design doc)
```json
{
  "content_id": "douyin_abc123",
  "source_platform": "douyin",
  "title": "...",
  "transcript": "...",
  "key_points": ["...", "..."],
  "visual_descriptions": ["frame 1: ...", "frame 2: ..."],
  "metadata": {
    "duration_seconds": 120,
    "publish_date": "2026-03-25",
    "engagement": { "views": 5000, "likes": 200, "comments": 30 }
  }
}
```

### Failure Modes (Phase 1 scope)
- Malformed JSON input: validate against schema, print missing fields, exit non-zero
- Missing extractor output files: clear error pointing to expected file paths

</specifics>

<deferred>
## Deferred Ideas

- Platform adapters (Phase 2)
- Voice profile system (Phase 3)
- Feedback loop (Phase 4)
- Auto-publishing integration
- Batch processing

</deferred>

---

*Phase: 01-core-models-infrastructure*
*Context gathered: 2026-03-30 via /office-hours design doc*
