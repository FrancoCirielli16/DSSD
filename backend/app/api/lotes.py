from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Emergencia, EstadoEmergencia, Lote, Rol, Usuario
from app.schemas import EmergenciaOut, LoteCreate, LoteOut, PublicarLotesIn
from app.security import get_current_user

router = APIRouter(tags=["lotes"])


@router.post(
    "/api/emergencias/{emergencia_id}/lotes",
    response_model=LoteOut,
    status_code=status.HTTP_201_CREATED,
)
def crear_lote(
    emergencia_id: int,
    body: LoteCreate,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> Lote:
    if user.rol != Rol.COORDINADOR:
        raise HTTPException(status_code=403, detail="Solo el Centro Coordinador puede crear lotes")

    emergencia = db.get(Emergencia, emergencia_id)
    if not emergencia:
        raise HTTPException(status_code=404, detail="Emergencia no encontrada")

    lote = Lote(
        emergencia_id=emergencia_id,
        recurso=body.recurso,
        cantidad=body.cantidad,
        tipo=body.tipo,
    )
    db.add(lote)
    db.commit()
    db.refresh(lote)
    return lote


@router.get("/api/emergencias/{emergencia_id}/lotes", response_model=list[LoteOut])
def listar_lotes(
    emergencia_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> list[Lote]:
    emergencia = db.get(Emergencia, emergencia_id)
    if not emergencia:
        raise HTTPException(status_code=404, detail="Emergencia no encontrada")
    return db.query(Lote).filter(Lote.emergencia_id == emergencia_id).order_by(Lote.id).all()


@router.post("/api/emergencias/{emergencia_id}/publicar", response_model=EmergenciaOut)
def publicar_convocatoria(
    emergencia_id: int,
    body: PublicarLotesIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> Emergencia:
    if user.rol != Rol.COORDINADOR:
        raise HTTPException(status_code=403, detail="Solo el Centro Coordinador puede publicar")

    emergencia = db.get(Emergencia, emergencia_id)
    if not emergencia:
        raise HTTPException(status_code=404, detail="Emergencia no encontrada")

    lotes = db.query(Lote).filter(Lote.emergencia_id == emergencia_id).all()
    if not lotes:
        raise HTTPException(status_code=400, detail="No hay lotes para publicar")

    for lote in lotes:
        lote.publicado = True

    emergencia.ventana_ofertas_iso = body.ventana_ofertas_iso
    emergencia.plazo_adjudicacion_iso = body.plazo_adjudicacion_iso
    emergencia.estado = EstadoEmergencia.EN_CONVOCATORIA
    db.commit()
    db.refresh(emergencia)
    return emergencia
