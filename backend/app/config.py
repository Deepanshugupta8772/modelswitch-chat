"""Environment-backed application settings."""

from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()


def _csv_values(value: str | None) -> tuple[str, ...]:
    return tuple(item.strip() for item in (value or "").split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    llm_api_keys: tuple[str, ...]
    llm_model: str
    default_system_prompt: str
    database_url: str
    allowed_origins: tuple[str, ...]
    cache_enabled: bool
    enable_failure_simulation: bool


def get_settings() -> Settings:
    """Read configuration without exposing secret values in responses or logs."""
    return Settings(
        llm_api_keys=_csv_values(os.getenv("LLM_API_KEYS")),
        llm_model=os.getenv("LLM_MODEL", "groq/openai/gpt-oss-120b"),
        default_system_prompt=os.getenv(
            "DEFAULT_SYSTEM_PROMPT", "You are a helpful assistant."
        ),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./data/app.db"),
        allowed_origins=_csv_values(
            os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
        ),
        cache_enabled=os.getenv("CACHE_ENABLED", "true").strip().lower()
        in {"1", "true", "yes", "on"},
        enable_failure_simulation=os.getenv("ENABLE_FAILURE_SIMULATION", "false")
        .strip()
        .lower()
        in {"1", "true", "yes", "on"},
    )
