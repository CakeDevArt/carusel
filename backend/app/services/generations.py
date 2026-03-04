import uuid
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.carousel import Carousel
from app.models.generation import Generation
from app.models.slide import Slide
from app.services.llm_client import generate_slides
from app.utils.tokens import estimate_tokens
from app.core.config import settings
from app.core.db import async_session

logger = logging.getLogger(__name__)


async def create_generation(db: AsyncSession, carousel_id: uuid.UUID) -> Generation:
    carousel = await db.get(Carousel, carousel_id)
    if not carousel:
        raise ValueError("Carousel not found")

    source_text = carousel.source_payload.get("text", "")
    tokens_est = estimate_tokens(source_text, carousel.slides_count)

    gen = Generation(
        carousel_id=carousel_id,
        status="queued",
        provider="openai",
        model=settings.LLM_MODEL,
        tokens_est=tokens_est,
    )
    db.add(gen)
    await db.commit()
    await db.refresh(gen)
    return gen


async def get_generation(db: AsyncSession, generation_id: uuid.UUID) -> Generation | None:
    return await db.get(Generation, generation_id)


async def run_generation(generation_id: uuid.UUID) -> None:
    """Background task: run LLM generation and save slides."""
    async with async_session() as db:
        gen = await db.get(Generation, generation_id)
        if not gen:
            return

        carousel = await db.get(Carousel, gen.carousel_id)
        if not carousel:
            gen.status = "failed"
            gen.error = "Carousel not found"
            await db.commit()
            return

        gen.status = "running"
        carousel.status = "generating"
        await db.commit()

        try:
            source_text = carousel.source_payload.get("text", "")
            output, tokens_used = await generate_slides(
                source_text=source_text,
                language=carousel.language,
                slides_count=carousel.slides_count,
                style_hint=carousel.style_hint,
            )

            stmt = select(Slide).where(Slide.carousel_id == carousel.id)
            result = await db.execute(stmt)
            old_slides = result.scalars().all()
            for s in old_slides:
                await db.delete(s)

            for slide_data in output.slides:
                slide = Slide(
                    carousel_id=carousel.id,
                    order=slide_data.order,
                    title=slide_data.title,
                    body=slide_data.body,
                    footer=slide_data.footer,
                )
                db.add(slide)

            gen.status = "done"
            gen.tokens_used = tokens_used
            gen.result = {"slides": [s.model_dump() for s in output.slides]}
            carousel.status = "ready"
            await db.commit()

            logger.info("Generation %s done, %d slides created", generation_id, len(output.slides))

        except Exception as e:
            logger.error("Generation %s failed: %s", generation_id, e, exc_info=True)
            gen.status = "failed"
            gen.error = str(e)[:500]
            carousel.status = "failed"
            await db.commit()
