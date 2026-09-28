import logging
from contextlib import asynccontextmanager

import requests
from fastapi import FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import get_settings
from app.core.templating import BASE_DIR, templates
from app.routers import api, auth, emergencias, lotes, pages
from app.integrations.bonita import BonitaError
from app.services.bonita_users import sincronizar_usuarios_existentes

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.bonita_sync_on_startup:
        try:
            sincronizar_usuarios_existentes(settings)
        except (BonitaError, requests.RequestException):
            logger.exception("No se pudieron sincronizar los usuarios de RescueSync con Bonita")
    yield

app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    SessionMiddleware, secret_key=settings.session_secret, same_site="lax", max_age=8 * 3600
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.include_router(api.router)
app.include_router(auth.router)
app.include_router(emergencias.router)
app.include_router(lotes.router)
app.include_router(pages.router)


@app.exception_handler(StarletteHTTPException)
async def http_error(request: Request, exc: StarletteHTTPException):
    """Páginas: 401 → login, 403/404 → pantalla de aviso. /api/* mantiene JSON."""
    if request.url.path.startswith("/api") or exc.status_code not in (401, 403, 404):
        return await http_exception_handler(request, exc)
    if exc.status_code == 401:
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse(
        request, "forbidden.html", {"detail": exc.detail}, status_code=exc.status_code
    )
