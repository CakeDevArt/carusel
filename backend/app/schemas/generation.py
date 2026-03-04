from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class GenerationCreate(BaseModel):
    carousel_id: uuid.UUID


class GenerationOut(BaseModel):
    id: uuid.UUID
    carousel_id: uuid.UUID
    status: str
    provider: str
    model: str
    tokens_est: int
    tokens_used: Optional[int]
    cost_usd: Optional[float]
    result: Optional[dict]
    error: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
