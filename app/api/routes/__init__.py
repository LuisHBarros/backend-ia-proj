from app.api.routes.chat_routes import router as chat_router
from app.api.routes.chat_stream_routes import router as chat_stream_router
from app.api.routes.health_routes import router as health_router

__all__ = ["chat_router", "chat_stream_router", "health_router"]

