"""Application settings, read from environment variables and the repo-root `.env`.

LLM providers are selected here, never in code: `LLM_PROVIDER` picks the primary,
`LLM_FALLBACK_PROVIDER` the one used when the primary is rate-limited (empty = no fallback).
Mistral, Groq and Ollama all expose an OpenAI-compatible API, so each provider is fully
described by a base URL, a model name and an optional API key.
"""

from enum import StrEnum
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/config.py -> repo root. In Docker the file is absent and compose injects the env.
REPO_ROOT_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class ProviderName(StrEnum):
    MISTRAL = "mistral"
    GROQ = "groq"
    OLLAMA = "ollama"


class ProviderConfig(BaseModel):
    name: ProviderName
    base_url: str
    model: str
    api_key: SecretStr | None = None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT_ENV_FILE, extra="ignore")

    database_url: str = "postgresql://docrag:docrag@localhost:5432/docrag"

    llm_provider: ProviderName = ProviderName.MISTRAL
    llm_fallback_provider: ProviderName | None = None

    mistral_api_key: SecretStr | None = None
    mistral_base_url: str = "https://api.mistral.ai/v1"
    mistral_model: str = "mistral-small-latest"

    groq_api_key: SecretStr | None = None
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = "llama-3.3-70b-versatile"

    # Ollama runs locally and needs no key.
    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_model: str = "llama3.1:8b"

    @field_validator("llm_fallback_provider", mode="before")
    @classmethod
    def empty_fallback_means_none(cls, value: object) -> object:
        # `LLM_FALLBACK_PROVIDER=` in .env arrives as "", which is not a valid enum value.
        return None if value == "" else value

    @model_validator(mode="after")
    def check_selected_providers(self) -> "Settings":
        # Fail at startup rather than on the first question.
        if self.llm_fallback_provider == self.llm_provider:
            raise ValueError("LLM_FALLBACK_PROVIDER must differ from LLM_PROVIDER")
        for name in (self.llm_provider, self.llm_fallback_provider):
            if name is not None and name != ProviderName.OLLAMA:
                if self.provider(name).api_key is None:
                    raise ValueError(f"{name.upper()}_API_KEY is required when {name} is selected")
        return self

    def provider(self, name: ProviderName) -> ProviderConfig:
        return ProviderConfig(
            name=name,
            base_url=getattr(self, f"{name}_base_url"),
            model=getattr(self, f"{name}_model"),
            api_key=getattr(self, f"{name}_api_key", None),
        )

    @property
    def primary_provider(self) -> ProviderConfig:
        return self.provider(self.llm_provider)

    @property
    def fallback_provider(self) -> ProviderConfig | None:
        if self.llm_fallback_provider is None:
            return None
        return self.provider(self.llm_fallback_provider)


@lru_cache
def get_settings() -> Settings:
    """Settings are read once per process; use as a FastAPI dependency."""
    return Settings()
