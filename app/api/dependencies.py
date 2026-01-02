"""API dependencies for dependency injection."""
from app.application.services.chat_service import ChatService
from app.infrastructure.config.settings import settings
from app.infrastructure.llm import OpenAIProvider, BedrockProvider, MockProvider
from app.infrastructure.persistence import InMemoryRepository


def get_llm_provider():
    """
    Get LLM provider based on configuration.
    
    Returns:
        An instance of LLMPort implementation.
    """
    provider_name = settings.llm_provider.lower()
    
    if provider_name == "openai":
        return OpenAIProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_model
        )
    elif provider_name == "bedrock":
        return BedrockProvider(
            model_id=settings.bedrock_model_id,
            region=settings.aws_region
        )
    else:
        return MockProvider()


def get_repository():
    """
    Get repository instance.
    
    Returns:
        An instance of RepositoryPort implementation.
    """
    return InMemoryRepository()


def get_chat_service() -> ChatService:
    """
    Get chat service instance with dependencies injected.
    
    Returns:
        ChatService instance.
    """
    llm = get_llm_provider()
    repository = get_repository()
    return ChatService(llm=llm, repository=repository)

