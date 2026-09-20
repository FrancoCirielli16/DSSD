"""Cliente de Bonita con HTTP simulado: no necesita Studio corriendo."""
import pytest
import responses

from app.integrations import bonita as bonita_mod
from app.integrations.bonita import BonitaClient, BonitaError, CONTRACT_INPUTS

BASE = "http://bonita.test/bonita"
CONTRATO = {"emergenciaId": 1, "municipioId": 2, "nivelGravedad": "ALTO",
            "ventanaOfertasISO": "2026-10-01T10:00:00-03:00"}


@pytest.fixture
def client():
    return BonitaClient(BASE + "/")  # con barra final: debe normalizarse


@pytest.fixture(autouse=True)
def sin_espera(monkeypatch):
    monkeypatch.setattr(bonita_mod.time, "sleep", lambda s: None)


def _login_ok(rsps):
    rsps.add(responses.POST, f"{BASE}/loginservice", status=204,
             headers={"Set-Cookie": "X-Bonita-API-Token=tok123; Path=/"})


@responses.activate
def test_login_guarda_el_token_csrf_como_header(client):
    _login_ok(responses)
    client.login("walter.bates", "bpm")
    assert client.session.headers["X-Bonita-API-Token"] == "tok123"
    body = responses.calls[0].request.body
    assert "redirect=false" in body and "username=walter.bates" in body


@responses.activate
def test_login_sin_cookie_de_token_falla(client):
    responses.add(responses.POST, f"{BASE}/loginservice", status=204)
    with pytest.raises(BonitaError):
        client.login("u", "p")


@responses.activate
def test_login_rechazado_propaga_error_http(client):
    responses.add(responses.POST, f"{BASE}/loginservice", status=401)
    with pytest.raises(Exception):
        client.login("u", "mal")


@responses.activate
def test_resolve_process_id(client):
    responses.add(responses.GET, f"{BASE}/API/bpm/process", json=[{"id": "555"}])
    assert client.resolve_process_id("Gestion Integral de la Emergencia", "1.0") == "555"
    q = responses.calls[0].request.url
    assert "name%3DGestion" in q or "name=Gestion" in q
    assert "version" in q


@responses.activate
def test_resolve_process_no_desplegado(client):
    responses.add(responses.GET, f"{BASE}/API/bpm/process", json=[])
    with pytest.raises(BonitaError, match="desplegado"):
        client.resolve_process_id("X", "1.0")


def test_start_case_exige_los_4_inputs_del_contrato(client):
    for faltante in CONTRACT_INPUTS:
        incompleto = {k: v for k, v in CONTRATO.items() if k != faltante}
        with pytest.raises(ValueError, match=faltante):
            client.start_case("555", incompleto)


@responses.activate
def test_start_case_envia_el_contrato_y_devuelve_case_id(client):
    responses.add(responses.POST, f"{BASE}/API/bpm/process/555/instantiation", json={"caseId": "1001"})
    assert client.start_case("555", CONTRATO) == "1001"
    import json
    assert json.loads(responses.calls[0].request.body) == CONTRATO


@responses.activate
def test_set_case_variable_envia_valor_y_tipo(client):
    import json
    responses.add(responses.PUT, f"{BASE}/API/bpm/caseVariable/1001/ventanaOfertasISO", status=200)
    client.set_case_variable("1001", "ventanaOfertasISO", "2026-10-02T00:00:00-03:00", "java.lang.String")
    assert json.loads(responses.calls[0].request.body) == {
        "value": "2026-10-02T00:00:00-03:00", "type": "java.lang.String"}


@responses.activate
def test_get_human_tasks_reintenta_hasta_que_aparece_la_primera(client):
    url = f"{BASE}/API/bpm/humanTask"
    responses.add(responses.GET, url, json=[])
    responses.add(responses.GET, url, json=[])
    responses.add(responses.GET, url, json=[{"displayName": "Registrar Emergencia"}])
    tasks = client.get_human_tasks("1001")
    assert tasks[0]["displayName"] == "Registrar Emergencia"
    assert len(responses.calls) == 3
    assert "p=0" in responses.calls[0].request.url and "c=100" in responses.calls[0].request.url


@responses.activate
def test_get_human_tasks_devuelve_vacio_si_nunca_aparece(client):
    responses.add(responses.GET, f"{BASE}/API/bpm/humanTask", json=[])
    assert client.get_human_tasks("1001", retries=3) == []
