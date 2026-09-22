from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import verify_password
from app.core.templating import templates
from app.db import get_db
from app.models import Usuario
from app.seed import DEMO_PASSWORD, DEMO_USERS

router = APIRouter()


def _login_page(request: Request, settings: Settings, error: str | None = None, status_code: int = 200):
    demo = [(u, rol.value) for u, _, rol, _ in DEMO_USERS] if settings.show_demo_users else None
    return templates.TemplateResponse(
        request, "login.html",
        {"error": error, "demo_users": demo, "demo_password": DEMO_PASSWORD},
        status_code=status_code,
    )


@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request, settings: Settings = Depends(get_settings)):
    if request.session.get("uid"):
        return RedirectResponse("/", status_code=303)
    return _login_page(request, settings)


@router.post("/login", response_class=HTMLResponse)
def login(
    request: Request,
    username: str = Form(""),
    password: str = Form(""),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = db.scalar(select(Usuario).where(Usuario.username == username.strip()))
    if user is None or not verify_password(password, user.password_hash):
        return _login_page(request, settings, "Usuario o contraseña incorrectos", status_code=401)
    request.session.clear()
    request.session.update({"uid": user.id, "nombre": user.nombre, "rol": user.rol.value})
    return RedirectResponse("/", status_code=303)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)
