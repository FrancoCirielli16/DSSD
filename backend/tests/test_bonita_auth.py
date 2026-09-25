import responses


BASE = "http://bonita.test/bonita"


def _bonita_identity_responses():
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
        json={"userName": "admin.rescuesync", "firstname": "Administrador", "lastname": "RescueSync"},
    )
    responses.add(
        responses.GET,
        f"{BASE}/API/identity/membership",
        json=[
            {"group_id": "15", "role_id": "1"},
            {"group_id": "16", "role_id": "1"},
        ],
    )
    responses.add(
        responses.GET,
        f"{BASE}/API/identity/group/15",
        json={"name": "municipio", "parent_path": "/rescuesync"},
    )
    responses.add(
        responses.GET,
        f"{BASE}/API/identity/group/16",
        json={"name": "coordinador", "parent_path": "/rescuesync"},
    )
    responses.add(
        responses.GET,
        f"{BASE}/API/identity/role/1",
        json={"name": "member"},
    )


@responses.activate
def test_login_bonita_guarda_la_identidad_en_la_sesion(client):
    _bonita_identity_responses()

    response = client.post(
        "/api/auth/bonita/login",
        json={"username": "admin.rescuesync", "password": "bpm"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "user_id": "42",
        "username": "admin.rescuesync",
        "nombre": "Administrador RescueSync",
        "grupos": ["/rescuesync/coordinador", "/rescuesync/municipio"],
    }


@responses.activate
def test_login_bonita_rechaza_credenciales_invalidas(client):
    responses.add(responses.POST, f"{BASE}/loginservice", status=401)

    response = client.post(
        "/api/auth/bonita/login",
        json={"username": "admin.rescuesync", "password": "incorrecta"},
    )

    assert response.status_code == 401