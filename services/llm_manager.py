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
        if self._llm is None:
            self._initialize_llm()
    
    def _initialize_llm(self) -> None:
        """Initialize the LLM with OpenRouter configuration."""
        self._llm = ChatOpenAI(
            model=settings.default_model,
            temperature=settings.llm_temperature,
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        
        if settings.enable_privacy_logging:
            print(f"[PRIVACY] LLM initialized with model: {settings.default_model}")
            print(f"[PRIVACY] API calls routed through: openrouter.ai")
    
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
        return ChatOpenAI(
            model=model,
            temperature=settings.llm_temperature,
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1"
        )
    
    def switch_model(self, model: str) -> None:
        """
        Switch the default model.
        
        Args:
            model: New model identifier (e.g., "google/gemini-pro")
        """
        self._llm = ChatOpenAI(
            model=model,
            temperature=settings.llm_temperature,
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        
        if settings.enable_privacy_logging:
            print(f"[PRIVACY] Model switched to: {model}")


# Singleton instance
llm_manager = LLMManager()
