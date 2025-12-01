"""Configuration management for Learning Path Agent."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Anthropic API Configuration
    anthropic_api_key: str = Field(default="", description="Anthropic API Key")

    # Application Settings
    app_env: str = Field(default="development", description="Application environment")
    debug: bool = Field(default=True, description="Debug mode")

    # Server Settings
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")

    # Data Storage Paths
    data_dir: Path = Field(default=Path("./data"), description="Base data directory")
    memories_dir: Path = Field(
        default=Path("./data/memories"), description="Long-term memory storage"
    )
    sessions_dir: Path = Field(
        default=Path("./data/sessions"), description="Session data storage"
    )

    # LLM Settings
    default_model: str = Field(
        default="claude-sonnet-4-5-20250929", description="Default LLM model"
    )
    max_tokens: int = Field(default=4096, description="Maximum tokens for LLM response")
    temperature: float = Field(default=0.7, description="LLM temperature")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    def ensure_directories(self) -> None:
        """Create required directories if they don't exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.memories_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    settings = Settings()
    settings.ensure_directories()
    return settings
