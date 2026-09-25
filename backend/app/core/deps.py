from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Rol, Usuario


def get_current_user(request: Request, db: Session = Depends(get_db)) -> Usuario | None:
    uid = request.session.get("uid")
    if uid is not None:
        user = db.get(Usuario, uid)
    else:
        bonita_username = request.session.get("bonita_username")
        if bonita_username is None:
            return None
        user = db.scalar(select(Usuario).where(Usuario.username == bonita_username))
    if user is None:  # usuario borrado con la sesión viva
        request.session.clear()
    return user


def require_role(*roles: Rol):
    """Dependencia de ruta: 401 si no hay sesión, 403 si el rol no está permitido.
    Sin roles, solo exige estar logueado. Uso: `user = Depends(require_role(Rol.COORDINADOR))`."""

    def dep(request: Request, user: Usuario | None = Depends(get_current_user)) -> Usuario:
        if user is None:
            raise HTTPException(status_code=401, detail="Iniciá sesión")
        bonita_roles = request.session.get("bonita_roles")
        if bonita_roles is not None:
            allowed = not roles or any(role.value in bonita_roles for role in roles)
        else:
            allowed = not roles or user.rol in roles
        if not allowed:
            raise HTTPException(status_code=403, detail="Tu perfil no tiene acceso a esta sección")
        return user

    return dep
