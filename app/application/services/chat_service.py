"""Chat service - application service layer."""
from app.domain.ports.llm_port import LLMPort
from app.domain.ports.repository_port import RepositoryPort
from app.application.use_cases.process_message import ProcessMessageUseCase


class ChatService:
    """
    Application service for chat operations.
    
    This service coordinates use cases and provides a higher-level API
    for the application layer.
    """
    
    def __init__(
        self,
        llm: LLMPort,
        repository: RepositoryPort
    ):
        """
        Initialize the chat service.
        
        Args:
            llm: LLM port for generating responses.
            repository: Repository port for persistence.
        """
        self.process_message_use_case = ProcessMessageUseCase(
            llm=llm,
            repository=repository
        )
    
    async def handle(
        self,
        message: str,
        user_id: str = "default_user",
        conversation_id: str = None
    ) -> dict:
        """
        Handle a message and return the response.
        
        Args:
            message: The user's message.
            user_id: The user identifier.
            conversation_id: Optional conversation ID to continue.
            
        Returns:
            Dictionary with conversation_id, response, user_message, and assistant_message.
        """
        return await self.process_message_use_case.execute(
            user_id=user_id,
            message_content=message,
            conversation_id=conversation_id
        )

