from fastapi import FastAPI

from app.config import get_settings
from app.routers import adjudicacion, catalogo, cierre, inventario, validacion


app = FastAPI(
    title=get_settings().app_name,
    description=(
        "API del Sistema Nacional para administrar el catálogo de recursos, inventario "
        "de ONGs, validación, adjudicación transaccional y cierres operativos."
    ),
    version="1.0.0",
    contact={"name": "Equipo DSSD", "email": "devs@dssd.edu.ar"},
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.include_router(catalogo.router)
app.include_router(inventario.router)
app.include_router(validacion.router)
app.include_router(cierre.router)
app.include_router(adjudicacion.router, prefix="/adjudicaciones", tags=["Adjudicaciones"])

@app.get(
    "/health",
    tags=["Health"],
    summary="Verificar disponibilidad del Sistema Nacional",
    description="Devuelve un estado simple para healthchecks y monitoreo.",
    responses={200: {"description": "Servicio disponible"}},
)
def health() -> dict[str, str]:
    return {"estado": "ok"}
