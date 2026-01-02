import os
from app.application.services.conversation_service import ConversationService
from app.infraestructure.llm.factory import create_llm


# Initialize service with LLM based on environment configuration
# Set LLM_PROVIDER env var to 'openai', 'bedrock', or 'mock' (default)
llm_provider = os.getenv("LLM_PROVIDER", "mock")
service = ConversationService(llm=create_llm(provider=llm_provider))

