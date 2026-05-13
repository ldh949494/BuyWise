from app.ai.llm_client import LLMClient


class GuideService:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()

    def build_text_reply(self, user_query: str) -> str:
        return self.llm_client.generate_reply(user_query)
