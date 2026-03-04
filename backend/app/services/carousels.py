import uuid
import logging

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.carousel import Carousel
from app.models.slide import Slide

logger = logging.getLogger(__name__)


async def list_carousels(
    db: AsyncSession,
    status: str | None = None,
    lang: str | None = None,
) -> list[Carousel]:
    stmt = select(Carousel).order_by(Carousel.created_at.desc())
    if status:
        stmt = stmt.where(Carousel.status == status)
    if lang:
        stmt = stmt.where(Carousel.language == lang)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_carousel(db: AsyncSession, carousel_id: uuid.UUID) -> Carousel | None:
    stmt = select(Carousel).options(selectinload(Carousel.slides)).where(Carousel.id == carousel_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_carousel(
    db: AsyncSession,
    title: str,
    source_type: str,
    source_payload: dict,
    slides_count: int,
    language: str,
    style_hint: str | None,
) -> Carousel:
    carousel = Carousel(
        title=title,
        source_type=source_type,
        source_payload=source_payload,
        slides_count=slides_count,
        language=language,
        style_hint=style_hint,
        status="draft",
    )
    db.add(carousel)
    await db.commit()
    await db.refresh(carousel)
    return carousel


async def update_carousel(
    db: AsyncSession,
    carousel: Carousel,
    **kwargs,
) -> Carousel:
    for key, value in kwargs.items():
        if value is not None:
            setattr(carousel, key, value)
    await db.commit()
    await db.refresh(carousel)
    return carousel


async def delete_carousel(db: AsyncSession, carousel: Carousel) -> None:
    await db.delete(carousel)
    await db.commit()
    logger.info("Carousel %s deleted", carousel.id)


async def get_slides(db: AsyncSession, carousel_id: uuid.UUID) -> list[Slide]:
    stmt = select(Slide).where(Slide.carousel_id == carousel_id).order_by(Slide.order)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_slide(db: AsyncSession, slide_id: uuid.UUID) -> Slide | None:
    stmt = select(Slide).where(Slide.id == slide_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_slide(db: AsyncSession, slide: Slide, **kwargs) -> Slide:
    for key, value in kwargs.items():
        if value is not None:
            setattr(slide, key, value)
    await db.commit()
    await db.refresh(slide)
    return slide


async def create_slide(
    db: AsyncSession,
    carousel_id: uuid.UUID,
    title: str = "",
    body: str = "",
    footer: str | None = None,
) -> Slide:
    stmt = select(func.coalesce(func.max(Slide.order), 0)).where(Slide.carousel_id == carousel_id)
    result = await db.execute(stmt)
    max_order = result.scalar() or 0

    slide = Slide(
        carousel_id=carousel_id,
        order=max_order + 1,
        title=title,
        body=body,
        footer=footer,
    )
    db.add(slide)
    await db.commit()
    await db.refresh(slide)
    logger.info("Slide created in carousel %s, order %d", carousel_id, slide.order)
    return slide


async def delete_slide(db: AsyncSession, slide: Slide) -> None:
    carousel_id = slide.carousel_id
    order = slide.order
    await db.delete(slide)

    stmt = select(Slide).where(
        Slide.carousel_id == carousel_id, Slide.order > order
    ).order_by(Slide.order)
    result = await db.execute(stmt)
    for s in result.scalars().all():
        s.order -= 1

    await db.commit()
    logger.info("Slide deleted from carousel %s", carousel_id)


async def reorder_slides(
    db: AsyncSession,
    carousel_id: uuid.UUID,
    slide_ids: list[uuid.UUID],
) -> list[Slide]:
    stmt = select(Slide).where(Slide.carousel_id == carousel_id)
    result = await db.execute(stmt)
    slides_map = {s.id: s for s in result.scalars().all()}

    for i, sid in enumerate(slide_ids):
        if sid in slides_map:
            slides_map[sid].order = i + 1

    await db.commit()

    stmt = select(Slide).where(Slide.carousel_id == carousel_id).order_by(Slide.order)
    result = await db.execute(stmt)
    return list(result.scalars().all())
