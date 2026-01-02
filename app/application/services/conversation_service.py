from app.domain.ports.llm_port import LLMPort


class ConversationService:
    def __init__(self, llm: LLMPort):
        self.llm = llm

    async def handle(self, message: str) -> str:
        return await self.llm.generate(message)
