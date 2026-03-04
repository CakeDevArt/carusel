import uuid
from datetime import datetime

from sqlalchemy import String, Integer, Text, Numeric, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Generation(Base):
    __tablename__ = "generations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    carousel_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("carousels.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="queued")
    provider: Mapped[str] = mapped_column(String(100), nullable=False, default="openai")
    model: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    tokens_est: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_usd: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
