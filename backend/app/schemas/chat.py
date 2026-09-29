from typing import Literal

from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    model: str = "LongCat-Flash-Chat"
    max_tokens: int = 2048


class ChatResponse(BaseModel):
    content: str
    model: str
    input_tokens: int
    output_tokens: int
