"""Use case for processing a message."""
from typing import Optional
from app.domain.ports.llm_port import LLMPort
from app.domain.ports.repository_port import RepositoryPort
from app.domain.value_objects.message import Message
from app.domain.entities.conversation import Conversation
from app.domain.exceptions import LLMError, RepositoryError


class ProcessMessageUseCase:
    """
    Use case for processing a user message and generating a response.
    
    This use case orchestrates:
    1. Loading conversation history
    2. Generating LLM response
    3. Saving the conversation
    """
    
    def __init__(
        self,
        llm: LLMPort,
        repository: RepositoryPort
    ):
        """
        Initialize the use case.
        
        Args:
            llm: LLM port for generating responses.
            repository: Repository port for persistence.
        """
        self.llm = llm
        self.repository = repository
    
    async def execute(
        self,
        user_id: str,
        message_content: str,
        conversation_id: Optional[str] = None
    ) -> dict:
        """
        Execute the use case.
        
        Args:
            user_id: The user identifier.
            message_content: The message content from the user.
            conversation_id: Optional conversation ID to continue existing conversation.
            
        Returns:
            Dictionary containing:
            - conversation_id: The conversation identifier
            - response: The generated response
            - user_message: The user's message
            - assistant_message: The assistant's response
            
        Raises:
            LLMError: If LLM generation fails.
            RepositoryError: If repository operations fail.
        """
        # Load or create conversation
        if conversation_id:
            conversation = await self.repository.find_by_id(conversation_id)
            if conversation is None:
                raise RepositoryError(f"Conversation {conversation_id} not found")
        else:
            conversation = Conversation(user_id=user_id)
        
        # Create user message value object
        user_message = Message(content=message_content, role="user")
        conversation.add_message(user_message)
        
        # Generate response using LLM
        try:
            response_content = await self.llm.generate(message_content)
        except Exception as e:
            raise LLMError(f"Failed to generate LLM response: {str(e)}") from e
        
        # Create assistant message value object
        assistant_message = Message(content=response_content, role="assistant")
        conversation.add_message(assistant_message)
        
        # Save conversation
        saved_conversation = await self.repository.save(conversation)
        
        return {
            "conversation_id": saved_conversation.id,
            "response": response_content,
            "user_message": message_content,
            "assistant_message": response_content
        }

