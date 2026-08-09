"""
DevOps Sentinel - LLM Manager
=============================
Centralized LLM management with OpenRouter integration.
Supports multiple models via user configuration.
"""

from typing import Optional
from langchain_openai import ChatOpenAI
from config import settings


class LLMManager:
    """
    Singleton manager for LLM instances.
    
    Provides centralized access to LLM with:
    - Model switching capability
    - Token usage tracking
    - Privacy-aware logging
    """
    
    _instance: Optional["LLMManager"] = None
    _llm: Optional[ChatOpenAI] = None
    
    def __new__(cls) -> "LLMManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Keep construction side-effect free. Configuration errors should be
        # raised when an agent actually requests an LLM, not while importing
        # the CLI or API modules.
        pass
    
    def _initialize_llm(self) -> None:
        """Initialize the configured LLM provider."""
        self._llm = self._build_llm(settings.default_model)
        
        if settings.enable_privacy_logging:
            print(f"[PRIVACY] LLM initialized with model: {settings.default_model}")
            print(f"[PRIVACY] API calls routed through: {settings.llm_provider}")

    @staticmethod
    def _build_llm(model: str) -> ChatOpenAI:
        """Build a provider-specific ChatOpenAI-compatible client."""
        provider = settings.llm_provider.lower().strip()
        if provider == "openrouter":
            if not settings.openrouter_api_key:
                raise ValueError("LLM_PROVIDER=openrouter requires OPENROUTER_API_KEY")
            return ChatOpenAI(
                model=model,
                temperature=settings.llm_temperature,
                api_key=settings.openrouter_api_key,
                base_url="https://openrouter.ai/api/v1",
            )

        if provider == "openai":
            if not settings.openai_api_key:
                raise ValueError("LLM_PROVIDER=openai requires OPENAI_API_KEY")
            if "/" in model:
                raise ValueError(
                    "Direct OpenAI models must use names such as gpt-4o-mini; "
                    "provider/model names are for OpenRouter"
                )
            return ChatOpenAI(
                model=model,
                temperature=settings.llm_temperature,
                api_key=settings.openai_api_key,
            )

        raise ValueError("LLM_PROVIDER must be either 'openrouter' or 'openai'")
    
    @property
    def llm(self) -> ChatOpenAI:
        """Get the LLM instance."""
        if self._llm is None:
            self._initialize_llm()
        return self._llm
    
    def get_llm(self, model: Optional[str] = None) -> ChatOpenAI:
        """
        Get LLM instance, optionally with a different model.
        
        Args:
            model: Override the default model for this request.
                   Format: "provider/model-name" (e.g., "anthropic/claude-3.5-sonnet")
        
        Returns:
            ChatOpenAI instance configured for OpenRouter.
        """
        if model is None or model == settings.default_model:
            return self.llm
        
        # Create a new instance with the specified model
        return self._build_llm(model)
    
    def switch_model(self, model: str) -> None:
        """
        Switch the default model.
        
        Args:
            model: New model identifier (e.g., "google/gemini-pro")
        """
        self._llm = self._build_llm(model)
        
        if settings.enable_privacy_logging:
            print(f"[PRIVACY] Model switched to: {model}")


# Singleton instance
llm_manager = LLMManager()
