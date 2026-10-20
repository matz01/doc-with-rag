import pytest
from pydantic import ValidationError

from app.config import ProviderName, Settings

PROVIDER_ENV_VARS = [
    "LLM_PROVIDER",
    "LLM_FALLBACK_PROVIDER",
    "MISTRAL_API_KEY",
    "GROQ_API_KEY",
]


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    # Keep the developer's shell environment out of the tests.
    for var in PROVIDER_ENV_VARS:
        monkeypatch.delenv(var, raising=False)


def make_settings(**overrides) -> Settings:
    # _env_file=None: ignore the real .env so tests only see what they set.
    return Settings(_env_file=None, **overrides)


def test_defaults_to_mistral_without_fallback():
    settings = make_settings(mistral_api_key="test-key")

    assert settings.primary_provider.name == ProviderName.MISTRAL
    assert settings.primary_provider.base_url == "https://api.mistral.ai/v1"
    assert settings.fallback_provider is None


def test_provider_is_selected_from_environment(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("LLM_FALLBACK_PROVIDER", "mistral")
    monkeypatch.setenv("GROQ_API_KEY", "groq-key")
    monkeypatch.setenv("MISTRAL_API_KEY", "mistral-key")

    settings = make_settings()

    assert settings.primary_provider.name == ProviderName.GROQ
    assert settings.primary_provider.api_key.get_secret_value() == "groq-key"
    assert settings.fallback_provider.name == ProviderName.MISTRAL


def test_empty_fallback_means_no_fallback(monkeypatch):
    monkeypatch.setenv("LLM_FALLBACK_PROVIDER", "")

    settings = make_settings(mistral_api_key="test-key")

    assert settings.fallback_provider is None


def test_ollama_needs_no_api_key():
    settings = make_settings(llm_provider="ollama")

    assert settings.primary_provider.api_key is None


def test_missing_api_key_for_selected_provider_fails():
    with pytest.raises(ValidationError, match="MISTRAL_API_KEY is required"):
        make_settings()


def test_missing_api_key_for_fallback_fails():
    with pytest.raises(ValidationError, match="GROQ_API_KEY is required"):
        make_settings(mistral_api_key="test-key", llm_fallback_provider="groq")


def test_fallback_must_differ_from_primary():
    with pytest.raises(ValidationError, match="must differ"):
        make_settings(mistral_api_key="test-key", llm_fallback_provider="mistral")


def test_api_key_is_not_leaked_in_repr():
    settings = make_settings(mistral_api_key="super-secret")

    assert "super-secret" not in repr(settings)
