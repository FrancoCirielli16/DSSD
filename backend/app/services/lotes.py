"""T-10: lotes de necesidades y publicación de la convocatoria (Centro Coordinador)."""
from __future__ import annotations

from datetime import datetime, timezone

import requests
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.integrations.bonita import BonitaClient, BonitaError
from app.models import Emergencia, EstadoEmergencia, Lote, Usuario
from app.schemas.lotes import LoteIn

TAREA_REVISAR = "Revisar Informacion"
TAREA_PUBLICAR = "Publicar Convocatoria"


class LoteError(RuntimeError):
    """Operación inválida sobre los lotes (estado equivocado, lote inexistente…)."""


class RevisionError(RuntimeError):
    """La revisión no pudo completarse en Bonita."""


class PublicacionError(RuntimeError):
    """La convocatoria no pudo publicarse; la emergencia queda como estaba."""


def _editable(emergencia: Emergencia) -> None:
    if emergencia.estado is not EstadoEmergencia.REGISTRADA:
        raise LoteError("La convocatoria ya está publicada: los lotes no se pueden modificar.")


def agregar_lote(
    db: Session, settings: Settings, emergencia: Emergencia, datos: LoteIn, *, actor: Usuario
) -> Lote:
    _editable(emergencia)
    if emergencia.bonita_case_id is None:
        raise LoteError("La emergencia no tiene caso en Bonita.")
    lote = Lote(emergencia_id=emergencia.id, **datos.model_dump())
    db.add(lote)
    try:
        db.flush()
        finalizar_revision_en_bonita(settings, emergencia.bonita_case_id, actor)
        db.commit()
        db.refresh(lote)
    except (BonitaError, requests.RequestException) as exc:
        db.rollback()
        raise RevisionError("No se pudo completar la revisión en Bonita; probá de nuevo.") from exc
    return lote


def borrar_lote(db: Session, emergencia: Emergencia, lote_id: int) -> None:
    _editable(emergencia)
    lote = next((lote for lote in emergencia.lotes if lote.id == lote_id), None)
    if lote is None:
        raise LoteError("Ese lote no pertenece a esta emergencia.")
    db.delete(lote)
    db.commit()


def publicar_convocatoria(
    db: Session, settings: Settings, *, emergencia: Emergencia, ventana_fin: datetime, actor: Usuario
) -> Emergencia:
    if emergencia.estado is not EstadoEmergencia.REGISTRADA:
        raise PublicacionError("Esta convocatoria ya fue publicada.")
    if not emergencia.lotes:
        raise PublicacionError("Agregá al menos un lote antes de publicar la convocatoria.")
    if emergencia.bonita_case_id is None:
        raise PublicacionError("La emergencia no tiene caso en Bonita; no se puede publicar.")
    if ventana_fin.tzinfo is None:
        ventana_fin = ventana_fin.astimezone()
    if ventana_fin <= datetime.now().astimezone():
        raise PublicacionError("El cierre de la ventana tiene que ser una fecha futura.")

    try:
        publicar_en_bonita(settings, emergencia.bonita_case_id, ventana_fin, actor)
    except (BonitaError, requests.RequestException) as exc:
        db.rollback()
        raise PublicacionError(
            "No se pudo publicar la convocatoria en Bonita. La emergencia quedó sin publicar; probá de nuevo."
        ) from exc

    # Siempre UTC: SQLite descarta la zona y guardaría la hora local como si fuera UTC.
    emergencia.ventana_ofertas_fin = ventana_fin.astimezone(timezone.utc)
    emergencia.estado = EstadoEmergencia.CONVOCATORIA
    db.commit()
    db.refresh(emergencia)
    return emergencia


def finalizar_revision_en_bonita(settings: Settings, case_id: int, actor: Usuario) -> None:
    admin = BonitaClient(settings.bonita_base_url, settings.bonita_timeout_seconds)
    admin.login(settings.bonita_username, settings.bonita_password)
    revisar = admin.find_task(case_id, TAREA_REVISAR)
    if revisar is None:
        if admin.find_task(case_id, TAREA_PUBLICAR) is not None:
            return
        raise BonitaError(f"El caso {case_id} no está en '{TAREA_REVISAR}…'.")

    coordinador = BonitaClient(settings.bonita_base_url, settings.bonita_timeout_seconds)
    coordinador.login(actor.username, settings.bonita_user_password)
    coordinador.complete_task_as_self(revisar["id"])


def publicar_en_bonita(settings: Settings, case_id: int, ventana_fin: datetime, actor: Usuario) -> None:
    """Completa "Revisar…" (si sigue pendiente), setea la ventana y completa "Publicar…"."""
    admin = BonitaClient(settings.bonita_base_url, settings.bonita_timeout_seconds)
    admin.login(settings.bonita_username, settings.bonita_password)
    coordinador = BonitaClient(settings.bonita_base_url, settings.bonita_timeout_seconds)
    coordinador.login(actor.username, settings.bonita_user_password)

    # Si un intento anterior se cortó después de completar "Revisar…", el caso ya está en
    # "Publicar…": se sigue desde ahí en vez de fallar.
    revisar = admin.find_task(case_id, TAREA_REVISAR)
    if revisar is not None:
        coordinador.complete_task_as_self(revisar["id"])

    publicar = admin.wait_for_task(case_id, TAREA_PUBLICAR)
    if publicar is None:
        raise BonitaError(f"El caso {case_id} no está en '{TAREA_PUBLICAR}…'; no se puede publicar.")

    # Antes de completar "Publicar…": el timer lee la variable al activarse "Cargar Ofertas de Ayuda".
    admin.set_case_variable(
        case_id, "ventanaOfertasISO", ventana_fin.isoformat(timespec="seconds"), "java.lang.String"
    )
    coordinador.complete_task_as_self(publicar["id"])
