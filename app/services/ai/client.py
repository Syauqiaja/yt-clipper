"""AI client: HTTP client for 9router OpenAI-compatible API."""

import json
from typing import Any, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config.settings import settings
from app.infrastructure.logging.logger import get_logger

logger = get_logger("ai")


class AIError(Exception):
    """AI API error."""
    pass


class AIClient:
    def __init__(self):
        self.api_key = settings.ninerouter_api_key
        self.base_url = settings.ninerouter_base_url.rstrip("/")
        self.model = settings.ninerouter_model
        self.timeout = settings.ninerouter_timeout

        if not self.api_key:
            raise AIError(
                "NINEROUTER_API_KEY not set. Create a .env file with your API key."
            )

        self.client = httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )

        self.async_client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )

    def __del__(self):
        try:
            self.client.close()
        except Exception:
            pass
        try:
            import asyncio
            try:
                asyncio.get_running_loop()
            except RuntimeError:
                self.async_client.close()
        except Exception:
            pass

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
    )
    def chat_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        response_format: Optional[dict] = None,
    ) -> str:
        """Send a chat completion request to the 9router API."""
        url = f"{self.base_url}/chat/completions"

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        if response_format:
            payload["response_format"] = response_format

        try:
            response = self.client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

        except httpx.TimeoutException as e:
            raise AIError(f"AI API timeout after {self.timeout}s: {e}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AIError("Invalid API key. Check NINEROUTER_API_KEY.")
            elif e.response.status_code == 429:
                raise AIError("Rate limited. Try again later.")
            else:
                raise AIError(f"AI API error {e.response.status_code}: {e}")
        except Exception as e:
            raise AIError(f"AI API request failed: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
    )
    async def chat_completion_async(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        response_format: Optional[dict] = None,
    ) -> str:
        """Send an async chat completion request."""
        url = f"{self.base_url}/chat/completions"

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        if response_format:
            payload["response_format"] = response_format

        try:
            response = await self.async_client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

        except httpx.TimeoutException as e:
            raise AIError(f"AI API timeout after {self.timeout}s: {e}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AIError("Invalid API key. Check NINEROUTER_API_KEY.")
            elif e.response.status_code == 429:
                raise AIError("Rate limited. Try again later.")
            else:
                raise AIError(f"AI API error {e.response.status_code}: {e}")
        except Exception as e:
            raise AIError(f"AI API request failed: {e}")

    def parse_json_response(self, content: str) -> Any:
        """Parse JSON from AI response, handling markdown code blocks."""
        content = content.strip()

        json_match = None
        for marker in ["```json", "```"]:
            if marker in content:
                start = content.find(marker) + len(marker)
                end = content.find("```", start)
                if end > start:
                    json_match = content[start:end].strip()
                    break

        text_to_parse = json_match or content

        try:
            return json.loads(text_to_parse)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse AI response as JSON: {e}")
            logger.debug(f"Raw AI response: {content}")
            raise AIError(f"Failed to parse AI response: {e}")

    def health_check(self) -> bool:
        """Check if the AI API is accessible."""
        try:
            response = self.client.get(f"{self.base_url}/models")
            return response.status_code == 200
        except Exception:
            return False
