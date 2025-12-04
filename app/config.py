"""Configuration management for Learning Path Agent.

=== pydantic_settings の仕組み ===

このファイルでは pydantic_settings の BaseSettings を使用して環境変数を一元管理しています。

【重要な特徴】
1. BaseSettings を継承したクラスのフィールドは、自動的に環境変数から値を読み込みます
2. フィールド名は自動的に大文字のスネークケースに変換されます
   例: anthropic_api_key → 環境変数 ANTHROPIC_API_KEY
       llm_provider → 環境変数 LLM_PROVIDER
3. model_config の env_file で .env ファイルからも読み込めます
4. 環境変数が設定されていない場合は Field(default=...) の値が使用されます

【優先順位】
環境変数 > .envファイル > デフォルト値

【使い方】
他のファイルでは get_settings() を呼び出して設定を取得します:
    from app.config import get_settings
    settings = get_settings()
    api_key = settings.anthropic_api_key

【Field() について】
Field() は pydantic の関数で、フィールドに追加情報を設定します:
    - default: デフォルト値
    - description: フィールドの説明（ドキュメント生成やAPIスキーマに使用）
    - ge/le/gt/lt: 数値の範囲制限（ge=以上, le=以下, gt=より大きい, lt=未満）
    - min_length/max_length: 文字列の長さ制限
    - pattern: 正規表現によるバリデーション
    - alias: 環境変数名を別名にする

例:
    port: int = Field(default=8000, ge=1, le=65535)  # 1〜65535の範囲でバリデーション
"""

from enum import Enum
from functools import lru_cache
from pathlib import Path

from pydantic import Field  # フィールドにデフォルト値や説明、バリデーションを設定する
from pydantic_settings import BaseSettings  # 環境変数から自動で値を読み込むクラス


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    OLLAMA = "ollama"


class Settings(BaseSettings):
    """環境変数から設定を読み込むクラス。

    各フィールド名が自動的に環境変数名にマッピングされます。
    例: anthropic_api_key → ANTHROPIC_API_KEY
    """

    # === LLM Provider Settings ===
    # 環境変数: LLM_PROVIDER (値: "anthropic" または "ollama")
    llm_provider: LLMProvider = Field(
        default=LLMProvider.ANTHROPIC,
        description="LLM provider to use (anthropic or ollama)",
    )

    # === Anthropic API Configuration ===
    # 環境変数: ANTHROPIC_API_KEY
    anthropic_api_key: str = Field(default="", description="Anthropic API Key")

    # === OpenAI API Configuration ===
    # 環境変数: OPENAI_API_KEY
    openai_api_key: str = Field(default="", description="OpenAI API Key")
    # 環境変数: OPENAI_MODEL
    openai_model: str = Field(
        default="gpt-4o-mini",
        description="OpenAI model to use (e.g., gpt-4o, gpt-4o-mini, gpt-4-turbo)",
    )

    # === Ollama Configuration ===
    # 環境変数: OLLAMA_BASE_URL
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama server base URL",
    )
    # 環境変数: OLLAMA_MODEL
    ollama_model: str = Field(
        default="gpt-oss:20b",
        description="Ollama model to use",
    )

    # === Tavily API Configuration ===
    # 環境変数: TAVILY_API_KEY
    tavily_api_key: str = Field(default="", description="Tavily API Key for web search")

    # === Application Settings ===
    # 環境変数: APP_ENV
    app_env: str = Field(default="development", description="Application environment")
    # 環境変数: DEBUG (値: true または false)
    debug: bool = Field(default=True, description="Debug mode")

    # === Server Settings ===
    # 環境変数: HOST
    host: str = Field(default="0.0.0.0", description="Server host")
    # 環境変数: PORT
    port: int = Field(default=8000, description="Server port")

    # === Data Storage Paths ===
    # 環境変数: DATA_DIR
    data_dir: Path = Field(default=Path("./data"), description="Base data directory")
    # 環境変数: MEMORIES_DIR
    memories_dir: Path = Field(
        default=Path("./data/memories"), description="Long-term memory storage"
    )
    # 環境変数: SESSIONS_DIR
    sessions_dir: Path = Field(default=Path("./data/sessions"), description="Session data storage")

    # === LLM Settings (for Anthropic) ===
    # 環境変数: ANTHROPIC_MODEL
    anthropic_model: str = Field(
        default="claude-sonnet-4-5-20250929", description="Default Anthropic model"
    )
    # 環境変数: MAX_TOKENS
    max_tokens: int = Field(default=4096, description="Maximum tokens for LLM response")
    # 環境変数: TEMPERATURE
    temperature: float = Field(default=0.7, description="LLM temperature")

    # === pydantic_settings の設定 ===
    model_config = {
        "env_file": ".env",  # .envファイルから環境変数を読み込む
        "env_file_encoding": "utf-8",  # ファイルのエンコーディング
        "extra": "ignore",  # 定義されていない環境変数は無視する
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
