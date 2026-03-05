import uuid
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.carousel import Carousel
from app.models.export import Export
from app.models.slide import Slide
from app.models.asset import Asset
from app.services.render import render_carousel_zip
from app.services.assets import upload_file, generate_asset_key
from app.core.db import async_session

logger = logging.getLogger(__name__)


async def create_export(db: AsyncSession, carousel_id: uuid.UUID) -> Export:
    carousel = await db.get(Carousel, carousel_id)
    if not carousel:
        raise ValueError("Carousel not found")

    export = Export(carousel_id=carousel_id, status="queued")
    db.add(export)
    await db.commit()
    await db.refresh(export)
    return export


async def get_export(db: AsyncSession, export_id: uuid.UUID) -> Export | None:
    return await db.get(Export, export_id)


async def run_export(export_id: uuid.UUID) -> None:
    """Background task: render slides to PNG and create ZIP."""
    async with async_session() as db:
        export = await db.get(Export, export_id)
        if not export:
            return

        export.status = "running"
        await db.commit()

        try:
            carousel = await db.get(Carousel, export.carousel_id)
            if not carousel:
                raise ValueError("Carousel not found")

            stmt = select(Slide).where(Slide.carousel_id == carousel.id).order_by(Slide.order)
            result = await db.execute(stmt)
            slides = list(result.scalars().all())

            if not slides:
                raise ValueError("No slides to export")

            carousel_design = dict(carousel.design or {})
            designs = []

            for slide in slides:
                slide_design = dict(slide.design or {})
                effective = {**carousel_design, **slide_design}
                bg_asset_id = effective.get("bg_asset_id")
                if bg_asset_id:
                    try:
                        aid = uuid.UUID(str(bg_asset_id)) if isinstance(bg_asset_id, str) else bg_asset_id
                        asset = await db.get(Asset, aid)
                        if asset:
                            effective["bg_asset_s3_key"] = asset.s3_key
                            effective["bg_asset_content_type"] = asset.content_type or "image/jpeg"
                    except (ValueError, TypeError):
                        pass
                designs.append(effective)

            zip_bytes = await render_carousel_zip(slides, designs)

            s3_key = generate_asset_key("export_zip", "zip")
            upload_file(zip_bytes, s3_key, "application/zip")

            asset = Asset(
                kind="export_zip",
                s3_key=s3_key,
                content_type="application/zip",
                size=len(zip_bytes),
            )
            db.add(asset)
            await db.flush()

            export.status = "done"
            export.zip_asset_id = asset.id
            await db.commit()

            logger.info("Export %s done, zip size %d bytes", export_id, len(zip_bytes))

        except Exception as e:
            logger.error("Export %s failed: %s", export_id, e, exc_info=True)
            export.status = "failed"
            export.error = str(e)[:500]
            await db.commit()
