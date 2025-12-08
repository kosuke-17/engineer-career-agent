"""LLM Factory for creating LLM instances based on provider configuration."""

import os
from typing import Optional

from langchain_core.language_models.chat_models import BaseChatModel

from app.config import LLMProvider, Settings, get_settings


class LLMFactory:
    """Factory for creating LLM instances based on configuration."""

    def __init__(self, settings: Optional[Settings] = None):
        """Initialize the factory with settings."""
        self.settings = settings or get_settings()
        self._setup_langsmith()

    def _setup_langsmith(self) -> None:
        """Setup LangSmith tracing if enabled.

        LangSmith is LangChain's monitoring and observability platform.
        It tracks LLM calls, latency, costs, and errors.

        To enable:
        1. Set LANGCHAIN_TRACING_V2=true
        2. Set LANGCHAIN_API_KEY=your-api-key (get from https://smith.langchain.com)
        3. Optionally set LANGCHAIN_PROJECT=project-name
        """
        if self.settings.langchain_tracing:
            # Set environment variables for LangSmith
            os.environ["LANGCHAIN_TRACING"] = "true"

            if self.settings.langchain_api_key:
                os.environ["LANGCHAIN_API_KEY"] = self.settings.langchain_api_key

            if self.settings.langchain_project:
                os.environ["LANGCHAIN_PROJECT"] = self.settings.langchain_project

            if self.settings.langchain_endpoint:
                os.environ["LANGCHAIN_ENDPOINT"] = self.settings.langchain_endpoint

    def create_chat_model(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> BaseChatModel:
        """
        Create a chat model based on the configured provider.

        Args:
            model: Optional model name override
            temperature: Optional temperature override
            max_tokens: Optional max tokens override

        Returns:
            BaseChatModel instance (ChatAnthropic or ChatOllama)
        """
        provider = self.settings.llm_provider
        temp = temperature if temperature is not None else self.settings.temperature
        tokens = max_tokens if max_tokens is not None else self.settings.max_tokens

        if provider == LLMProvider.ANTHROPIC:
            return self._create_anthropic_model(model, temp, tokens)
        elif provider == LLMProvider.OPENAI:
            return self._create_openai_model(model, temp, tokens)
        elif provider == LLMProvider.OLLAMA:
            return self._create_ollama_model(model, temp, tokens)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

    def _create_anthropic_model(
        self,
        model: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> BaseChatModel:
        """Create an Anthropic chat model."""
        from langchain_anthropic import ChatAnthropic

        model_name = model or self.settings.anthropic_model

        return ChatAnthropic(
            model=model_name,
            api_key=self.settings.anthropic_api_key,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def _create_openai_model(
        self,
        model: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> BaseChatModel:
        """Create an OpenAI chat model."""
        from langchain_openai import ChatOpenAI

        model_name = model or self.settings.openai_model

        return ChatOpenAI(
            model=model_name,
            api_key=self.settings.openai_api_key,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def _create_ollama_model(
        self,
        model: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> BaseChatModel:
        """Create an Ollama chat model."""
        from langchain_ollama import ChatOllama

        model_name = model or self.settings.ollama_model

        return ChatOllama(
            model=model_name,
            base_url=self.settings.ollama_base_url,
            temperature=temperature,
            num_predict=max_tokens,
        )

    def get_model_name(self) -> str:
        """Get the current model name based on provider."""
        if self.settings.llm_provider == LLMProvider.ANTHROPIC:
            return self.settings.anthropic_model
        elif self.settings.llm_provider == LLMProvider.OPENAI:
            return self.settings.openai_model
        elif self.settings.llm_provider == LLMProvider.OLLAMA:
            return self.settings.ollama_model
        else:
            return "unknown"

    def get_provider_info(self) -> dict:
        """Get information about the current LLM provider."""
        provider = self.settings.llm_provider

        if provider == LLMProvider.ANTHROPIC:
            return {
                "provider": "anthropic",
                "model": self.settings.anthropic_model,
                "api_key_set": bool(self.settings.anthropic_api_key),
            }
        elif provider == LLMProvider.OPENAI:
            return {
                "provider": "openai",
                "model": self.settings.openai_model,
                "api_key_set": bool(self.settings.openai_api_key),
            }
        elif provider == LLMProvider.OLLAMA:
            return {
                "provider": "ollama",
                "model": self.settings.ollama_model,
                "base_url": self.settings.ollama_base_url,
            }
        else:
            return {"provider": "unknown"}


# Convenience functions for getting LLM instances

_factory: Optional[LLMFactory] = None


def get_factory() -> LLMFactory:
    """Get or create a singleton LLM factory instance."""
    global _factory
    if _factory is None:
        _factory = LLMFactory()
    return _factory


def get_llm(
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> BaseChatModel:
    """
    Get an LLM instance based on current configuration.

    This is a convenience function that uses the singleton factory.

    Args:
        model: Optional model name override
        temperature: Optional temperature override
        max_tokens: Optional max tokens override

    Returns:
        BaseChatModel instance
    """
    return get_factory().create_chat_model(model, temperature, max_tokens)


def get_chat_model(
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> BaseChatModel:
    """
    Alias for get_llm for clarity.

    Args:
        model: Optional model name override
        temperature: Optional temperature override
        max_tokens: Optional max tokens override

    Returns:
        BaseChatModel instance
    """
    return get_llm(model, temperature, max_tokens)


def reset_factory() -> None:
    """Reset the singleton factory (useful for testing)."""
    global _factory
    _factory = None
