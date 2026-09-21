from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Emergencia, EstadoEmergencia, Lote, Oferta, Rol, Usuario
from app.schemas import OfertaConsolidadaOut, OfertaCreate, OfertaOut, OfertaUpdate
from app.security import get_current_user

router = APIRouter(tags=["ofertas"])


@router.post(
    "/api/emergencias/{emergencia_id}/ofertas",
    response_model=OfertaOut,
    status_code=status.HTTP_201_CREATED,
)
def crear_oferta(
    emergencia_id: int,
    body: OfertaCreate,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> Oferta:
    if user.rol != Rol.ONG:
        raise HTTPException(status_code=403, detail="Solo una ONG puede cargar ofertas")

    emergencia = db.get(Emergencia, emergencia_id)
    if not emergencia:
        raise HTTPException(status_code=404, detail="Emergencia no encontrada")
    if emergencia.estado != EstadoEmergencia.EN_CONVOCATORIA:
        raise HTTPException(status_code=400, detail="La convocatoria no está abierta")

    lote = db.get(Lote, body.lote_id)
    if not lote or lote.emergencia_id != emergencia_id or not lote.publicado:
        raise HTTPException(status_code=400, detail="Lote inválido o no publicado")

    oferta = Oferta(
        emergencia_id=emergencia_id,
        lote_id=body.lote_id,
        ong_id=user.id,
        detalle_recursos=body.detalle_recursos,
        cantidad_ofrecida=body.cantidad_ofrecida,
        version=1,
    )
    db.add(oferta)
    db.commit()
    db.refresh(oferta)
    return oferta


@router.put("/api/ofertas/{oferta_id}", response_model=OfertaOut)
def actualizar_oferta(
    oferta_id: int,
    body: OfertaUpdate,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> Oferta:
    oferta = db.get(Oferta, oferta_id)
    if not oferta:
        raise HTTPException(status_code=404, detail="Oferta no encontrada")
    if user.rol != Rol.ONG or oferta.ong_id != user.id:
        raise HTTPException(status_code=403, detail="No podés editar esta oferta")

    emergencia = db.get(Emergencia, oferta.emergencia_id)
    if not emergencia or emergencia.estado != EstadoEmergencia.EN_CONVOCATORIA:
        raise HTTPException(status_code=400, detail="La ventana de ofertas ya cerró")

    if body.detalle_recursos is not None:
        oferta.detalle_recursos = body.detalle_recursos
    if body.cantidad_ofrecida is not None:
        oferta.cantidad_ofrecida = body.cantidad_ofrecida
    oferta.version += 1
    db.commit()
    db.refresh(oferta)
    return oferta


@router.get("/api/emergencias/{emergencia_id}/ofertas", response_model=OfertaConsolidadaOut)
def ofertas_consolidadas(
    emergencia_id: int,
    db: Session = Depends(get_db),
) -> OfertaConsolidadaOut:
    """HU-2.5: endpoint que Bonita consulta al vencer el timer (sin auth de app por ahora)."""
    emergencia = db.get(Emergencia, emergencia_id)
    if not emergencia:
        raise HTTPException(status_code=404, detail="Emergencia no encontrada")
    ofertas = db.query(Oferta).filter(Oferta.emergencia_id == emergencia_id).order_by(Oferta.id).all()
    return OfertaConsolidadaOut(emergencia_id=emergencia_id, ofertas=ofertas)
