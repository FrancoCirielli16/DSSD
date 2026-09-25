from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import PerfilOperativo, Rol, Usuario


@dataclass
class AuthenticatedUser:
    id: int
    username: str
    nombre: str
    rol: Rol
    municipio_id: int | None
    ong_id: int | None


def _from_local_user(user: Usuario) -> AuthenticatedUser:
    return AuthenticatedUser(
        id=user.id,
        username=user.username,
        nombre=user.nombre,
        rol=user.rol,
        municipio_id=user.municipio_id,
        ong_id=user.ong_id,
    )


def get_current_user(request: Request, db: Session = Depends(get_db)) -> AuthenticatedUser | None:
    uid = request.session.get("uid")
    if uid is not None:
        user = db.get(Usuario, uid)
        if user is None:
            request.session.clear()
            return None
        return _from_local_user(user)

    bonita_username = request.session.get("bonita_username")
    if bonita_username is None:
        return None
    profile = db.scalar(
        select(PerfilOperativo).where(PerfilOperativo.bonita_username == bonita_username)
    )
    if profile is None:
        request.session.clear()
        return None
    roles = request.session.get("bonita_roles", [])
    default_role = Rol.AUDITOR.value if Rol.AUDITOR.value in roles else (roles[0] if roles else Rol.AUDITOR.value)
    return AuthenticatedUser(
        id=profile.id,
        username=bonita_username,
        nombre=profile.nombre,
        rol=Rol(default_role),
        municipio_id=profile.municipio_id,
        ong_id=profile.ong_id,
    )


def require_role(*roles: Rol):
    """Dependencia de ruta: 401 si no hay sesión, 403 si el rol no está permitido.
    Sin roles, solo exige estar logueado. Uso: `user = Depends(require_role(Rol.COORDINADOR))`."""

    def dep(request: Request, user: AuthenticatedUser | None = Depends(get_current_user)) -> AuthenticatedUser:
        if user is None:
            raise HTTPException(status_code=401, detail="Iniciá sesión")
        bonita_roles = request.session.get("bonita_roles")
        if bonita_roles is not None:
            allowed = not roles or any(role.value in bonita_roles for role in roles)
            if allowed and roles:
                user.rol = roles[0]
        else:
            allowed = not roles or user.rol in roles
        if not allowed:
            raise HTTPException(status_code=403, detail="Tu perfil no tiene acceso a esta sección")
        return user

    return dep
