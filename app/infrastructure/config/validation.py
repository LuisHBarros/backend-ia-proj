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
    
    elif provider == "bedrock":
        if not settings.aws_region:
            errors.append(
                "AWS_REGION is required when LLM_PROVIDER=bedrock. "
                "Set it as an environment variable or in .env file."
            )
        # Note: AWS credentials are typically provided via IAM role,
        # AWS CLI, or environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
        # We don't validate them here as they may be provided via IAM role
    
    elif provider not in ["openai", "bedrock", "mock"]:
        errors.append(
            f"Invalid LLM_PROVIDER: {provider}. "
            "Supported values: 'openai', 'bedrock', 'mock'"
        )
    
    # Validate database configuration (if provided)
    if settings.database_url:
        if not settings.database_url.startswith(("postgresql://", "postgresql+asyncpg://")):
            errors.append(
                "DATABASE_URL must start with 'postgresql://' or 'postgresql+asyncpg://'. "
                f"Got: {settings.database_url[:20]}..."
            )
    
    # Raise error if any validation failed
    if errors:
        error_message = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        raise ConfigurationError(error_message)
    
    return True

