"""Configuration validation on startup."""
from app.infrastructure.config.settings import settings
from app.infrastructure.exceptions import ConfigurationError


def validate_configuration():
    """
    Validate application configuration on startup.
    
    This function checks that all required configuration is present
    and valid. It raises ConfigurationError if validation fails.
    
    Raises:
        ConfigurationError: If required configuration is missing or invalid.
    """
    errors = []
    
    # Validate LLM provider configuration
    provider = settings.llm_provider.lower()
    
    if provider == "openai":
        if not settings.openai_api_key:
            errors.append(
                "OPENAI_API_KEY is required when LLM_PROVIDER=openai. "
                "Set it as an environment variable or in .env file."
            )
    
    elif provider not in ["openai", "mock"]:
        errors.append(
            f"Invalid LLM_PROVIDER: {provider}. "
            "Supported values: 'openai', 'mock'"
        )
    
    # Validate database configuration (if provided)
    if settings.database_url:
        if not settings.database_url.startswith(("postgresql://", "postgresql+asyncpg://")):
            errors.append(
                "DATABASE_URL must start with 'postgresql://' or 'postgresql+asyncpg://'. "
                f"Got: {settings.database_url[:20]}..."
            )
    
    # Validate database connection pool settings
    if settings.db_pool_size < 1:
        errors.append("DB_POOL_SIZE must be at least 1")
    if settings.db_max_overflow < 0:
        errors.append("DB_MAX_OVERFLOW must be non-negative")
    if settings.db_pool_timeout < 1:
        errors.append("DB_POOL_TIMEOUT must be at least 1 second")
    if settings.db_pool_recycle < 1:
        errors.append("DB_POOL_RECYCLE must be at least 1 second")
    
    # Validate LLM circuit breaker settings
    if settings.llm_circuit_breaker_enabled:
        if settings.llm_circuit_breaker_failure_threshold < 1:
            errors.append("LLM_CIRCUIT_BREAKER_FAILURE_THRESHOLD must be at least 1")
        if settings.llm_circuit_breaker_recovery_timeout < 1:
            errors.append("LLM_CIRCUIT_BREAKER_RECOVERY_TIMEOUT must be at least 1 second")
    
    # Validate LLM failure cooldown
    if settings.llm_failure_cooldown < 0:
        errors.append("LLM_FAILURE_COOLDOWN must be non-negative")
    
    # Validate rate limiting settings
    if settings.rate_limit_enabled:
        if settings.rate_limit_requests_per_minute < 1:
            errors.append("RATE_LIMIT_REQUESTS_PER_MINUTE must be at least 1")
        if settings.rate_limit_window_seconds < 1:
            errors.append("RATE_LIMIT_WINDOW_SECONDS must be at least 1 second")
    
    # Raise error if any validation failed
    if errors:
        error_message = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        raise ConfigurationError(error_message)
    
    return True

