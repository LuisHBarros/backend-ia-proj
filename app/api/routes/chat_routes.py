"""Chat API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.dto.chat_dto import MessageRequestDTO, MessageResponseDTO
from app.api.dependencies import get_chat_service
from app.application.services.chat_service import ChatService
from app.domain.exceptions import LLMError, RepositoryError


router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message", response_model=MessageResponseDTO)
async def send_message(
    payload: MessageRequestDTO,
    service: ChatService = Depends(get_chat_service)
):
    """
    Send a message and get AI response.
    
    Args:
        payload: The message request DTO.
        service: Injected chat service.
        
    Returns:
        MessageResponseDTO with the generated response.
        
    Raises:
        HTTPException: If processing fails.
    """
    try:
        result = await service.handle(
            message=payload.message,
            user_id=payload.user_id or "default_user",
            conversation_id=payload.conversation_id
        )
        
        return MessageResponseDTO(
            conversation_id=result["conversation_id"],
            response=result["response"],
            user_message=result["user_message"],
            assistant_message=result["assistant_message"]
        )
    except LLMError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"LLM service error: {str(e)}"
        )
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Repository error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

