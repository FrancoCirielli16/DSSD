"""Cliente de la REST API de Bonita (base para T-07, T-08 y T-13).

Probado el 20/09/2026 contra el Bonita embebido de Studio 10.4.0: login con
token CSRF, resolver el proceso, instanciar con el contrato, leer tareas,
setear variables y avanzar tareas. Ver bonita/scripts/bonita_client.py para la
version de linea de comandos.
"""
import time

import requests

CONTRACT_INPUTS = ("emergenciaId", "municipioId", "nivelGravedad", "ventanaOfertasISO")

BONITA_ROLE_MAP = {
    "MUNICIPIO": ("municipio", "operador_municipal", "Operador Municipal"),
    "COORDINADOR": ("coordinador", "centro_coordinador_regional", "Centro Coordinador Regional"),
    "ONG": ("ong", "organizacion_no_gubernamental", "Organización No Gubernamental"),
    "AUDITOR": ("entidad_nacional", "entidad_nacional", "Entidad Nacional"),
}


class BonitaError(RuntimeError):
    pass


class BonitaClient:
    def __init__(self, base_url: str, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        # requests no tiene timeout por defecto: sin esto, un Bonita colgado congela la request.
        return self.session.request(method, f"{self.base_url}{path}", timeout=self.timeout, **kwargs)

    def login(self, username: str, password: str) -> None:
        resp = self._request(
            "POST", "/loginservice",
            data={"username": username, "password": password, "redirect": "false"},
        )
        resp.raise_for_status()
        token = self.session.cookies.get("X-Bonita-API-Token")
        if not token:
            raise BonitaError("Login OK pero sin cookie X-Bonita-API-Token")
        self.session.headers.update({"X-Bonita-API-Token": token})

    def resolve_process_id(self, name: str, version: str) -> str:
        resp = self._request(
            "GET", "/API/bpm/process",
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
        resp = self._request(
            "POST", f"/API/bpm/process/{process_definition_id}/instantiation", json=contract_inputs
        )
        resp.raise_for_status()
        return resp.json()["caseId"]

    def set_case_variable(self, case_id, name: str, value, java_type: str) -> None:
        resp = self._request(
            "PUT", f"/API/bpm/caseVariable/{case_id}/{name}", json={"value": value, "type": java_type}
        )
        resp.raise_for_status()

    def get_case_variables(self, case_id) -> dict:
        """Variables del caso como {nombre: valor} (los valores vienen serializados a texto)."""
        resp = self._request(
            "GET", "/API/bpm/caseVariable", params={"f": f"case_id={case_id}", "p": 0, "c": 100}
        )
        resp.raise_for_status()
        return {v["name"]: v["value"] for v in resp.json()}

    def resolve_case_id(self, returned_case_id, emergencia_id: int) -> int:
        """Devuelve el caso que Bonita vinculo con la emergencia indicada.

        Normalmente el ID de la instanciacion es suficiente. La busqueda de
        respaldo evita asociar una emergencia local al caso equivocado si las
        bases de Bonita y de la aplicacion quedaron desincronizadas.
        """
        returned_variables = self.get_case_variables(returned_case_id)
        if returned_variables.get("emergenciaId") == str(emergencia_id):
            return int(returned_case_id)

        resp = self._request(
            "GET", "/API/bpm/caseVariable",
            params={"f": "name=emergenciaId", "p": 0, "c": 1000},
        )
        resp.raise_for_status()
        for variable in resp.json():
            if variable.get("value") == str(emergencia_id):
                case_id = variable.get("case_id", variable.get("caseId"))
                if case_id is not None:
                    return int(case_id)

        raise BonitaError(
            f"No se encontro en Bonita un caso asociado a la emergencia {emergencia_id}"
        )

    def get_human_tasks(self, case_id) -> list:
        resp = self._request(
            "GET", "/API/bpm/humanTask", params={"f": f"caseId={case_id}", "p": 0, "c": 100}
        )
        resp.raise_for_status()
        return resp.json()

    def find_identity(self, resource: str, field: str, value: str) -> dict | None:
        resp = self._request(
            "GET", f"/API/identity/{resource}", params={"f": f"{field}={value}", "p": 0, "c": 100}
        )
        resp.raise_for_status()
        return next(iter(resp.json()), None)

    def list_identity(self, resource: str, field: str, value: str) -> list[dict]:
        resp = self._request(
            "GET", f"/API/identity/{resource}", params={"f": f"{field}={value}", "p": 0, "c": 100}
        )
        resp.raise_for_status()
        return resp.json()

    def find_profile(self, name: str) -> dict | None:
        resp = self._request(
            "GET", "/API/portal/profile", params={"f": f"name={name}", "p": 0, "c": 100}
        )
        resp.raise_for_status()
        return next(iter(resp.json()), None)

    def find_profile_member(self, profile_id: str, user_id: str) -> dict | None:
        resp = self._request(
            "GET", "/API/portal/profileMember",
            params={
                "f": ["member_type=user", f"profile_id={profile_id}", f"user_id={user_id}"],
                "p": 0,
                "c": 100,
            },
        )
        resp.raise_for_status()
        return next(iter(resp.json()), None)

    def create_identity(self, resource: str, data: dict) -> dict:
        resp = self._request("POST", f"/API/identity/{resource}", json=data)
        resp.raise_for_status()
        return resp.json()

    def add_membership(self, user_id: str, group_id: str, role_id: str) -> None:
        resp = self._request(
            "POST", "/API/identity/membership",
            json={"user_id": user_id, "group_id": group_id, "role_id": role_id},
        )
        resp.raise_for_status()

    def delete_membership(self, membership_id: str) -> None:
        resp = self._request("DELETE", f"/API/identity/membership/{membership_id}")
        resp.raise_for_status()

    def add_profile_member(self, profile_id: str, user_id: str) -> None:
        resp = self._request(
            "POST", "/API/portal/profileMember", json={"profile_id": profile_id, "user_id": user_id}
        )
        resp.raise_for_status()

    def current_user_id(self) -> str:
        resp = self._request("GET", "/API/system/session/unusedid")
        resp.raise_for_status()
        return resp.json()["user_id"]

    def assign_task(self, task_id, user_id) -> None:
        resp = self._request("PUT", f"/API/bpm/userTask/{task_id}", json={"assigned_id": user_id})
        resp.raise_for_status()

    def execute_task(self, task_id) -> None:
        resp = self._request("POST", f"/API/bpm/userTask/{task_id}/execution", json={})
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

    def wait_for_task(self, case_id, display_name_prefix: str, retries: int = 10) -> dict | None:
        """Bonita crea cada tarea de forma asíncrona: puede tardar un instante en aparecer."""
        for intento in range(retries):
            tarea = self.find_task(case_id, display_name_prefix)
            if tarea is not None:
                return tarea
            if intento < retries - 1:
                time.sleep(0.5)
        return None
