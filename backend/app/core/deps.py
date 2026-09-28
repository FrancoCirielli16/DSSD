from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Rol, Usuario


def get_current_user(request: Request, db: Session = Depends(get_db)) -> Usuario | None:
    uid = request.session.get("uid")
    if uid is None:
        return None
    user = db.get(Usuario, uid)
    if user is None:  # usuario borrado con la sesión viva
        request.session.clear()
    return user


def require_role(*roles: Rol):
    """Dependencia de ruta: 401 si no hay sesión, 403 si el rol no está permitido.
    Sin roles, solo exige estar logueado. Uso: `user = Depends(require_role(Rol.COORDINADOR))`."""

    def dep(user: Usuario | None = Depends(get_current_user)) -> Usuario:
        if user is None:
            raise HTTPException(status_code=401, detail="Iniciá sesión")
        if roles and user.rol not in roles:
            raise HTTPException(status_code=403, detail="Tu perfil no tiene acceso a esta sección")
        return user

    return dep
