"""Login, sesión y control de acceso por rol (T-04)."""
import pytest
from fastapi import Depends

from app.core.deps import require_role
from app.main import app
from app.models import Rol

USUARIOS = ["operador.municipal", "coordinador.regional", "ong.cruzroja", "ong.bomberos", "auditor"]


# Rutas de prueba, una vez por proceso: solo el Coordinador puede entrar.
if not any(getattr(r, "path", "") == "/_t/coord" for r in app.routes):
    @app.get("/_t/coord")
    def _t_coord(u=Depends(require_role(Rol.COORDINADOR))):
        return {"ok": u.username}

    @app.get("/api/_t/coord")
    def _t_api_coord(u=Depends(require_role(Rol.COORDINADOR))):
        return {"ok": u.username}

    @app.get("/_t/logueado")
    def _t_logueado(u=Depends(require_role())):
        return {"ok": u.username}


def test_anonimo_es_redirigido_al_login(client):
    r = client.get("/")
    assert r.status_code == 303 and r.headers["location"] == "/login"


def test_api_sin_sesion_devuelve_401_json(client):
    r = client.get("/api/_t/coord")
    assert r.status_code == 401
    assert "detail" in r.json()


@pytest.mark.parametrize("password", ["", "incorrecta", "DEMO1234"])
def test_login_con_password_incorrecta(client, password):
    r = client.post("/login", data={"username": "ong.cruzroja", "password": password})
    assert r.status_code == 401
    assert "incorrectos" in r.text
    assert client.get("/").status_code == 303  # sigue sin sesión


def test_login_de_usuario_inexistente(client):
    r = client.post("/login", data={"username": "nadie", "password": "demo1234"})
    assert r.status_code == 401


@pytest.mark.parametrize("username", USUARIOS)
def test_cada_perfil_entra_y_ve_su_menu(login, username):
    c = login(username)
    r = c.get("/")
    assert r.status_code == 200
    assert "Salir" in r.text


def test_menus_distintos_por_perfil(login):
    assert "Registrar emergencia" in login("operador.municipal").get("/").text
    c = login("coordinador.regional")
    assert "Generar y publicar lotes" in c.get("/").text
    assert "Registrar emergencia" not in c.get("/").text


def test_rol_incorrecto_da_403_en_pagina_y_en_api(login):
    c = login("ong.cruzroja")
    r = c.get("/_t/coord")
    assert r.status_code == 403 and "no tiene acceso" in r.text
    assert c.get("/api/_t/coord").status_code == 403


def test_rol_correcto_pasa(login):
    assert login("coordinador.regional").get("/_t/coord").json() == {"ok": "coordinador.regional"}


def test_logout_cierra_la_sesion(login):
    c = login("ong.cruzroja")
    assert c.post("/logout").status_code == 303
    assert c.get("/_t/logueado").status_code == 303


def test_login_estando_logueado_redirige_al_inicio(login):
    c = login("ong.cruzroja")
    r = c.get("/login")
    assert r.status_code == 303 and r.headers["location"] == "/"


def test_sesion_de_usuario_borrado_deja_de_valer(login, seeded):
    from sqlalchemy import delete
    from app.models import Usuario

    c = login("auditor")
    with seeded() as s:
        s.execute(delete(Usuario).where(Usuario.username == "auditor"))
        s.commit()
    assert c.get("/_t/logueado").status_code == 303


def test_health_es_publico(client):
    assert client.get("/health").json() == {"status": "ok"}
