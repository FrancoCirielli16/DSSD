from fastapi import FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import get_settings
from app.core.templating import BASE_DIR, templates
from app.routers import auth, pages

settings = get_settings()

app = FastAPI(title=settings.app_name)
app.add_middleware(
    SessionMiddleware, secret_key=settings.session_secret, same_site="lax", max_age=8 * 3600
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.include_router(auth.router)
app.include_router(pages.router)


@app.exception_handler(StarletteHTTPException)
async def http_error(request: Request, exc: StarletteHTTPException):
    """Páginas: 401 → login, 403 → pantalla de acceso denegado. /api/* mantiene JSON."""
    if request.url.path.startswith("/api") or exc.status_code not in (401, 403):
        return await http_exception_handler(request, exc)
    if exc.status_code == 401:
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse(request, "forbidden.html", {"detail": exc.detail}, status_code=403)
