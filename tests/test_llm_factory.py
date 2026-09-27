"""Tests for provider selection in cdr.llm.factory."""

import pytest

from cdr.config import reset_settings
from cdr.core.exceptions import ConfigurationError
from cdr.llm.factory import create_provider

PROVIDER_ENV_VARS = [
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "OPENAI_MODEL",
]


@pytest.fixture(autouse=True)
def clean_env(monkeypatch, tmp_path):
    """Isolate each test from the developer's real .env and environment."""
    monkeypatch.chdir(tmp_path)  # settings read .env from the working directory
    for var in PROVIDER_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    reset_settings()
    yield
    reset_settings()


def test_openai_without_key_or_base_url_is_a_config_error():
    with pytest.raises(ConfigurationError, match="OPENAI_BASE_URL"):
        create_provider("openai")


def test_openai_base_url_alone_is_enough_for_local_servers(monkeypatch):
    monkeypatch.setenv("OPENAI_BASE_URL", "http://localhost:11434/v1")
    monkeypatch.setenv("OPENAI_MODEL", "llama3.1:8b")
    reset_settings()

    provider = create_provider("openai")

    assert provider.model == "llama3.1:8b"
    assert str(provider._client.base_url).startswith("http://localhost:11434/v1")


def test_explicit_key_is_kept_with_base_url(monkeypatch):
    monkeypatch.setenv("OPENAI_BASE_URL", "http://localhost:8001/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    reset_settings()

    provider = create_provider("openai")

    assert provider._client.api_key == "sk-test"
