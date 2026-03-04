import uuid
from datetime import datetime

from sqlalchemy import String, Integer, Text, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Carousel(Base):
    __tablename__ = "carousels"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    source_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    language: Mapped[str] = mapped_column(String(5), nullable=False, default="en")
    slides_count: Mapped[int] = mapped_column(Integer, nullable=False, default=6)
    style_hint: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    design: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    preview_asset_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    slides = relationship("Slide", back_populates="carousel", cascade="all, delete-orphan", order_by="Slide.order")
