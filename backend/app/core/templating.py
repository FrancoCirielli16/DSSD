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


def _session_context(request: Request) -> dict:
    # Solo para mostrar en la barra; la autorización real la hace core/deps.py contra la BD.
    s = request.session
    return {"session_user": s if s.get("uid") else None, "rol_label": ROL_LABEL}


templates = Jinja2Templates(directory=str(BASE_DIR / "templates"), context_processors=[_session_context])
