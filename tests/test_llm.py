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
    @patch("content_rewriter.llm._detect_proxy", return_value=False)
    def test_init_with_api_key(self, _mock_proxy: MagicMock) -> None:
        client = LLMClient(api_key="sk-direct-key")
        assert client.api_key == "sk-direct-key"
        assert client._use_proxy is False

    @patch("content_rewriter.llm._detect_proxy", return_value=False)
    def test_init_raises_without_credentials(self, _mock_proxy: MagicMock, tmp_path: Path) -> None:
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(LLMError, match="No Claude API credentials"):
                LLMClient(config_dir=tmp_path)

    @patch("content_rewriter.llm._detect_proxy", return_value=False)
    def test_generate_via_anthropic(self, _mock_proxy: MagicMock) -> None:
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

    @patch("content_rewriter.llm._detect_proxy", return_value=True)
    def test_init_with_proxy(self, _mock_proxy: MagicMock) -> None:
        client = LLMClient()
        assert client._use_proxy is True
        assert client._client is None

    @patch("content_rewriter.llm._detect_proxy", return_value=True)
    @patch("content_rewriter.llm.httpx.post")
    def test_generate_via_proxy(self, mock_post: MagicMock, _mock_proxy: MagicMock) -> None:
        client = LLMClient()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Proxy response"}}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = client.generate(system="System", user_message="Hello")
        assert result == "Proxy response"
        mock_post.assert_called_once()
