from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CarouselFormat(BaseModel):
    slides_count: int = Field(ge=6, le=10, default=6)
    language: str = Field(pattern="^(ru|en)$", default="en")
    style_hint: Optional[str] = None


class CarouselCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    source_type: str = Field(pattern="^(text|video)$")
    source_payload: dict = Field(default_factory=dict)
    format: CarouselFormat = Field(default_factory=CarouselFormat)


class CarouselUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    format: Optional[CarouselFormat] = None


class DesignSettings(BaseModel):
    template: Optional[str] = "classic"
    bg_color: Optional[str] = "#ffffff"
    bg_asset_id: Optional[str] = None
    bg_dim: Optional[float] = Field(0.0, ge=0.0, le=0.7)
    padding: Optional[int] = Field(40, ge=10, le=100)
    align_h: Optional[str] = "left"
    align_v: Optional[str] = "top"
    header_enabled: Optional[bool] = False
    header_text: Optional[str] = ""
    footer_enabled: Optional[bool] = False
    footer_text: Optional[str] = ""


class DesignUpdate(BaseModel):
    design: DesignSettings
    apply_to_all: bool = True


class CarouselOut(BaseModel):
    id: uuid.UUID
    title: str
    source_type: str
    source_payload: dict
    language: str
    slides_count: int
    style_hint: Optional[str]
    status: str
    design: Optional[dict]
    preview_asset_id: Optional[uuid.UUID]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
