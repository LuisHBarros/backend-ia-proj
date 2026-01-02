"""Main application entry point."""
from fastapi import FastAPI
from app.infrastructure.config.settings import settings
from app.infrastructure.config.validation import validate_configuration
from app.api.routes import chat_router
from app.api.routes import chat_stream_routes
from app.api.routes import health_routes
from app.api.middleware.correlation import CorrelationIDMiddleware
from app.infrastructure.exceptions import ConfigurationError
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
)

# Validate configuration on startup
@app.on_event("startup")
async def startup_event():
    """Validate configuration on application startup."""
    try:
        validate_configuration()
        logger.info("Configuration validated successfully")
    except ConfigurationError as e:
        logger.error(f"Configuration validation failed: {e}")
        raise  # Fail fast if configuration is invalid

# Add middleware for correlation ID tracking
app.add_middleware(CorrelationIDMiddleware)

# Include routers
app.include_router(chat_router, prefix=settings.api_prefix)
app.include_router(chat_stream_routes.router, prefix=settings.api_prefix)
app.include_router(health_routes.router)

# Root health check is now handled by health_routes
