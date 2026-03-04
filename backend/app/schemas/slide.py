from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, Field


class SlideCreate(BaseModel):
    title: str = Field(default="", max_length=200)
    body: str = Field(default="")
    footer: Optional[str] = Field(None, max_length=200)


class SlideUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    body: Optional[str] = None
    footer: Optional[str] = Field(None, max_length=200)


class SlideReorder(BaseModel):
    slide_ids: list[uuid.UUID]


class SlideOut(BaseModel):
    id: uuid.UUID
    carousel_id: uuid.UUID
    order: int
    title: str
    body: str
    footer: Optional[str]

    model_config = {"from_attributes": True}
