"""Claude API client wrapper with CLI Proxy API support."""

from __future__ import annotations

import json
import os
from pathlib import Path

import anthropic
import httpx


class LLMError(Exception):
    """Raised when LLM operations fail."""


DEFAULT_CONFIG_DIR = Path.home() / ".cli-proxy-api"
DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_PROXY_URL = "http://localhost:8317"
DEFAULT_PROXY_KEY = "sk-cliproxy-wendy"


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


def _detect_proxy(proxy_url: str = DEFAULT_PROXY_URL) -> bool:
    """Check if CLI Proxy API is running locally."""
    try:
        r = httpx.get(proxy_url, timeout=2)
        return r.status_code == 200 and "CLI Proxy API" in r.text
    except (httpx.ConnectError, httpx.TimeoutException):
        return False


class LLMClient:
    """Wrapper around Claude API with CLI Proxy API support.

    Resolution order:
    1. CLI Proxy API on localhost:8317 (OpenAI-compatible, uses proxy API key)
    2. ANTHROPIC_API_KEY environment variable (direct Anthropic API)
    3. Explicit api_key parameter
    """

    def __init__(
        self,
        api_key: str | None = None,
        config_dir: Path = DEFAULT_CONFIG_DIR,
        model: str = DEFAULT_MODEL,
        proxy_url: str = DEFAULT_PROXY_URL,
        proxy_key: str = DEFAULT_PROXY_KEY,
    ) -> None:
        self.model = model
        self._use_proxy = _detect_proxy(proxy_url)

        if self._use_proxy:
            self._proxy_url = proxy_url
            self._proxy_key = proxy_key
            self.api_key = proxy_key
            self._client = None
        else:
            self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY") or load_cli_proxy_token(config_dir)
            if not self.api_key:
                raise LLMError(
                    "No Claude API credentials found. Set ANTHROPIC_API_KEY, "
                    "ensure CLI Proxy API is running on localhost:8317, or "
                    "ensure tokens exist in ~/.cli-proxy-api/"
                )
            self._client = anthropic.Anthropic(api_key=self.api_key)
            self._proxy_url = None
            self._proxy_key = None

    def generate(
        self,
        system: str,
        user_message: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> str:
        """Generate a response from Claude."""
        if self._use_proxy:
            return self._generate_via_proxy(system, user_message, max_tokens, temperature)
        return self._generate_via_anthropic(system, user_message, max_tokens, temperature)

    def _generate_via_proxy(
        self, system: str, user_message: str, max_tokens: int, temperature: float
    ) -> str:
        """Generate via CLI Proxy API (OpenAI-compatible endpoint)."""
        try:
            r = httpx.post(
                f"{self._proxy_url}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._proxy_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user_message},
                    ],
                },
                timeout=120,
            )
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]["content"]
        except (httpx.HTTPError, KeyError, IndexError) as e:
            raise LLMError(f"CLI Proxy API error: {e}") from e

    def _generate_via_anthropic(
        self, system: str, user_message: str, max_tokens: int, temperature: float
    ) -> str:
        """Generate via direct Anthropic API."""
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
