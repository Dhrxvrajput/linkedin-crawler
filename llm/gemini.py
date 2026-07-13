import json
from typing import Any, Optional
from google import genai
from config.settings import get_settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

JSON_SYSTEM_PROMPT = "You are a helpful assistant. Always respond with valid JSON only, no markdown fences."

class GeminiClient:
    def __init__(self):
        settings = get_settings()
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY not set in environment")
        
        self.client = genai.Client(api_key=settings.google_api_key)
        # Using the model name from settings (user requested gemini-3.5-flash)
        self.model_name = settings.google_model or "gemini-2.0-flash"
        self.temperature = settings.google_temperature

    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        try:
            config = {
                "temperature": self.temperature,
                "system_instruction": system_instruction or "",
            }
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )
            result = response.text or ""
            
            # Safe Sleep: Stay under the 5 RPM limit
            import asyncio
            import time
            time.sleep(12.0)
            
            return result
        except Exception as e:
            logger.error("Gemini (modern) generation failed: %s", e)
            raise

    def generate_json(self, prompt: str, system_instruction: Optional[str] = None) -> dict[str, Any]:
        from utils.helpers import safe_json_loads
        
        try:
            config = {
                "temperature": self.temperature,
                "system_instruction": system_instruction or JSON_SYSTEM_PROMPT,
                "response_mime_type": "application/json",
            }
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )
            return safe_json_loads(response.text, default={})
        except Exception as e:
            logger.error("Gemini (modern) JSON generation failed: %s", e)
            return {}

    async def generate_async(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        import asyncio
        import random
        
        max_retries = 3
        base_delay = 2.0
        
        config = {
            "temperature": self.temperature,
            "system_instruction": system_instruction or "",
        }
        
        for attempt in range(max_retries):
            try:
                response = await self.client.aio.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=config
                )
                return response.text
            except Exception as e:
                err_msg = str(e)
                if ("429" in err_msg or "resource_exhausted" in err_msg.lower()) and attempt < max_retries - 1:
                    wait_time = (base_delay * (2 ** attempt)) + random.uniform(0, 1.0)
                    logger.warning("Gemini modern Rate limit hit. Retrying in %.2fs...", wait_time)
                    await asyncio.sleep(wait_time)
                    continue
                logger.error("Gemini modern async generation failed: %s", e)
                raise

    async def generate_json_async(self, prompt: str, system_instruction: Optional[str] = None) -> dict[str, Any]:
        from utils.helpers import safe_json_loads
        
        config = {
            "temperature": self.temperature,
            "system_instruction": system_instruction or JSON_SYSTEM_PROMPT,
            "response_mime_type": "application/json",
        }
        
        import asyncio
        import random
        
        max_retries = 3
        base_delay = 2.0
        
        for attempt in range(max_retries):
            try:
                response = await self.client.aio.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=config
                )
                return safe_json_loads(response.text, default={})
            except Exception as e:
                err_msg = str(e)
                if ("429" in err_msg or "resource_exhausted" in err_msg.lower()) and attempt < max_retries - 1:
                    wait_time = (base_delay * (2 ** attempt)) + random.uniform(0, 1.0)
                    await asyncio.sleep(wait_time)
                    continue
                logger.error("Gemini modern JSON async generation failed: %s", e)
                return {}
