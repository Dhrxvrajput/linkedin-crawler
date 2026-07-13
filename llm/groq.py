from typing import Any, Optional

from groq import AsyncGroq, Groq

from config.settings import get_settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

JSON_SYSTEM_PROMPT = "You are a helpful assistant. Always respond with valid JSON only, no markdown fences."


class GroqClient:
    def __init__(self):
        settings = get_settings()
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY not set in environment")
        self.api_key = settings.groq_api_key
        self.model = settings.groq_model
        self.temperature = settings.groq_temperature
        self.max_tokens = settings.groq_max_tokens
        self._sync_client: Groq | None = None
        self._async_client: AsyncGroq | None = None

    @property
    def sync(self) -> Groq:
        if self._sync_client is None:
            self._sync_client = Groq(api_key=self.api_key)
        return self._sync_client

    @property
    def async_(self) -> AsyncGroq:
        if self._async_client is None:
            self._async_client = AsyncGroq(api_key=self.api_key)
        return self._async_client

    def _build_messages(self, prompt: str, system_instruction: Optional[str] = None) -> list[dict]:
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        return messages

    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        import time
        messages = self._build_messages(prompt, system_instruction)
        try:
            response = self.sync.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            result = response.choices[0].message.content or ""
            
            # Safe Sleep: We must wait to stay under the 5 RPM limit
            time.sleep(12.0)
            
            return result
        except Exception as e:
            logger.error("Groq generation failed: %s", e)
            raise

    def generate_json(self, prompt: str, system_instruction: Optional[str] = None) -> dict[str, Any]:
        from utils.helpers import safe_json_loads

        system = system_instruction or JSON_SYSTEM_PROMPT
        text = self.generate(prompt, system_instruction=system)
        result = safe_json_loads(text, default={})
        if not result:
            logger.warning("Failed to parse JSON from Groq response")
        return result

    async def generate_async(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        import asyncio
        import random
        
        messages = self._build_messages(prompt, system_instruction)
        max_retries = 5
        base_delay = 2.0
        
        for attempt in range(max_retries):
            try:
                response = await self.async_.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
                return response.choices[0].message.content or ""
            except Exception as e:
                err_msg = str(e)
                # Only retry on 429 (Rate Limit) or some 5xx errors
                is_rate_limit = "429" in err_msg or "rate_limit_exceeded" in err_msg.lower()
                
                if is_rate_limit and attempt < max_retries - 1:
                    wait_time = (base_delay * (2 ** attempt)) + random.uniform(0, 1.0)
                    logger.warning(
                        "Rate limit (429) on attempt %d. Retrying in %.2fs...",
                        attempt + 1, wait_time
                    )
                    await asyncio.sleep(wait_time)
                    continue
                
                # For other errors or if we ran out of retries, log and re-raise
                logger.error("Groq async generation failed: %s", e)
                raise

    async def generate_json_async(self, prompt: str, system_instruction: Optional[str] = None) -> dict[str, Any]:
        from utils.helpers import safe_json_loads

        system = system_instruction or JSON_SYSTEM_PROMPT
        text = await self.generate_async(prompt, system_instruction=system)
        result = safe_json_loads(text, default={})
        if not result:
            logger.warning("Failed to parse JSON from Groq async response")
        return result


def get_llm_client() -> GroqClient:
    return GroqClient()
