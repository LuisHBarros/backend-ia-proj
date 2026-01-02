"""Main application entry point."""
from fastapi import FastAPI
from app.infrastructure.config.settings import settings
from app.api.routes import chat_router

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
)

# Include routers
app.include_router(chat_router, prefix=settings.api_prefix)

@app.get("/health")
def health():
    """Root health check endpoint."""
    return {"status": "ok", "version": settings.app_version}
