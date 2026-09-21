from sqlalchemy.orm import Session

from app.models import Rol, Usuario
from app.security import hash_password

SEED_USERS = [
    ("operador.municipal", "bpm", "Operador Municipal", Rol.MUNICIPIO, "Municipio Demo"),
    ("coordinador.regional", "bpm", "Coordinador Regional", Rol.COORDINADOR, "CCR"),
    ("ong.cruzroja", "bpm", "Cruz Roja", Rol.ONG, "Cruz Roja"),
    ("ong.bomberos", "bpm", "Bomberos Voluntarios", Rol.ONG, "Bomberos"),
    ("auditor.directivo", "bpm", "Auditor Directivo", Rol.AUDITOR, None),
]


def seed_users(db: Session) -> None:
    for username, password, nombre, rol, org in SEED_USERS:
        exists = db.query(Usuario).filter(Usuario.username == username).first()
        if exists:
            continue
        db.add(
            Usuario(
                username=username,
                password_hash=hash_password(password),
                nombre=nombre,
                rol=rol,
                organizacion=org,
            )
        )
    db.commit()
