"""Claude API client wrapper with CLI Proxy API support."""

from __future__ import annotations

import json
import os
from pathlib import Path

import anthropic


class LLMError(Exception):
    """Raised when LLM operations fail."""


DEFAULT_CONFIG_DIR = Path.home() / ".cli-proxy-api"
DEFAULT_MODEL = "claude-sonnet-4-6"


def load_cli_proxy_token(config_dir: Path = DEFAULT_CONFIG_DIR) -> str | None:
    """Load access token from CLI Proxy API config files."""
    if not config_dir.exists():
        return None
    for f in sorted(config_dir.glob("claude-*.json"), reverse=True):
        try:
            data = json.loads(f.read_text())
            token = data.get("access_token")
            if token:
                return token
        except (json.JSONDecodeError, OSError):
            continue
    return None


class LLMClient:
    """Wrapper around the Anthropic SDK with CLI Proxy API fallback."""

    def __init__(
        self,
        api_key: str | None = None,
        config_dir: Path = DEFAULT_CONFIG_DIR,
        model: str = DEFAULT_MODEL,
    ) -> None:
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY") or load_cli_proxy_token(config_dir)
        if not self.api_key:
            raise LLMError(
                "No Claude API credentials found. Set ANTHROPIC_API_KEY or "
                "ensure CLI Proxy API tokens exist in ~/.cli-proxy-api/"
            )
        self.model = model
        self._client = anthropic.Anthropic(api_key=self.api_key)

    def generate(
        self,
        system: str,
        user_message: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> str:
        """Generate a response from Claude."""
        try:
            response = self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user_message}],
                temperature=temperature,
            )
            return response.content[0].text
        except anthropic.APIError as e:
            raise LLMError(f"Claude API error: {e}") from e
