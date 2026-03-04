from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class LLMSlide(BaseModel):
    order: int
    title: str = Field(max_length=40)
    body: str = Field(max_length=320)
    footer: Optional[str] = Field(None, max_length=60)

    @field_validator("title")
    @classmethod
    def truncate_title(cls, v: str) -> str:
        return v[:40] if v else v

    @field_validator("body")
    @classmethod
    def truncate_body(cls, v: str) -> str:
        return v[:320] if v else v

    @field_validator("footer")
    @classmethod
    def truncate_footer(cls, v: str | None) -> str | None:
        if v:
            return v[:60]
        return v


class LLMOutput(BaseModel):
    slides: list[LLMSlide]
