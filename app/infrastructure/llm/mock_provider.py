"""Mock LLM provider implementation for testing and development."""
import asyncio
from typing import AsyncGenerator
from app.domain.ports.llm_port import LLMPort


class MockProvider(LLMPort):
    """
    Mock LLM implementation that echoes the input message.
    
    Useful for:
    - Local development
    - Testing
    - CI/CD pipelines where real LLM APIs are not available
    """
    
    async def generate(self, message: str) -> str:
        """
        Generate a mock response by echoing the input message.
        
        Args:
            message: The input message.
            
        Returns:
            A formatted echo response.
        """
        return f"Echo: {message}"
    
    async def generate_stream(self, message: str) -> AsyncGenerator[str, None]:
        """
        Generate a streaming mock response.
        
        Args:
            message: The input message.
            
        Yields:
            Chunks of the echo response.
        """
        response = f"Echo: {message}"
        chunk_size = 5
        for i in range(0, len(response), chunk_size):
            yield response[i:i + chunk_size]
            await asyncio.sleep(0.05)  # Small delay to simulate streaming

