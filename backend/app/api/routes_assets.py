import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.config import settings
from app.models.asset import Asset
from app.services.assets import upload_file as s3_upload, get_file_stream, generate_asset_key
from app.schemas.asset import AssetOut

router = APIRouter(prefix="/assets", tags=["assets"])


@router.post("/upload", response_model=AssetOut, status_code=201)
async def api_upload_asset(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    content = await file.read()
    ext = (file.filename or "bin").rsplit(".", 1)[-1] if file.filename else "bin"
    kind = "bg"
    if file.content_type and "video" in file.content_type:
        kind = "video"

    key = generate_asset_key(kind, ext)
    s3_upload(content, key, file.content_type or "application/octet-stream")

    asset = Asset(
        kind=kind,
        s3_key=key,
        content_type=file.content_type or "application/octet-stream",
        size=len(content),
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)

    return AssetOut(
        id=asset.id,
        kind=asset.kind,
        s3_key=asset.s3_key,
        content_type=asset.content_type,
        size=asset.size,
        url=f"{settings.BACKEND_PUBLIC_URL}/assets/{asset.id}",
        created_at=asset.created_at,
    )


@router.get("/{asset_id}")
async def api_get_asset(
    asset_id: uuid.UUID,
    inline: bool = False,
    db: AsyncSession = Depends(get_db),
):
    asset = await db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(404, "Asset not found")

    try:
        body, content_type, size = get_file_stream(asset.s3_key)
    except Exception:
        raise HTTPException(404, "File not found in storage")

    filename = asset.s3_key.rsplit("/", 1)[-1]
    disposition = "inline" if (inline or content_type.startswith("image/")) else f'attachment; filename="{filename}"'
    return StreamingResponse(
        body,
        media_type=content_type,
        headers={
            "Content-Disposition": disposition,
            "Cache-Control": "public, max-age=3600",
        },
    )
