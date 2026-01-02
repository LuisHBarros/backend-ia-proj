"""Factory for creating LLM instances based on configuration."""
import os
from typing import Optional
from app.domain.ports.llm_port import LLMPort
from app.infraestructure.llm.openai_llm import OpenAILLM
from app.infraestructure.llm.bedrock_llm import BedrockLLM
from app.infraestructure.llm.mock_llm import MockLLM


def create_llm(
    provider: Optional[str] = None,
    **kwargs
) -> LLMPort:
    """
    Factory function to create an LLM instance based on provider.
    
    Args:
        provider: The LLM provider to use. Options: 'openai', 'bedrock', 'mock'.
                  If not provided, auto-detects based on environment variables.
        **kwargs: Additional arguments passed to the LLM constructor.
        
    Returns:
        An instance of LLMPort implementation.
        
    Raises:
        ValueError: If provider is invalid or required configuration is missing.
    """
    # Auto-detect provider if not specified
    if provider is None:
        if os.getenv("OPENAI_API_KEY"):
            provider = "openai"
        elif os.getenv("AWS_REGION") or os.getenv("AWS_ACCESS_KEY_ID"):
            provider = "bedrock"
        else:
            provider = "mock"
    
    provider = provider.lower()
    
    if provider == "openai":
        return OpenAILLM(**kwargs)
    elif provider == "bedrock":
        return BedrockLLM(**kwargs)
    elif provider == "mock":
        return MockLLM()
    else:
        raise ValueError(
            f"Unknown LLM provider: {provider}. "
            "Supported providers: 'openai', 'bedrock', 'mock'"
        )

