from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AssetOut(BaseModel):
    id: uuid.UUID
    kind: str
    s3_key: str
    content_type: str
    size: Optional[int]
    url: str
    created_at: datetime

    model_config = {"from_attributes": True}
