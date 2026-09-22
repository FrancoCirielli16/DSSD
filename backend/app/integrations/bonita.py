"""Cliente de la REST API de Bonita (base para T-07, T-08 y T-13).

Probado el 20/09/2026 contra el Bonita embebido de Studio 10.4.0: login con
token CSRF, resolver el proceso, instanciar con el contrato, leer tareas,
setear variables y avanzar tareas. Ver bonita/scripts/bonita_client.py para la
version de linea de comandos.
"""
import time

import requests

CONTRACT_INPUTS = ("emergenciaId", "municipioId", "nivelGravedad", "ventanaOfertasISO")

# Usuario de prueba de la organización Bonita (entrega-2/ACME.xml) por rol de nuestra
# app (app.models.Rol): quien nuestra app usa para completar tareas humanas de esa lane.
BONITA_TEST_USERS = {
    "MUNICIPIO": "operador.municipal",
    "COORDINADOR": "coordinador.regional",
    "ONG": "ong.cruzroja",
}


class BonitaError(RuntimeError):
    pass


class BonitaClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def login(self, username: str, password: str) -> None:
        resp = self.session.post(
            f"{self.base_url}/loginservice",
            data={"username": username, "password": password, "redirect": "false"},
        )
        resp.raise_for_status()
        token = self.session.cookies.get("X-Bonita-API-Token")
        if not token:
            raise BonitaError("Login OK pero sin cookie X-Bonita-API-Token")
        self.session.headers.update({"X-Bonita-API-Token": token})

    def resolve_process_id(self, name: str, version: str) -> str:
        resp = self.session.get(
            f"{self.base_url}/API/bpm/process",
            params={"f": [f"name={name}", f"version={version}"]},
        )
        resp.raise_for_status()
        results = resp.json()
        if not results:
            raise BonitaError(f"Proceso '{name}' v{version} no encontrado (¿desplegado?)")
        return results[0]["id"]

    def start_case(self, process_definition_id: str, contract_inputs: dict) -> str:
        missing = [k for k in CONTRACT_INPUTS if k not in contract_inputs]
        if missing:
            raise ValueError(f"Faltan inputs del contrato: {missing}")
        resp = self.session.post(
            f"{self.base_url}/API/bpm/process/{process_definition_id}/instantiation",
            json=contract_inputs,
        )
        resp.raise_for_status()
        return resp.json()["caseId"]

    def set_case_variable(self, case_id, name: str, value, java_type: str) -> None:
        resp = self.session.put(
            f"{self.base_url}/API/bpm/caseVariable/{case_id}/{name}",
            json={"value": value, "type": java_type},
        )
        resp.raise_for_status()

    def get_human_tasks(self, case_id, retries: int = 10) -> list:
        # La primera tarea se crea de forma asincrona: puede tardar un instante.
        for _ in range(retries):
            resp = self.session.get(
                f"{self.base_url}/API/bpm/humanTask",
                params={"f": f"caseId={case_id}", "p": 0, "c": 100},
            )
            resp.raise_for_status()
            tasks = resp.json()
            if tasks:
                return tasks
            time.sleep(0.5)
        return []

    def current_user_id(self) -> str:
        resp = self.session.get(f"{self.base_url}/API/system/session/unusedid")
        resp.raise_for_status()
        return resp.json()["user_id"]

    def assign_task(self, task_id, user_id) -> None:
        resp = self.session.put(f"{self.base_url}/API/bpm/userTask/{task_id}", json={"assigned_id": user_id})
        resp.raise_for_status()

    def execute_task(self, task_id) -> None:
        resp = self.session.post(f"{self.base_url}/API/bpm/userTask/{task_id}/execution", json={})
        resp.raise_for_status()

    def complete_task_as_self(self, task_id) -> None:
        """Asigna la tarea al usuario logueado y la ejecuta. Requiere ser miembro
        del actor de la tarea (loguearse con un usuario de prueba del rol correcto)."""
        self.assign_task(task_id, self.current_user_id())
        self.execute_task(task_id)

    def find_task(self, case_id, display_name_prefix: str) -> dict | None:
        for t in self.get_human_tasks(case_id):
            if t["displayName"].startswith(display_name_prefix):
                return t
        return None
