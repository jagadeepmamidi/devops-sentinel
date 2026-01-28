"""
DevOps Sentinel - Configuration Management
==========================================
Centralized configuration using Pydantic Settings.
Supports environment variables and .env file loading.
"""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # ===== LLM Configuration =====
    openrouter_api_key: str = Field(
        ...,
        description="OpenRouter API key for LLM access"
    )
    default_model: str = Field(
        default="google/gemini-pro",
        description="Default LLM model to use via OpenRouter"
    )
    llm_temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=2.0,
        description="LLM temperature for response generation"
    )
    
    # ===== Supabase Configuration =====
    supabase_url: Optional[str] = Field(
        default=None,
        description="Supabase project URL"
    )
    supabase_key: Optional[str] = Field(
        default=None,
        description="Supabase anon/service key"
    )
    
    # ===== Slack Configuration =====
    slack_webhook_url: Optional[str] = Field(
        default=None,
        description="Slack webhook URL for alerts"
    )
    
    # ===== Monitoring Configuration =====
    check_interval_seconds: int = Field(
        default=10,
        ge=1,
        description="Health check interval in seconds"
    )
    request_timeout_seconds: int = Field(
        default=10,
        ge=1,
        le=60,
        description="HTTP request timeout in seconds"
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retry attempts for failed requests"
    )
    
    # ===== Server Configuration =====
    server_host: str = Field(
        default="0.0.0.0",
        description="API server host"
    )
    server_port: int = Field(
        default=8080,
        description="API server port"
    )
    
    # ===== Feature Flags =====
    enable_privacy_logging: bool = Field(
        default=False,
        description="Log what data is being processed for transparency"
    )
    
    @property
    def has_supabase(self) -> bool:
        """Check if Supabase is configured."""
        return bool(self.supabase_url and self.supabase_key)
    
    @property
    def has_slack(self) -> bool:
        """Check if Slack is configured."""
        return bool(self.slack_webhook_url)


def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Singleton instance for easy imports
settings = get_settings()
