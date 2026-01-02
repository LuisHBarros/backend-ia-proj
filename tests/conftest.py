import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api.routes import chat_router
from app.infrastructure.config.settings import settings


@pytest.fixture
def app():
    """Create a FastAPI app instance for testing."""
    test_app = FastAPI(title="AI Platform Test")
    test_app.include_router(chat_router, prefix=settings.api_prefix)
    return test_app


@pytest.fixture
def client(app):
    """Create a test client for the FastAPI app."""
    return TestClient(app)

