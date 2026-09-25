import responses


BASE = "http://bonita.test/bonita"


def test_bonita_me_sin_sesion_devuelve_401(client):
    response = client.get("/api/auth/bonita/me")

    assert response.status_code == 401


@responses.activate
def test_bonita_me_devuelve_la_identidad_de_la_sesion(client):
    responses.add(
        responses.POST,
        f"{BASE}/loginservice",
        status=204,
        headers={"Set-Cookie": "X-Bonita-API-Token=tok123; Path=/"},
    )
    responses.add(responses.GET, f"{BASE}/API/system/session/unusedid", json={"user_id": "42"})
    responses.add(
        responses.GET,
        f"{BASE}/API/identity/user/42",
        json={"userName": "admin.rescuesync", "firstname": "Administrador", "lastname": "RescueSync"},
    )
    responses.add(
        responses.GET,
        f"{BASE}/API/identity/membership",
        json=[{"group_id": "15", "role_id": "1"}],
    )
    responses.add(
        responses.GET,
        f"{BASE}/API/identity/group/15",
        json={"name": "municipio", "parent_path": "/rescuesync"},
    )
    responses.add(responses.GET, f"{BASE}/API/identity/role/1", json={"name": "member"})

    login = client.post(
        "/api/auth/bonita/login",
        json={"username": "admin.rescuesync", "password": "bpm"},
    )
    response = client.get("/api/auth/bonita/me")

    assert login.status_code == 200
    assert response.json()["username"] == "admin.rescuesync"
    assert response.json()["roles"] == ["MUNICIPIO"]