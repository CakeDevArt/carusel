from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


class ApiKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not settings.APP_API_KEY:
            return await call_next(request)

        if request.url.path in ("/health", "/docs", "/openapi.json", "/redoc"):
            return await call_next(request)

        key = request.headers.get("X-API-Key", "")
        if key != settings.APP_API_KEY:
            raise HTTPException(status_code=401, detail="Invalid API key")

        return await call_next(request)
