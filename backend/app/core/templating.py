from datetime import datetime, timezone
from pathlib import Path

from fastapi import Request
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent.parent

ROL_LABEL = {
    "MUNICIPIO": "Operador Municipal",
    "COORDINADOR": "Centro Coordinador Regional",
    "ONG": "Representante de ONG",
    "AUDITOR": "Auditor / Directivo",
}


TIPO_LABEL = {
    "inundacion": "Inundación",
    "incendio": "Incendio",
    "terremoto": "Terremoto",
    "otro": "Otro",
}

ESTADO_LABEL = {
    "REGISTRADA": ("Registrada", "secondary"),
    "CONVOCATORIA": ("Convocatoria abierta", "primary"),
    "CERRADA": ("Cerrada", "dark"),
}


def fecha(dt: datetime | None) -> str:
    if dt is None:
        return "—"
    if dt.tzinfo is None:  # SQLite no guarda la zona; lo que se guarda siempre es UTC
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone().strftime("%d/%m/%Y %H:%M")


ISLANDS_BUNDLE = BASE_DIR / "static" / "islands" / "islands.js"


def islands_version() -> int | None:
    """mtime del bundle de React (sirve para invalidar la caché del navegador), o None si no se compiló."""
    try:
        return int(ISLANDS_BUNDLE.stat().st_mtime)
    except FileNotFoundError:
        return None


def _session_context(request: Request) -> dict:
    # Solo para mostrar en la barra; la autorización real la hace core/deps.py contra la BD.
    s = request.session
    return {"session_user": s if s.get("uid") else None, "rol_label": ROL_LABEL, "estado_label": ESTADO_LABEL,
            "tipo_label": TIPO_LABEL}


templates = Jinja2Templates(directory=str(BASE_DIR / "templates"), context_processors=[_session_context])
templates.env.filters["fecha"] = fecha
templates.env.globals["islands_version"] = islands_version
