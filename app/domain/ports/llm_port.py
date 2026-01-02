from typing import Protocol


class LLMPort(Protocol):
    """
    Protocol defining the interface for Large Language Model (LLM) implementations.
    
    This port follows the Hexagonal Architecture pattern, allowing the domain layer
    to remain independent of specific LLM provider implementations (OpenAI, Bedrock, etc.).
    
    Any class implementing this protocol must provide an async generate method that
    takes a message string and returns a generated response string.
    """
    
    async def generate(self, message: str) -> str:
        """
        Generate a response from the LLM based on the input message.
        
        Args:
            message: The input message/prompt to send to the LLM.
            
        Returns:
            The generated response from the LLM as a string.
            
        Raises:
            Implementation-specific exceptions may be raised for errors such as:
            - API authentication failures
            - Rate limiting
            - Network errors
            - Invalid input
        """
        ...