import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api.routes import router


@pytest.fixture
def app():
    """Create a FastAPI app instance for testing."""
    test_app = FastAPI(title="AI Platform Test")
    test_app.include_router(router)
    return test_app


@pytest.fixture
def client(app):
    """Create a test client for the FastAPI app."""
    return TestClient(app)

