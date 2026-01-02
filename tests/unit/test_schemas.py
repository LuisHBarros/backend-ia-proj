import pytest
from pydantic import ValidationError
from app.api.dto.chat_dto import MessageRequestDTO


class TestMessageRequestDTO:
    """Unit tests for MessageRequestDTO schema."""

    def test_message_dto_valid(self):
        """Test that MessageRequestDTO accepts valid message string."""
        payload = MessageRequestDTO(message="Hello, world!")
        assert payload.message == "Hello, world!"

    def test_message_dto_with_user_id(self):
        """Test that MessageRequestDTO accepts user_id."""
        payload = MessageRequestDTO(message="Hello", user_id="user123")
        assert payload.message == "Hello"
        assert payload.user_id == "user123"

    def test_message_dto_with_conversation_id(self):
        """Test that MessageRequestDTO accepts conversation_id."""
        payload = MessageRequestDTO(message="Hello", conversation_id="conv123")
        assert payload.conversation_id == "conv123"

    def test_message_dto_empty_string(self):
        """Test that MessageRequestDTO rejects empty string."""
        with pytest.raises(ValidationError):
            MessageRequestDTO(message="")

    def test_message_dto_missing_field(self):
        """Test that MessageRequestDTO raises error when message field is missing."""
        with pytest.raises(ValidationError) as exc_info:
            MessageRequestDTO()
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("message",)
        assert errors[0]["type"] == "missing"

    def test_message_dto_invalid_type(self):
        """Test that MessageRequestDTO raises error when message is not a string."""
        with pytest.raises(ValidationError) as exc_info:
            MessageRequestDTO(message=123)
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("message",)

    def test_message_dto_long_message(self):
        """Test that MessageRequestDTO accepts long messages."""
        long_message = "A" * 10000
        payload = MessageRequestDTO(message=long_message)
        assert payload.message == long_message

    def test_message_dto_special_characters(self):
        """Test that MessageRequestDTO accepts special characters."""
        special_message = "Hello! @#$%^&*() 中文 🚀"
        payload = MessageRequestDTO(message=special_message)
        assert payload.message == special_message

