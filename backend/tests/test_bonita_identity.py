import responses

from app.integrations.bonita_identity import authenticate


BASE = "http://bonita.test/bonita"


@responses.activate
def test_authenticate_devuelve_usuario_y_grupos():
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
        json={"id": "42", "userName": "admin.rescuesync", "firstname": "Administrador", "lastname": "RescueSync"},
    )
    responses.add(
        responses.GET,
        f"{BASE}/API/identity/membership",
        json=[
            {"group_id": "15", "role_id": "1"},
            {"group_id": "101", "role_id": "1"},
        ],
    )
    responses.add(
        responses.GET,
        f"{BASE}/API/identity/group/15",
        json={"name": "municipio", "parent_path": "/rescuesync"},
    )
    responses.add(
        responses.GET,
        f"{BASE}/API/identity/group/101",
        json={"name": "auditor", "parent_path": "/rescuesync"},
    )
    responses.add(
        responses.GET,
        f"{BASE}/API/identity/role/1",
        json={"name": "member"},
    )

    identity = authenticate(BASE, "admin.rescuesync", "bpm")

    assert identity.user_id == "42"
    assert identity.username == "admin.rescuesync"
    assert identity.display_name == "Administrador RescueSync"
    assert identity.group_paths == {"/rescuesync/municipio", "/rescuesync/auditor"}