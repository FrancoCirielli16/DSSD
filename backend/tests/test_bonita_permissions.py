import responses


BASE = "http://bonita.test/bonita"


def _login_bonita(client, username: str, group_id: str, group_name: str):
    responses.add(
        responses.POST,
        f"{BASE}/loginservice",
        status=204,
        headers={"Set-Cookie": "X-Bonita-API-Token=tok123; Path=/"},
    )
    responses.add(
        responses.GET,
        f"{BASE}/API/system/session/unusedid",
        json={"user_id": "42"},
    )
    responses.add(
        responses.GET,
        f"{BASE}/API/identity/user/42",
        json={"userName": username, "firstname": "Usuario", "lastname": "Prueba"},
    )
    responses.add(
        responses.GET,
        f"{BASE}/API/identity/membership",
        json=[{"group_id": group_id, "role_id": "1"}],
    )
    responses.add(
        responses.GET,
        f"{BASE}/API/identity/group/{group_id}",
        json={"name": group_name, "parent_path": "/rescuesync"},
    )
    responses.add(
        responses.GET,
        f"{BASE}/API/identity/role/1",
        json={"name": "member"},
    )
    return client.post(
        "/api/auth/bonita/login",
        json={"username": username, "password": "bpm"},
    )


@responses.activate
def test_require_role_usa_grupos_bonita_para_rechazar_un_rol(client):
    response = _login_bonita(client, "operador.municipal", "15", "municipio")
    assert response.status_code == 200

    response = client.post(
        "/api/emergencias/1/lotes",
        json={"recurso": "Raciones", "cantidad": 10, "unidad": "unidades"},
    )

    assert response.status_code == 403


@responses.activate
def test_require_role_usa_grupos_bonita_para_permitir_un_rol(client):
    response = _login_bonita(client, "coordinador.regional", "16", "coordinador")
    assert response.status_code == 200

    response = client.post(
        "/api/emergencias/1/lotes",
        json={"recurso": "Raciones", "cantidad": 10, "unidad": "unidades"},
    )

    assert response.status_code == 404