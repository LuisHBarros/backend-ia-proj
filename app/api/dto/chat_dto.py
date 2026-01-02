"""Data Transfer Objects for chat API."""
from pydantic import BaseModel, Field
from typing import Optional


class MessageRequestDTO(BaseModel):
    """DTO for message request."""
    message: str = Field(..., min_length=1, description="The message content")
    user_id: Optional[str] = Field(None, description="User identifier")
    conversation_id: Optional[str] = Field(None, description="Conversation ID to continue")


class MessageResponseDTO(BaseModel):
    """DTO for message response."""
    conversation_id: str = Field(..., description="The conversation identifier")
    response: str = Field(..., description="The generated response")
    user_message: str = Field(..., description="The user's message")
    assistant_message: str = Field(..., description="The assistant's response")

