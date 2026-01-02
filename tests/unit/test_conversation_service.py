import pytest
from app.application.services.conversation_service import ConversationService


class MockLLM:
    """Mock LLM implementation for testing."""
    
    def __init__(self, response: str = "Mock response"):
        self.response = response
        self.called_with = None
    
    async def generate(self, message: str) -> str:
        self.called_with = message
        return self.response


class TestConversationService:
    """Unit tests for ConversationService."""

    @pytest.mark.asyncio
    async def test_handle_calls_llm_generate(self):
        """Test that handle method calls LLM generate with correct message."""
        mock_llm = MockLLM(response="Test response")
        service = ConversationService(llm=mock_llm)
        
        result = await service.handle("Test message")
        
        assert result == "Test response"
        assert mock_llm.called_with == "Test message"

    @pytest.mark.asyncio
    async def test_handle_with_empty_message(self):
        """Test that handle method works with empty message."""
        mock_llm = MockLLM(response="Empty response")
        service = ConversationService(llm=mock_llm)
        
        result = await service.handle("")
        
        assert result == "Empty response"
        assert mock_llm.called_with == ""

    @pytest.mark.asyncio
    async def test_handle_preserves_llm_response(self):
        """Test that handle method preserves the exact LLM response."""
        custom_response = "Custom LLM response with special chars: @#$%"
        mock_llm = MockLLM(response=custom_response)
        service = ConversationService(llm=mock_llm)
        
        result = await service.handle("Any message")
        
        assert result == custom_response

    @pytest.mark.asyncio
    async def test_handle_multiple_calls(self):
        """Test that handle method works correctly with multiple calls."""
        mock_llm = MockLLM(response="Response")
        service = ConversationService(llm=mock_llm)
        
        result1 = await service.handle("Message 1")
        result2 = await service.handle("Message 2")
        
        assert result1 == "Response"
        assert result2 == "Response"
        assert mock_llm.called_with == "Message 2"  # Last call

