import uuid
import json
import asyncio

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db, async_session
from app.core.config import settings
from app.models.export import Export
from app.schemas.export import ExportCreate, ExportOut
from app.services.exports import create_export, get_export, run_export

router = APIRouter(prefix="/exports", tags=["exports"])


@router.post("", response_model=ExportOut, status_code=201)
async def api_create_export(
    body: ExportCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    try:
        export = await create_export(db, body.carousel_id)
    except ValueError as e:
        raise HTTPException(404, str(e))

    background_tasks.add_task(run_export, export.id)
    return export


@router.get("/{export_id}", response_model=ExportOut)
async def api_get_export(export_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    export = await get_export(db, export_id)
    if not export:
        raise HTTPException(404, "Export not found")

    out = ExportOut.model_validate(export)
    if export.zip_asset_id:
        out.url = f"{settings.BACKEND_PUBLIC_URL}/assets/{export.zip_asset_id}"
    return out


@router.get("/{export_id}/stream")
async def stream_export_status(export_id: uuid.UUID):
    async def event_generator():
        prev_status = None
        while True:
            async with async_session() as db:
                export = await db.get(Export, export_id)
                if not export:
                    yield f"data: {json.dumps({'status': 'error', 'error': 'Not found'})}\n\n"
                    return

                if export.status != prev_status:
                    prev_status = export.status
                    url = ""
                    if export.zip_asset_id:
                        url = f"{settings.BACKEND_PUBLIC_URL}/assets/{export.zip_asset_id}"
                    data = {
                        "status": export.status,
                        "url": url,
                        "error": export.error,
                    }
                    yield f"data: {json.dumps(data)}\n\n"

                if export.status in ("done", "failed"):
                    return

            await asyncio.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
