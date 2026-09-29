import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import get_session
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    session: AsyncSession = Depends(get_session),
):
    from app.services.longcat import call_longcat
    from app.services.macro_context import build_system_prompt

    api_key = os.getenv("LONGCAT_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=500, detail="LONGCAT_API_KEY not configured")

    system_prompt = await build_system_prompt(session)
    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    try:
        resp = await call_longcat(
            api_key=api_key,
            model=request.model,
            system=system_prompt,
            messages=messages,
            max_tokens=request.max_tokens,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LongCat API error: {e}") from e

    content = resp.get("content", [{}])
    text = content[0].get("text", "") if content else ""
    usage = resp.get("usage", {})

    return ChatResponse(
        content=text,
        model=resp.get("model", request.model),
        input_tokens=usage.get("input_tokens", 0),
        output_tokens=usage.get("output_tokens", 0),
    )
