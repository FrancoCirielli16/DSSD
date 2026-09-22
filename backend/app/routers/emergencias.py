from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.deps import require_role
from app.core.templating import templates
from app.db import get_db
from app.models import Gravedad, Rol, Usuario
from app.services.emergencias import AltaEmergenciaError, registrar_emergencia

router = APIRouter()


def _form(request: Request, error: str | None = None, status_code: int = 200):
    return templates.TemplateResponse(
        request, "emergencia_form.html", {"gravedades": list(Gravedad), "error": error},
        status_code=status_code,
    )


@router.get("/emergencias/nueva", response_class=HTMLResponse)
def nueva_emergencia_form(request: Request, user: Usuario = Depends(require_role(Rol.MUNICIPIO))):
    return _form(request)


@router.post("/emergencias/nueva", response_class=HTMLResponse)
def crear_emergencia(
    request: Request,
    tipo: str = Form(""),
    nivel_gravedad: str = Form(""),
    zona_afectada: str = Form(""),
    descripcion: str = Form(""),
    user: Usuario = Depends(require_role(Rol.MUNICIPIO)),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    tipo, zona_afectada, descripcion = tipo.strip(), zona_afectada.strip(), descripcion.strip()
    if not (tipo and zona_afectada and descripcion):
        return _form(request, "Completá todos los campos.", status_code=400)
    try:
        gravedad = Gravedad(nivel_gravedad)
    except ValueError:
        return _form(request, "Nivel de gravedad inválido.", status_code=400)

    try:
        emergencia = registrar_emergencia(
            db, settings, operador=user, tipo=tipo, nivel_gravedad=gravedad,
            zona_afectada=zona_afectada, descripcion=descripcion,
        )
    except AltaEmergenciaError as exc:
        return _form(request, str(exc), status_code=502)

    return templates.TemplateResponse(request, "emergencia_creada.html", {"emergencia": emergencia})
