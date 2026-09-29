import os

import httpx
from anthropic import AsyncAnthropic

AI_PROVIDER = os.getenv("AI_PROVIDER", "anthropic").lower()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
LONGCAT_API_KEY = os.getenv("LONGCAT_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
LONGCAT_MODEL = os.getenv("LONGCAT_MODEL", "LongCat-Flash-Chat")
AI_MAX_TOKENS = int(os.getenv("AI_MAX_TOKENS", "2048"))
LONGCAT_BASE_URL = "https://api.longcat.chat/anthropic/v1/messages"


class AIClient:
    def __init__(self, provider: str | None = None):
        self.provider = (provider or AI_PROVIDER).lower()

    async def complete(
        self,
        prompt: str,
        system: str = "",
        max_tokens: int = AI_MAX_TOKENS,
    ) -> str:
        if self.provider == "anthropic":
            return await self._call_anthropic(prompt, system, max_tokens)
        elif self.provider == "longcat":
            return await self._call_longcat(prompt, system, max_tokens)
        else:
            raise ValueError(
                f"Unknown AI_PROVIDER: '{self.provider}'. Use 'anthropic' or 'longcat'."
            )

    async def _call_anthropic(self, prompt: str, system: str, max_tokens: int) -> str:
        if not ANTHROPIC_API_KEY:
            raise RuntimeError("ANTHROPIC_API_KEY not configured")
        client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
        message = await client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

    async def _call_longcat(self, prompt: str, system: str, max_tokens: int) -> str:
        if not LONGCAT_API_KEY:
            raise RuntimeError("LONGCAT_API_KEY not configured")
        headers = {
            "Authorization": f"Bearer {LONGCAT_API_KEY}",
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": LONGCAT_MODEL,
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": prompt}],
        }
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(LONGCAT_BASE_URL, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["content"][0]["text"]
