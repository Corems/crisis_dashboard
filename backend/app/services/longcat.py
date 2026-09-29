import httpx

BASE_URL = "https://api.longcat.chat/anthropic"
ENDPOINT = "/v1/messages"


async def call_longcat(
    *,
    api_key: str,
    model: str,
    system: str,
    messages: list[dict],
    max_tokens: int = 2048,
) -> dict:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "system": system,
        "messages": messages,
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{BASE_URL}{ENDPOINT}",
            headers=headers,
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()
