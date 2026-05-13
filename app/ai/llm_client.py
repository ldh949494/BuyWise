class LLMClient:
    """Mock-first LLM client wrapper for later provider replacement."""

    def generate_reply(self, user_query: str) -> str:
        return f"Mock shopping guidance for: {user_query}"
