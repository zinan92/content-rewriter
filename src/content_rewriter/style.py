"""Writing style loading and extraction."""

from __future__ import annotations

from pathlib import Path


DEFAULT_CONFIG_DIR = Path.home() / ".content-rewriter"
WRITING_STYLE_FILENAME = "writing-style.md"


def load_writing_style(config_dir: Path = DEFAULT_CONFIG_DIR) -> str | None:
    """Load the writing style from the config directory."""
    style_path = config_dir / WRITING_STYLE_FILENAME
    if not style_path.exists():
        return None
    content = style_path.read_text().strip()
    return content if content else None
