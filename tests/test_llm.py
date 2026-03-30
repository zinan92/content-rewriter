"""Tests for Claude API client wrapper."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from content_rewriter.llm import (
    LLMClient,
    LLMError,
    load_cli_proxy_token,
)


class TestLoadCliProxyToken:
    def test_loads_token_from_file(self, tmp_path: Path) -> None:
        token_file = tmp_path / "claude-test.json"
        token_file.write_text(json.dumps({"access_token": "sk-test-123"}))
        token = load_cli_proxy_token(config_dir=tmp_path)
        assert token == "sk-test-123"

    def test_returns_none_when_no_files(self, tmp_path: Path) -> None:
        token = load_cli_proxy_token(config_dir=tmp_path)
        assert token is None

    def test_returns_none_when_missing_access_token(self, tmp_path: Path) -> None:
        token_file = tmp_path / "claude-bad.json"
        token_file.write_text(json.dumps({"other_key": "value"}))
        token = load_cli_proxy_token(config_dir=tmp_path)
        assert token is None


class TestLLMClient:
    def test_init_with_api_key(self) -> None:
        client = LLMClient(api_key="sk-direct-key")
        assert client.api_key == "sk-direct-key"

    def test_init_raises_without_credentials(self, tmp_path: Path) -> None:
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(LLMError, match="No Claude API credentials"):
                LLMClient(config_dir=tmp_path)

    def test_generate_calls_api(self) -> None:
        client = LLMClient(api_key="sk-test")
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Generated text")]
        with patch.object(client._client, "messages") as mock_messages:
            mock_messages.create.return_value = mock_response
            result = client.generate(
                system="You are a helper.",
                user_message="Hello",
            )
            assert result == "Generated text"
            mock_messages.create.assert_called_once()
