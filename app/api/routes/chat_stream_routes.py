"""Chat streaming API routes (SSE)."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from app.api.dto.chat_dto import MessageRequestDTO
from app.api.dependencies import get_process_message_use_case
from app.application.use_cases.process_message import ProcessMessageUseCase
from app.domain.ports.llm_port import LLMPort
from app.bootstrap import get_container
import json


router = APIRouter(prefix="/chat", tags=["chat"])


async def _stream_llm_response(llm: LLMPort, message: str):
    """
    Stream LLM response chunks.
    
    Args:
        llm: LLM provider instance.
        message: The message to send to LLM.
        
    Yields:
        SSE-formatted chunks.
    """
    try:
        async for chunk in llm.generate_stream(message):
            # Format as SSE (Server-Sent Events)
            data = json.dumps({"chunk": chunk})
            yield f"data: {data}\n\n"
        
        # Send completion event
        yield f"data: {json.dumps({'done': True})}\n\n"
    except Exception as e:
        # Send error event
        error_data = json.dumps({"error": str(e)})
        yield f"data: {error_data}\n\n"


@router.post("/message/stream")
async def stream_message(
    payload: MessageRequestDTO,
    request: Request
):
    """
    Stream AI response using Server-Sent Events (SSE).
    
    This endpoint streams the LLM response in real-time as chunks become available,
    providing a better user experience for long responses.
    
    Args:
        payload: The message request DTO.
        request: FastAPI request for correlation ID.
        
    Returns:
        StreamingResponse with SSE-formatted chunks.
    """
    container = get_container()
    llm = container.get_llm()
    
    return StreamingResponse(
        _stream_llm_response(llm, payload.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )

