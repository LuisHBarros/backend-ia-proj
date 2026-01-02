import pytest
from pydantic import ValidationError
from app.api.schemas import MessageDTO


class TestMessageDTO:
    """Unit tests for MessageDTO schema."""

    def test_message_dto_valid(self):
        """Test that MessageDTO accepts valid message string."""
        payload = MessageDTO(message="Hello, world!")
        assert payload.message == "Hello, world!"

    def test_message_dto_empty_string(self):
        """Test that MessageDTO accepts empty string."""
        payload = MessageDTO(message="")
        assert payload.message == ""

    def test_message_dto_missing_field(self):
        """Test that MessageDTO raises error when message field is missing."""
        with pytest.raises(ValidationError) as exc_info:
            MessageDTO()
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("message",)
        assert errors[0]["type"] == "missing"

    def test_message_dto_invalid_type(self):
        """Test that MessageDTO raises error when message is not a string."""
        with pytest.raises(ValidationError) as exc_info:
            MessageDTO(message=123)
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("message",)
        assert "string_type" in errors[0]["type"] or "str" in str(errors[0]["type"]).lower()

    def test_message_dto_none_value(self):
        """Test that MessageDTO raises error when message is None."""
        with pytest.raises(ValidationError) as exc_info:
            MessageDTO(message=None)
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("message",)

    def test_message_dto_long_message(self):
        """Test that MessageDTO accepts long messages."""
        long_message = "A" * 10000
        payload = MessageDTO(message=long_message)
        assert payload.message == long_message

    def test_message_dto_special_characters(self):
        """Test that MessageDTO accepts special characters."""
        special_message = "Hello! @#$%^&*() 中文 🚀"
        payload = MessageDTO(message=special_message)
        assert payload.message == special_message

