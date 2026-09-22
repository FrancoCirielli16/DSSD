"""Datos de demo: un municipio, dos ONGs y un usuario por cada perfil del enunciado.

Uso (después de `alembic upgrade head`):  python -m app.seed
Es idempotente: si el usuario ya existe, no lo vuelve a crear.
"""
from sqlalchemy import select

from app.core.security import hash_password
from app.db import SessionLocal
from app.models import Municipio, Ong, Rol, Usuario

DEMO_PASSWORD = "demo1234"


def seed(session_factory=SessionLocal) -> None:
    with session_factory() as db:
        municipio = db.scalar(select(Municipio).where(Municipio.nombre == "Bahía Blanca"))
        if municipio is None:
            municipio = Municipio(nombre="Bahía Blanca", provincia="Buenos Aires")
            db.add(municipio)
        # Dos ONGs: sin la segunda no se pueden probar consorcios, ofertas parciales ni cobertura.
        ongs = {}
        for nombre, cuit in [("Cruz Roja Argentina", "30-54666544-5"), ("Bomberos Voluntarios", "30-68522415-9")]:
            ong = db.scalar(select(Ong).where(Ong.nombre == nombre))
            if ong is None:
                ong = Ong(nombre=nombre, cuit=cuit)
                db.add(ong)
            ongs[nombre] = ong
        db.flush()

        usuarios = [
            ("operador.municipal", "Operador Municipal", Rol.MUNICIPIO, municipio.id, None),
            ("coordinador.regional", "Centro Coordinador Regional", Rol.COORDINADOR, None, None),
            ("ong.cruzroja", "Representante Cruz Roja", Rol.ONG, None, ongs["Cruz Roja Argentina"].id),
            ("ong.bomberos", "Representante Bomberos Voluntarios", Rol.ONG, None, ongs["Bomberos Voluntarios"].id),
            ("auditor", "Auditor / Directivo", Rol.AUDITOR, None, None),
        ]
        for username, nombre, rol, municipio_id, ong_id in usuarios:
            if db.scalar(select(Usuario).where(Usuario.username == username)) is None:
                db.add(
                    Usuario(
                        username=username,
                        password_hash=hash_password(DEMO_PASSWORD),
                        nombre=nombre,
                        rol=rol,
                        municipio_id=municipio_id,
                        ong_id=ong_id,
                    )
                )
        db.commit()


if __name__ == "__main__":
    seed()
    print("Seed listo. Usuarios de demo con contraseña:", DEMO_PASSWORD)
