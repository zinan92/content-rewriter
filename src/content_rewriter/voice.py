"""Voice profile loading and extraction."""

from __future__ import annotations

from pathlib import Path


DEFAULT_CONFIG_DIR = Path.home() / ".content-rewriter"
VOICE_PROFILE_FILENAME = "voice-profile.md"


def load_voice_profile(config_dir: Path = DEFAULT_CONFIG_DIR) -> str | None:
    """Load the voice profile from the config directory."""
    profile_path = config_dir / VOICE_PROFILE_FILENAME
    if not profile_path.exists():
        return None
    content = profile_path.read_text().strip()
    return content if content else None
