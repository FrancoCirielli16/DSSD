from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.deps import require_role
from app.core.templating import templates
from app.db import get_db
from app.models import Gravedad, Rol, Usuario
from app.schemas import mensaje_de_error
from app.schemas.emergencias import ETIQUETAS, EmergenciaIn
from app.services.emergencias import (
    AltaEmergenciaError,
    emergencia_visible,
    emergencias_visibles,
    registrar_emergencia,
)

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
    try:
        datos = EmergenciaIn(
            tipo=tipo, nivel_gravedad=nivel_gravedad, zona_afectada=zona_afectada, descripcion=descripcion
        )
    except ValidationError as exc:
        return _form(request, mensaje_de_error(exc, ETIQUETAS), status_code=400)

    try:
        emergencia = registrar_emergencia(db, settings, operador=user, **datos.model_dump())
    except AltaEmergenciaError as exc:
        return _form(request, str(exc), status_code=502)

    # 303 → GET: si el usuario recarga, no se reenvía el formulario (evita emergencia y caso duplicados).
    return RedirectResponse(f"/emergencias/{emergencia.id}?nueva=1", status_code=303)


@router.get("/emergencias", response_class=HTMLResponse)
def listar_emergencias(
    request: Request, user: Usuario = Depends(require_role()), db: Session = Depends(get_db)
):
    return templates.TemplateResponse(
        request, "emergencias_lista.html", {"user": user, "emergencias": emergencias_visibles(db, user)}
    )


@router.get("/emergencias/{emergencia_id:int}", response_class=HTMLResponse)
def ver_emergencia(
    request: Request,
    emergencia_id: int,
    nueva: bool = False,
    error: str | None = None,
    user: Usuario = Depends(require_role()),
    db: Session = Depends(get_db),
):
    emergencia = emergencia_visible(db, user, emergencia_id)
    if emergencia is None:
        raise HTTPException(status_code=404, detail="Emergencia no encontrada")
    return templates.TemplateResponse(
        request, "emergencia_detalle.html", {"user": user, "e": emergencia, "nueva": nueva, "error": error}
    )
