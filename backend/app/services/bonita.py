"""Cliente Bonita embebido en el backend (HU-2.4).

Basado en bonita/scripts/bonita_client.py — se adapta acá para usarlo desde FastAPI.
"""

from __future__ import annotations

import httpx

from app.config import settings

CONTRACT_INPUTS = ("emergenciaId", "municipioId", "nivelGravedad", "ventanaOfertasISO")


class BonitaError(RuntimeError):
    pass


class BonitaClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or settings.bonita_base_url).rstrip("/")
        self._client = httpx.Client(base_url=self.base_url, timeout=3.0, follow_redirects=True)
        self._api_token: str | None = None

    def close(self) -> None:
        self._client.close()

    def login(self, username: str | None = None, password: str | None = None) -> None:
        resp = self._client.post(
            "/loginservice",
            data={
                "username": username or settings.bonita_username,
                "password": password or settings.bonita_password,
                "redirect": "false",
            },
        )
        if resp.status_code >= 400:
            raise BonitaError(f"Login Bonita falló: {resp.status_code} {resp.text}")
        token = self._client.cookies.get("X-Bonita-API-Token")
        if not token:
            raise BonitaError("Login OK pero falta cookie X-Bonita-API-Token")
        self._api_token = token
        self._client.headers["X-Bonita-API-Token"] = token

    def _auth_headers(self) -> dict[str, str]:
        if not self._api_token:
            raise BonitaError("Hay que hacer login antes")
        return {"X-Bonita-API-Token": self._api_token}

    def resolve_process_id(
        self,
        name: str | None = None,
        version: str | None = None,
    ) -> str:
        params = {
            "p": 0,
            "c": 1,
            "f": [
                f"name={name or settings.bonita_process_name}",
                f"version={version or settings.bonita_process_version}",
            ],
        }
        resp = self._client.get("/API/bpm/process", params=params, headers=self._auth_headers())
        if resp.status_code >= 400:
            raise BonitaError(f"No se pudo resolver el proceso: {resp.status_code} {resp.text}")
        data = resp.json()
        if not data:
            raise BonitaError("Proceso RescueSync no encontrado / no desplegado")
        return str(data[0]["id"])

    def instantiate(
        self,
        *,
        emergencia_id: int,
        municipio_id: int,
        nivel_gravedad: str,
        ventana_ofertas_iso: str,
    ) -> str:
        process_id = self.resolve_process_id()
        payload = {
            "emergenciaId": emergencia_id,
            "municipioId": municipio_id,
            "nivelGravedad": nivel_gravedad,
            "ventanaOfertasISO": ventana_ofertas_iso,
        }
        # Validación mínima del contrato congelado en modelo-proceso.md
        missing = [k for k in CONTRACT_INPUTS if k not in payload]
        if missing:
            raise BonitaError(f"Faltan inputs del contrato: {missing}")

        resp = self._client.post(
            f"/API/bpm/process/{process_id}/instantiation",
            json=payload,
            headers={**self._auth_headers(), "Content-Type": "application/json"},
        )
        if resp.status_code >= 400:
            raise BonitaError(f"Instanciación falló: {resp.status_code} {resp.text}")
        body = resp.json()
        case_id = body.get("caseId") or body.get("id")
        if case_id is None:
            raise BonitaError(f"Respuesta de instanciación sin caseId: {body}")
        return str(case_id)


def start_rescue_sync_case(
    *,
    emergencia_id: int,
    municipio_id: int,
    nivel_gravedad: str,
    ventana_ofertas_iso: str,
) -> str:
    client = BonitaClient()
    try:
        client.login()
        return client.instantiate(
            emergencia_id=emergencia_id,
            municipio_id=municipio_id,
            nivel_gravedad=nivel_gravedad,
            ventana_ofertas_iso=ventana_ofertas_iso,
        )
    except BonitaError:
        raise
    except Exception as exc:  # red caída, Engine apagado, etc.
        raise BonitaError(str(exc)) from exc
    finally:
        client.close()
