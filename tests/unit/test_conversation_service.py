import pytest
from app.application.services.chat_service import ChatService
from app.infrastructure.persistence import InMemoryRepository


class MockLLM:
    """Mock LLM implementation for testing."""
    
    def __init__(self, response: str = "Mock response"):
        self.response = response
        self.called_with = None
    
    async def generate(self, message: str) -> str:
        self.called_with = message
        return self.response


class TestChatService:
    """Unit tests for ChatService."""

    @pytest.mark.asyncio
    async def test_handle_calls_llm_generate(self):
        """Test that handle method calls LLM generate with correct message."""
        mock_llm = MockLLM(response="Test response")
        repository = InMemoryRepository()
        service = ChatService(llm=mock_llm, repository=repository)
        
        result = await service.handle("Test message")
        
        assert result["response"] == "Test response"
        assert mock_llm.called_with == "Test message"
        assert "conversation_id" in result

    @pytest.mark.asyncio
    async def test_handle_preserves_llm_response(self):
        """Test that handle method preserves the exact LLM response."""
        custom_response = "Custom LLM response with special chars: @#$%"
        mock_llm = MockLLM(response=custom_response)
        repository = InMemoryRepository()
        service = ChatService(llm=mock_llm, repository=repository)
        
        result = await service.handle("Any message")
        
        assert result["response"] == custom_response

    @pytest.mark.asyncio
    async def test_handle_with_conversation_id(self):
        """Test that handle method works with conversation ID."""
        mock_llm = MockLLM(response="Response")
        repository = InMemoryRepository()
        service = ChatService(llm=mock_llm, repository=repository)
        
        # First message
        result1 = await service.handle("Message 1", user_id="user1")
        conversation_id = result1["conversation_id"]
        
        # Continue conversation
        result2 = await service.handle(
            "Message 2",
            user_id="user1",
            conversation_id=conversation_id
        )
        
        assert result2["conversation_id"] == conversation_id

