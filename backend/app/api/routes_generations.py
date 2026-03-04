import uuid
import json
import asyncio

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db, async_session
from app.models.generation import Generation
from app.schemas.generation import GenerationCreate, GenerationOut
from app.services.generations import create_generation, get_generation, run_generation

router = APIRouter(prefix="/generations", tags=["generations"])


@router.post("", response_model=GenerationOut, status_code=201)
async def api_create_generation(
    body: GenerationCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    try:
        gen = await create_generation(db, body.carousel_id)
    except ValueError as e:
        raise HTTPException(404, str(e))

    background_tasks.add_task(run_generation, gen.id)
    return gen


@router.get("/{generation_id}", response_model=GenerationOut)
async def api_get_generation(generation_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    gen = await get_generation(db, generation_id)
    if not gen:
        raise HTTPException(404, "Generation not found")
    return gen


@router.get("/{generation_id}/stream")
async def stream_generation_status(generation_id: uuid.UUID):
    async def event_generator():
        prev_status = None
        while True:
            async with async_session() as db:
                gen = await db.get(Generation, generation_id)
                if not gen:
                    yield f"data: {json.dumps({'status': 'error', 'error': 'Not found'})}\n\n"
                    return

                if gen.status != prev_status:
                    prev_status = gen.status
                    data = {
                        "status": gen.status,
                        "tokens_used": gen.tokens_used,
                        "error": gen.error,
                    }
                    yield f"data: {json.dumps(data)}\n\n"

                if gen.status in ("done", "failed"):
                    return

            await asyncio.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/by-carousel/{carousel_id}", response_model=list[GenerationOut])
async def api_list_generations(carousel_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Generation)
        .where(Generation.carousel_id == carousel_id)
        .order_by(Generation.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
