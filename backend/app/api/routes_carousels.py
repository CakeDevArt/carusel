import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.carousel import (
    CarouselCreate, CarouselUpdate, CarouselOut, DesignUpdate,
)
from app.schemas.slide import SlideOut, SlideUpdate, SlideCreate, SlideReorder
from app.services.carousels import (
    list_carousels, get_carousel, create_carousel, update_carousel, delete_carousel,
    get_slides, get_slide, update_slide, create_slide, delete_slide, reorder_slides,
)

router = APIRouter(prefix="/carousels", tags=["carousels"])


@router.get("", response_model=list[CarouselOut])
async def api_list_carousels(
    status: str | None = None,
    lang: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await list_carousels(db, status=status, lang=lang)


@router.get("/{carousel_id}", response_model=CarouselOut)
async def api_get_carousel(carousel_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    c = await get_carousel(db, carousel_id)
    if not c:
        raise HTTPException(404, "Carousel not found")
    return c


@router.post("", response_model=CarouselOut, status_code=201)
async def api_create_carousel(body: CarouselCreate, db: AsyncSession = Depends(get_db)):
    return await create_carousel(
        db,
        title=body.title,
        source_type=body.source_type,
        source_payload=body.source_payload,
        slides_count=body.format.slides_count,
        language=body.format.language,
        style_hint=body.format.style_hint,
    )


@router.patch("/{carousel_id}", response_model=CarouselOut)
async def api_update_carousel(
    carousel_id: uuid.UUID,
    body: CarouselUpdate,
    db: AsyncSession = Depends(get_db),
):
    c = await get_carousel(db, carousel_id)
    if not c:
        raise HTTPException(404, "Carousel not found")

    kwargs = {}
    if body.title is not None:
        kwargs["title"] = body.title
    if body.format is not None:
        if body.format.slides_count is not None:
            kwargs["slides_count"] = body.format.slides_count
        if body.format.language is not None:
            kwargs["language"] = body.format.language
        if body.format.style_hint is not None:
            kwargs["style_hint"] = body.format.style_hint
    return await update_carousel(db, c, **kwargs)


@router.delete("/{carousel_id}", status_code=204)
async def api_delete_carousel(carousel_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    c = await get_carousel(db, carousel_id)
    if not c:
        raise HTTPException(404, "Carousel not found")
    await delete_carousel(db, c)


@router.patch("/{carousel_id}/design", response_model=CarouselOut)
async def api_update_design(
    carousel_id: uuid.UUID,
    body: DesignUpdate,
    db: AsyncSession = Depends(get_db),
):
    c = await get_carousel(db, carousel_id)
    if not c:
        raise HTTPException(404, "Carousel not found")
    return await update_carousel(db, c, design=body.design.model_dump())


@router.get("/{carousel_id}/slides", response_model=list[SlideOut])
async def api_get_slides(carousel_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await get_slides(db, carousel_id)


@router.post("/{carousel_id}/slides", response_model=SlideOut, status_code=201)
async def api_create_slide(
    carousel_id: uuid.UUID,
    body: SlideCreate,
    db: AsyncSession = Depends(get_db),
):
    c = await get_carousel(db, carousel_id)
    if not c:
        raise HTTPException(404, "Carousel not found")
    return await create_slide(
        db, carousel_id=carousel_id,
        title=body.title, body=body.body, footer=body.footer,
    )


@router.patch("/{carousel_id}/slides/{slide_id}", response_model=SlideOut)
async def api_update_slide(
    carousel_id: uuid.UUID,
    slide_id: uuid.UUID,
    body: SlideUpdate,
    db: AsyncSession = Depends(get_db),
):
    slide = await get_slide(db, slide_id)
    if not slide or slide.carousel_id != carousel_id:
        raise HTTPException(404, "Slide not found")

    kwargs = {}
    if body.title is not None:
        kwargs["title"] = body.title
    if body.body is not None:
        kwargs["body"] = body.body
    if body.footer is not None:
        kwargs["footer"] = body.footer
    if body.design is not None:
        kwargs["design"] = body.design
    return await update_slide(db, slide, **kwargs)


@router.delete("/{carousel_id}/slides/{slide_id}", status_code=204)
async def api_delete_slide(
    carousel_id: uuid.UUID,
    slide_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    slide = await get_slide(db, slide_id)
    if not slide or slide.carousel_id != carousel_id:
        raise HTTPException(404, "Slide not found")
    await delete_slide(db, slide)


@router.post("/{carousel_id}/slides/reorder", response_model=list[SlideOut])
async def api_reorder_slides(
    carousel_id: uuid.UUID,
    body: SlideReorder,
    db: AsyncSession = Depends(get_db),
):
    c = await get_carousel(db, carousel_id)
    if not c:
        raise HTTPException(404, "Carousel not found")
    return await reorder_slides(db, carousel_id, body.slide_ids)
