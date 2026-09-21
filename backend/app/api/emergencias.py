from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Emergencia, EstadoEmergencia, Rol, Usuario
from app.schemas import EmergenciaCreate, EmergenciaOut
from app.security import get_current_user
from app.services.bonita import BonitaError, start_rescue_sync_case

router = APIRouter(prefix="/api/emergencias", tags=["emergencias"])


@router.post("", response_model=EmergenciaOut, status_code=status.HTTP_201_CREATED)
def crear_emergencia(
    body: EmergenciaCreate,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> Emergencia:
    if user.rol != Rol.MUNICIPIO:
        raise HTTPException(status_code=403, detail="Solo el Operador Municipal puede registrar emergencias")

    emergencia = Emergencia(
        municipio_id=user.id,
        tipo_desastre=body.tipo_desastre,
        nivel_gravedad=body.nivel_gravedad,
        zona_afectada=body.zona_afectada,
        descripcion=body.descripcion,
        estado=EstadoEmergencia.REGISTRADA,
        ventana_ofertas_iso=body.ventana_ofertas_iso,
    )
    db.add(emergencia)
    db.commit()
    db.refresh(emergencia)

    # HU-2.4: si Bonita no está arriba, la emergencia local se conserva igual.
    try:
        case_id = start_rescue_sync_case(
            emergencia_id=emergencia.id,
            municipio_id=user.id,
            nivel_gravedad=emergencia.nivel_gravedad,
            ventana_ofertas_iso=emergencia.ventana_ofertas_iso or "PT72H",
        )
        emergencia.bonita_case_id = case_id
        db.commit()
        db.refresh(emergencia)
    except BonitaError:
        # ConnectError u otros fallos de red mientras Studio/Engine no corre.
        pass

    return emergencia


@router.get("", response_model=list[EmergenciaOut])
def listar_emergencias(
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> list[Emergencia]:
    q = db.query(Emergencia).order_by(Emergencia.id.desc())
    if user.rol == Rol.MUNICIPIO:
        q = q.filter(Emergencia.municipio_id == user.id)
    return q.all()


@router.get("/{emergencia_id}", response_model=EmergenciaOut)
def obtener_emergencia(
    emergencia_id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> Emergencia:
    emergencia = db.get(Emergencia, emergencia_id)
    if not emergencia:
        raise HTTPException(status_code=404, detail="Emergencia no encontrada")
    if user.rol == Rol.MUNICIPIO and emergencia.municipio_id != user.id:
        raise HTTPException(status_code=403, detail="Sin acceso a esta emergencia")
    return emergencia
