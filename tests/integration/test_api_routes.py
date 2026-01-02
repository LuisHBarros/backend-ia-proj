import pytest
from fastapi import status
from fastapi.testclient import TestClient


class TestMessageEndpoint:
    """Integration tests for POST /message endpoint."""

    def test_post_message_success(self, client: TestClient):
        """Test successful message submission."""
        response = client.post(
            "/message",
            json={"message": "Hello, AI!"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "response" in data
        assert isinstance(data["response"], str)
        assert "Echo: Hello, AI!" in data["response"]

    def test_post_message_empty_string(self, client: TestClient):
        """Test message submission with empty string."""
        response = client.post(
            "/message",
            json={"message": ""}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "response" in data

    def test_post_message_missing_field(self, client: TestClient):
        """Test message submission with missing message field."""
        response = client.post(
            "/message",
            json={}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "detail" in data

    def test_post_message_invalid_type(self, client: TestClient):
        """Test message submission with invalid type."""
        response = client.post(
            "/message",
            json={"message": 123}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_post_message_long_message(self, client: TestClient):
        """Test message submission with long message."""
        long_message = "A" * 1000
        response = client.post(
            "/message",
            json={"message": long_message}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "response" in data

    def test_post_message_special_characters(self, client: TestClient):
        """Test message submission with special characters."""
        special_message = "Hello! @#$%^&*() 中文 🚀"
        response = client.post(
            "/message",
            json={"message": special_message}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "response" in data

    def test_post_message_wrong_method(self, client: TestClient):
        """Test that GET method is not allowed on /message endpoint."""
        response = client.get("/message")
        
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


class TestHealthEndpoint:
    """Integration tests for GET /health endpoint."""

    def test_get_health_success(self, client: TestClient):
        """Test successful health check."""
        response = client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == {"status": "ok"}

    def test_get_health_wrong_method(self, client: TestClient):
        """Test that POST method is not allowed on /health endpoint."""
        response = client.post("/health")
        
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_get_health_multiple_calls(self, client: TestClient):
        """Test that health endpoint works with multiple calls."""
        for _ in range(5):
            response = client.get("/health")
            assert response.status_code == status.HTTP_200_OK
            assert response.json() == {"status": "ok"}

