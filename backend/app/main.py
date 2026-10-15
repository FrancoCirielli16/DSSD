from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import get_settings
from app.routers import api

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description=(
        "API local de RescueSync para gestionar emergencias, lotes, ofertas de ayuda "
        "y la integración con el Sistema Nacional y Bonita."
    ),
    version="1.0.0",
    contact={"name": "Equipo DSSD", "email": "devs@dssd.edu.ar"},
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)
app.add_middleware(
    SessionMiddleware, secret_key=settings.session_secret, same_site="lax", max_age=8 * 3600
)
app.include_router(api.router)
