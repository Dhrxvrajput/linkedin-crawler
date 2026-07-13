from config.settings import get_settings
from typing import Any

def get_llm_client() -> Any:
    settings = get_settings()
    provider = settings.llm_provider.lower()
    
    if provider == "google":
        from llm.gemini import GeminiClient
        return GeminiClient()
    else:
        from llm.groq import GroqClient
        return GroqClient()
