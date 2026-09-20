"""Prueba real contra el Bonita de Studio. Apagada por defecto.

Correr con Studio ejecutado y el proceso desplegado:
    RUN_BONITA_INTEGRATION=1 pytest -m integration
Crea un caso de prueba (se borra al próximo Ejecutar/Desplegar de Studio).
"""
import os
from datetime import datetime, timedelta

import pytest

from app.core.config import Settings
from app.integrations.bonita import BonitaClient

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(os.getenv("RUN_BONITA_INTEGRATION") != "1",
                       reason="definir RUN_BONITA_INTEGRATION=1 (requiere Studio corriendo)"),
]


@pytest.fixture(scope="module")
def bonita():
    s = Settings(_env_file=None)
    c = BonitaClient(s.bonita_base_url)
    c.login(s.bonita_username, s.bonita_password)
    c.process_id = c.resolve_process_id(s.bonita_process_name, s.bonita_process_version)
    return c


def test_instanciar_arranca_en_registrar_emergencia_y_permite_pisar_la_ventana(bonita):
    ventana = (datetime.now().astimezone() + timedelta(hours=72)).isoformat(timespec="seconds")
    case_id = bonita.start_case(bonita.process_id, {
        "emergenciaId": 999, "municipioId": 1, "nivelGravedad": "ALTO", "ventanaOfertasISO": ventana})
    tareas = bonita.get_human_tasks(case_id)
    assert any(t["displayName"].startswith("Registrar Emergencia") for t in tareas)

    real = (datetime.now().astimezone() + timedelta(hours=1)).isoformat(timespec="seconds")
    bonita.set_case_variable(case_id, "ventanaOfertasISO", real, "java.lang.String")
