"""T-05/T-06/T-07/T-08: alta de emergencia, de punta a punta.

El formulario propio de la app reemplaza el formulario nativo de Bonita para la
tarea "Registrar Emergencia" (ver CLAUDE.md, stack elegido), así que además de
instanciar el caso, esta capa completa esa primera tarea en nombre del
Municipio: si no lo hiciéramos, el caso quedaría esperando para siempre a que
alguien la complete desde la UI nativa de Bonita, que la app no usa.
"""
from __future__ import annotations

from datetime import datetime, timedelta

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.integrations.bonita import BONITA_TEST_USERS, BonitaClient, BonitaError
from app.models import Emergencia, EstadoEmergencia, Gravedad, Rol, Usuario


def _filtro_visibilidad(user: Usuario):
    """Qué emergencias ve cada perfil. Coordinador y Auditor ven todas."""
    if user.rol is Rol.MUNICIPIO:
        return Emergencia.municipio_id == user.municipio_id
    if user.rol is Rol.ONG:
        return Emergencia.estado == EstadoEmergencia.CONVOCATORIA
    return True


def emergencias_visibles(db: Session, user: Usuario) -> list[Emergencia]:
    return list(db.scalars(
        select(Emergencia).where(_filtro_visibilidad(user)).order_by(Emergencia.id.desc())
    ))


def emergencia_visible(db: Session, user: Usuario, emergencia_id: int) -> Emergencia | None:
    return db.scalar(select(Emergencia).where(Emergencia.id == emergencia_id, _filtro_visibilidad(user)))


class AltaEmergenciaError(RuntimeError):
    """La emergencia no pudo registrarse contra Bonita; no debe quedar nada a medias en la BD."""


def _ventana_provisoria(settings: Settings) -> str:
    # Ver CLAUDE.md, "Decisión: ventana de ofertas" (opción A): valor provisorio válido
    # al alta; T-10 lo sobrescribe con la ventana real antes de publicar la convocatoria.
    vencimiento = datetime.now().astimezone() + timedelta(hours=settings.ventana_provisoria_horas)
    return vencimiento.isoformat(timespec="seconds")


def _completar_registrar_emergencia(settings: Settings, admin: BonitaClient, case_id) -> None:
    tarea = admin.find_task(case_id, "Registrar Emergencia")
    if tarea is None:
        raise BonitaError("El caso se instanció pero no apareció la tarea 'Registrar Emergencia'")

    municipio = BonitaClient(settings.bonita_base_url, settings.bonita_timeout_seconds)
    municipio.login(BONITA_TEST_USERS["MUNICIPIO"], settings.bonita_test_password)
    municipio.complete_task_as_self(tarea["id"])


def registrar_emergencia(
    db: Session,
    settings: Settings,
    *,
    operador: Usuario,
    tipo: str,
    nivel_gravedad: Gravedad,
    zona_afectada: str,
    descripcion: str,
) -> Emergencia:
    if operador.municipio_id is None:
        raise AltaEmergenciaError("Tu usuario no tiene un municipio asignado; no se puede registrar.")

    emergencia = Emergencia(
        municipio_id=operador.municipio_id,
        tipo=tipo,
        nivel_gravedad=nivel_gravedad,
        zona_afectada=zona_afectada,
        descripcion=descripcion,
    )
    db.add(emergencia)
    db.flush()  # asigna emergencia.id (para el contrato) sin comitear todavía

    try:
        admin = BonitaClient(settings.bonita_base_url, settings.bonita_timeout_seconds)
        admin.login(settings.bonita_username, settings.bonita_password)
        process_id = admin.resolve_process_id(settings.bonita_process_name, settings.bonita_process_version)
        case_id = admin.start_case(process_id, {
            "emergenciaId": emergencia.id,
            "municipioId": operador.municipio_id,
            "nivelGravedad": nivel_gravedad.value,
            "ventanaOfertasISO": _ventana_provisoria(settings),
        })
        _completar_registrar_emergencia(settings, admin, case_id)
    except (BonitaError, requests.RequestException) as exc:
        db.rollback()
        raise AltaEmergenciaError(
            "No se pudo iniciar el caso en Bonita. La emergencia no se registró; probá de nuevo."
        ) from exc

    emergencia.bonita_case_id = int(case_id)
    db.commit()
    db.refresh(emergencia)
    return emergencia
