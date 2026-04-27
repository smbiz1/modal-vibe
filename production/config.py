"""Production configuration

Centralized configuration for production deployment.
All settings can be overridden via environment variables.
"""

import os
from typing import List
from pydantic import BaseModel, Field


class ProductionConfig(BaseModel):
    """Production configuration settings"""

    # API settings
    max_concurrent_requests: int = Field(
        default=200,
        description="Maximum concurrent requests per container"
    )
    min_containers: int = Field(
        default=1,
        description="Minimum number of containers to keep warm"
    )

    # Sandbox settings
    sandbox_timeout_seconds: int = Field(
        default=3600,
        description="Sandbox timeout in seconds (1 hour default for production)"
    )
    max_sandboxes_per_user: int = Field(
        default=10,
        description="Optional rate limiting: max sandboxes per user"
    )

    # Cleanup settings
    cleanup_interval_minutes: int = Field(
        default=5,
        description="How often to run cleanup of dead apps"
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL"
    )

    # Authentication
    require_api_key: bool = Field(
        default=True,
        description="Whether to require API key authentication"
    )

    # CORS settings
    allowed_origins: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:8000",
        ],
        description="Allowed CORS origins"
    )

    # Modal Dict
    dict_name: str = Field(
        default="sandbox-apps-production",
        description="Name of Modal.Dict for storing app metadata"
    )

    # Anthropic API
    anthropic_model: str = Field(
        default="claude-sonnet-4-20250514",
        description="Anthropic model to use for code generation"
    )
    anthropic_max_tokens: int = Field(
        default=8192,
        description="Max tokens for Anthropic API responses"
    )
    anthropic_temperature: float = Field(
        default=0.5,
        description="Temperature for Anthropic API (0.0-1.0)"
    )

    class Config:
        # Allow environment variables to override config
        env_prefix = "MODAL_VIBE_"
        # Example: MODAL_VIBE_MAX_CONCURRENT_REQUESTS=300

    @classmethod
    def from_env(cls) -> "ProductionConfig":
        """Load configuration from environment variables"""
        return cls(
            max_concurrent_requests=int(os.getenv("MODAL_VIBE_MAX_CONCURRENT_REQUESTS", "200")),
            min_containers=int(os.getenv("MODAL_VIBE_MIN_CONTAINERS", "1")),
            sandbox_timeout_seconds=int(os.getenv("MODAL_VIBE_SANDBOX_TIMEOUT", "3600")),
            max_sandboxes_per_user=int(os.getenv("MODAL_VIBE_MAX_SANDBOXES_PER_USER", "10")),
            cleanup_interval_minutes=int(os.getenv("MODAL_VIBE_CLEANUP_INTERVAL", "5")),
            log_level=os.getenv("MODAL_VIBE_LOG_LEVEL", "INFO"),
            require_api_key=os.getenv("MODAL_VIBE_REQUIRE_API_KEY", "true").lower() == "true",
            allowed_origins=os.getenv(
                "MODAL_VIBE_ALLOWED_ORIGINS",
                "http://localhost:3000,http://localhost:8000"
            ).split(","),
            dict_name=os.getenv("MODAL_VIBE_DICT_NAME", "sandbox-apps-production"),
            anthropic_model=os.getenv("MODAL_VIBE_ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
            anthropic_max_tokens=int(os.getenv("MODAL_VIBE_ANTHROPIC_MAX_TOKENS", "8192")),
            anthropic_temperature=float(os.getenv("MODAL_VIBE_ANTHROPIC_TEMPERATURE", "0.5")),
        )


# Create default config instance
config = ProductionConfig.from_env()


# Example usage in main_api.py:
"""
from production.config import config

@app.function(
    min_containers=config.min_containers,
    timeout=config.sandbox_timeout_seconds,
)
@modal.concurrent(max_inputs=config.max_concurrent_requests)
def my_function():
    pass
"""
