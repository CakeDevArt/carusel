import uuid

from sqlalchemy import String, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Slide(Base):
    __tablename__ = "slides"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    carousel_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("carousels.id", ondelete="CASCADE"), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    footer: Mapped[str | None] = mapped_column(String(200), nullable=True)
    design: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    carousel = relationship("Carousel", back_populates="slides")
