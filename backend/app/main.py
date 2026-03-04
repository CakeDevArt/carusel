from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.logging import setup_logging
from app.core.security import ApiKeyMiddleware
from app.core.middleware import RequestIdMiddleware
from app.api.routes_carousels import router as carousels_router
from app.api.routes_generations import router as generations_router
from app.api.routes_exports import router as exports_router
from app.api.routes_assets import router as assets_router

setup_logging()

app = FastAPI(title="Carousel Generator API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ApiKeyMiddleware)
app.add_middleware(RequestIdMiddleware)

app.include_router(carousels_router)
app.include_router(generations_router)
app.include_router(exports_router)
app.include_router(assets_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
