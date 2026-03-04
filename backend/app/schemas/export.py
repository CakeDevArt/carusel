from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ExportCreate(BaseModel):
    carousel_id: uuid.UUID


class ExportOut(BaseModel):
    id: uuid.UUID
    carousel_id: uuid.UUID
    status: str
    zip_asset_id: Optional[uuid.UUID]
    url: Optional[str] = None
    error: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
