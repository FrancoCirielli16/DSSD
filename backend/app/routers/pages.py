from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from app.core.deps import require_role
from app.core.templating import templates
from app.models import Usuario

router = APIRouter()

# Pantallas por perfil. `href=None` = todavía no implementada (se muestra deshabilitada).
# Al construir una pantalla, poner su ruta acá.
MENU_POR_ROL = {
    "MUNICIPIO": [("Registrar emergencia", "/emergencias/nueva"), ("Mis emergencias", "/emergencias"),
                  ("Ofertas validadas", None)],
    "COORDINADOR": [("Emergencias", "/emergencias"), ("Generar y publicar lotes", None), ("Monitoreo", None)],
    "ONG": [("Convocatorias abiertas", "/emergencias"), ("Cargar / editar ofertas", None),
            ("Notificaciones de adjudicación", None)],
    "AUDITOR": [("Consulta de emergencias", "/emergencias")],
}


@router.get("/", response_class=HTMLResponse)
def home(request: Request, user: Usuario = Depends(require_role())):
    return templates.TemplateResponse(
        request, "index.html", {"user": user, "menu": MENU_POR_ROL[user.rol.value]}
    )


@router.get("/health")
def health():
    return {"status": "ok"}
