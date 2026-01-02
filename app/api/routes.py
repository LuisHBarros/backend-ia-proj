from fastapi import Body, APIRouter
from app.api.schemas import MessageDTO
from app.api.services import service

router = APIRouter()

@router.post("/message")
async def send_message(payload: MessageDTO = Body(...)):
    response = await service.handle(payload.message)
    return {"response": response}
    # Other routes can be added here, e.g. healthcheck

@router.get("/health")
async def health_check():
    return {"status": "ok"}
