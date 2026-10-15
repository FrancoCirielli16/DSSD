
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import Settings, get_settings
from app.core.deps import require_role
from app.core.security import verify_password
from app.core.labels import ROL_LABEL, TIPO_LABEL
from app.db import get_db
from app.integrations.nacional import NacionalClient, NacionalError, get_nacional
from app.models import Emergencia, Oferta, Rol, Usuario
from app.schemas.api import (
    EmergenciaOut,
    LoginIn,
    LoteOut,
    OfertaIn,
    OfertaItemOut,
    OfertaOut,
    PublicarIn,
    TipoRecursoOut,
    UsuarioOut,
)
from app.schemas.emergencias import EmergenciaIn
from app.schemas.lotes import LoteIn, PublicacionIn
from app.seed import DEMO_PASSWORD, DEMO_USERS
from app.services.emergencias import (
    AltaEmergenciaError,
    emergencia_visible,
    emergencias_visibles,
    registrar_emergencia,
    tarea_ong_en_bonita,
)
from app.services.ofertas import OfertaError, publicar_oferta
from app.services.lotes import (
    LoteError,
    PublicacionError,
    agregar_lote,
    borrar_lote,
    publicar_convocatoria,
)

router = APIRouter(prefix="/api")


def _load_emergencia(db: Session, emergencia_id: int) -> Emergencia | None:
    return db.scalar(
        select(Emergencia)
        .where(Emergencia.id == emergencia_id)
        .options(selectinload(Emergencia.lotes), selectinload(Emergencia.municipio))
    )


def _emergencia_out(e: Emergencia) -> EmergenciaOut:
    return EmergenciaOut(
        id=e.id,
        tipo=e.tipo,
        nivel_gravedad=e.nivel_gravedad,
        zona_afectada=e.zona_afectada,
        descripcion=e.descripcion,
        estado=e.estado,
        bonita_case_id=e.bonita_case_id,
        ventana_ofertas_fin=e.ventana_ofertas_fin,
        creada_en=e.creada_en,
        municipio_nombre=e.municipio.nombre if e.municipio else None,
        municipio_provincia=e.municipio.provincia if e.municipio else None,
        lotes=[LoteOut.model_validate(l) for l in e.lotes],
    )


def _require_visible(db: Session, user: Usuario, emergencia_id: int) -> Emergencia:
    emergencia = _load_emergencia(db, emergencia_id)
    if emergencia is None or emergencia_visible(db, user, emergencia_id) is None:
        raise HTTPException(status_code=404, detail="Emergencia no encontrada")
    return emergencia


@router.get(
    "/meta",
    tags=["Health"],
    summary="Obtener metadatos de la aplicación",
    description="Retorna roles, tipos y configuración pública para clientes locales.",
    responses={200: {"description": "Metadatos obtenidos"}},
)
def meta(settings: Settings = Depends(get_settings)):
    demo = None
    if settings.show_demo_users:
        demo = {
            "password": DEMO_PASSWORD,
            "users": [
                {"username": u, "rol": rol.value, "label": ROL_LABEL[rol.value]}
                for u, _, rol, _ in DEMO_USERS
            ],
        }
    return {"tipos": TIPO_LABEL, "roles": ROL_LABEL, "demo": demo}


@router.post(
    "/auth/login",
    response_model=UsuarioOut,
    tags=["Autenticación"],
    summary="Iniciar sesión",
    description="Autentica un usuario y crea su sesión HTTP.",
    responses={200: {"description": "Sesión iniciada"}, 401: {"description": "Credenciales inválidas"}, 422: {"description": "Datos inválidos"}},
)
def api_login(body: LoginIn, request: Request, db: Session = Depends(get_db)):
    user = db.scalar(select(Usuario).where(Usuario.username == body.username.strip()))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    request.session.clear()
    request.session.update({"uid": user.id, "nombre": user.nombre, "rol": user.rol.value})
    return user


@router.post(
    "/auth/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Autenticación"],
    summary="Cerrar sesión",
    description="Invalida la sesión HTTP actual.",
    responses={204: {"description": "Sesión cerrada"}},
)
def api_logout(request: Request):
    request.session.clear()


@router.get(
    "/auth/me",
    response_model=UsuarioOut,
    tags=["Autenticación"],
    summary="Consultar usuario actual",
    description="Retorna la identidad del usuario autenticado.",
    responses={200: {"description": "Usuario obtenido"}, 401: {"description": "No autenticado"}, 403: {"description": "Rol no autorizado"}},
)
def api_me(user: Usuario = Depends(require_role())):
    return user


@router.get(
    "/emergencias",
    response_model=list[EmergenciaOut],
    tags=["Emergencias"],
    summary="Listar emergencias",
    description="Lista las emergencias visibles para el usuario actual.",
    responses={200: {"description": "Emergencias obtenidas"}, 401: {"description": "No autenticado"}, 403: {"description": "Rol no autorizado"}},
)
def api_listar(
    user: Usuario = Depends(require_role()),
    db: Session = Depends(get_db),
):
    items = emergencias_visibles(db, user)
    out: list[EmergenciaOut] = []
    for e in items:
        full = _load_emergencia(db, e.id)
        if full:
            out.append(_emergencia_out(full))
    return out


@router.post(
    "/emergencias",
    response_model=EmergenciaOut,
    status_code=201,
    tags=["Emergencias"],
    summary="Crear emergencia",
    description="Registra una emergencia y la prepara para gestionar sus lotes.",
    responses={201: {"description": "Emergencia creada"}, 400: {"description": "Datos o estado inválidos"}, 401: {"description": "No autenticado"}, 403: {"description": "Se requiere rol de municipio"}, 502: {"description": "Bonita no disponible"}, 422: {"description": "Datos inválidos"}},
)
def api_crear(
    body: EmergenciaIn,
    user: Usuario = Depends(require_role(Rol.MUNICIPIO)),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    try:
        emergencia = registrar_emergencia(db, settings, operador=user, **body.model_dump())
    except AltaEmergenciaError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    full = _load_emergencia(db, emergencia.id)
    return _emergencia_out(full or emergencia)


@router.get(
    "/emergencias/{emergencia_id}",
    response_model=EmergenciaOut,
    tags=["Emergencias"],
    summary="Obtener emergencia",
    description="Retorna el detalle de una emergencia visible para el usuario.",
    responses={200: {"description": "Emergencia obtenida"}, 401: {"description": "No autenticado"}, 404: {"description": "Emergencia inexistente"}},
)
def api_detalle(
    emergencia_id: int,
    user: Usuario = Depends(require_role()),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    emergencia = _require_visible(db, user, emergencia_id)
    out = _emergencia_out(emergencia)
    out.tarea_bonita = tarea_ong_en_bonita(settings, emergencia, user)
    return out


NACIONAL_CAIDO = "El Sistema Nacional no responde; probá de nuevo en un momento."


@router.get(
    "/tipos-recurso",
    response_model=list[TipoRecursoOut],
    tags=["Catálogo"],
    summary="Listar tipos de recurso",
    description="Obtiene el catálogo del Sistema Nacional para crear lotes.",
    responses={200: {"description": "Catálogo obtenido"}, 503: {"description": "Sistema Nacional no disponible"}},
)
def api_tipos_recurso(
    user: Usuario = Depends(require_role()),
    nacional: NacionalClient = Depends(get_nacional),
):
    """Catálogo de recursos del Sistema Nacional, para elegir el tipo de cada lote."""
    try:
        return nacional.tipos_recurso()
    except NacionalError as exc:
        raise HTTPException(status_code=503, detail=NACIONAL_CAIDO) from exc


@router.post(
    "/emergencias/{emergencia_id}/lotes",
    response_model=LoteOut,
    status_code=201,
    tags=["Lotes"],
    summary="Agregar lote a una emergencia",
    description="Crea un lote usando un tipo de recurso válido del catálogo nacional.",
    responses={201: {"description": "Lote creado"}, 400: {"description": "Lote inválido"}, 401: {"description": "No autenticado"}, 403: {"description": "Se requiere rol de coordinador"}, 404: {"description": "Emergencia inexistente"}, 503: {"description": "Sistema Nacional no disponible"}, 422: {"description": "Datos inválidos"}},
)
def api_crear_lote(
    emergencia_id: int,
    body: LoteIn,
    user: Usuario = Depends(require_role(Rol.COORDINADOR)),
    db: Session = Depends(get_db),
    nacional: NacionalClient = Depends(get_nacional),
):
    emergencia = _require_visible(db, user, emergencia_id)
    try:
        lote = agregar_lote(db, emergencia, body, nacional)
    except LoteError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except NacionalError as exc:
        raise HTTPException(status_code=503, detail=NACIONAL_CAIDO) from exc
    return lote


@router.delete(
    "/emergencias/{emergencia_id}/lotes/{lote_id}",
    status_code=204,
    tags=["Lotes"],
    summary="Eliminar lote",
    description="Elimina un lote de una emergencia antes de su publicación.",
    responses={204: {"description": "Lote eliminado"}, 400: {"description": "Lote no puede eliminarse"}, 401: {"description": "No autenticado"}, 403: {"description": "Se requiere rol de coordinador"}, 404: {"description": "Emergencia o lote inexistente"}},
)
def api_borrar_lote(
    emergencia_id: int,
    lote_id: int,
    user: Usuario = Depends(require_role(Rol.COORDINADOR)),
    db: Session = Depends(get_db),
):
    emergencia = _require_visible(db, user, emergencia_id)
    try:
        borrar_lote(db, emergencia, lote_id)
    except LoteError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/emergencias/{emergencia_id}/publicar",
    response_model=EmergenciaOut,
    tags=["Emergencias"],
    summary="Publicar convocatoria",
    description="Abre la ventana de recepción de ofertas de una emergencia.",
    responses={200: {"description": "Convocatoria publicada"}, 400: {"description": "Estado o ventana inválida"}, 401: {"description": "No autenticado"}, 403: {"description": "Se requiere rol de coordinador"}, 404: {"description": "Emergencia inexistente"}},
)
def api_publicar(
    emergencia_id: int,
    body: PublicarIn,
    user: Usuario = Depends(require_role(Rol.COORDINADOR)),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    emergencia = _require_visible(db, user, emergencia_id)
    try:
        publicada = publicar_convocatoria(
            db,
            settings,
            emergencia=emergencia,
            coordinador=user,
            ventana_fin=PublicacionIn(ventana_fin=body.ventana_fin).ventana_fin,
        )
    except PublicacionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    full = _load_emergencia(db, publicada.id)
    return _emergencia_out(full or publicada)


def _oferta_out(o: Oferta) -> OfertaOut:
    items = [OfertaItemOut.model_validate(i) for i in o.items if i.version == o.version_actual]
    return OfertaOut(
        id=o.id,
        emergencia_id=o.emergencia_id,
        ong_id=o.ong_id,
        ong_nombre=o.ong.nombre,
        version_actual=o.version_actual,
        items=items,
        retirada=not items,
    )


@router.get(
    "/emergencias/{emergencia_id}/ofertas",
    response_model=list[OfertaOut],
    tags=["Ofertas"],
    summary="Listar ofertas",
    description="Lista las ofertas visibles para la emergencia y el usuario actual.",
    responses={200: {"description": "Ofertas obtenidas"}, 401: {"description": "No autenticado"}, 404: {"description": "Emergencia inexistente"}},
)
def api_listar_ofertas(
    emergencia_id: int,
    user: Usuario = Depends(require_role()),
    db: Session = Depends(get_db),
):
    _require_visible(db, user, emergencia_id)
    query = select(Oferta).where(Oferta.emergencia_id == emergencia_id)
    if user.rol is Rol.ONG:  # una ONG no ve las ofertas de las demás
        query = query.where(Oferta.ong_id == user.ong_id)
    ofertas = db.scalars(query.options(selectinload(Oferta.items), selectinload(Oferta.ong))).all()
    return [_oferta_out(o) for o in ofertas]


@router.post(
    "/emergencias/{emergencia_id}/ofertas",
    response_model=OfertaOut,
    status_code=201,
    tags=["Ofertas"],
    summary="Publicar oferta de ayuda",
    description="Guarda una nueva versión completa de la oferta de una ONG.",
    responses={201: {"description": "Oferta publicada"}, 400: {"description": "Oferta inválida"}, 401: {"description": "No autenticado"}, 403: {"description": "Se requiere rol de ONG"}, 404: {"description": "Emergencia inexistente"}, 503: {"description": "Sistema Nacional no disponible"}, 422: {"description": "Datos inválidos"}},
)
def api_crear_oferta(
    emergencia_id: int,
    body: OfertaIn,
    user: Usuario = Depends(require_role(Rol.ONG)),
    db: Session = Depends(get_db),
    nacional: NacionalClient = Depends(get_nacional),
):
    """Cada envío es la oferta completa: una versión nueva con todos sus ítems (T-12)."""
    emergencia = _require_visible(db, user, emergencia_id)
    try:
        oferta = publicar_oferta(db, nacional, emergencia=emergencia, ong=user.ong, items=body.items)
    except OfertaError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except NacionalError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail=NACIONAL_CAIDO) from exc
    return _oferta_out(oferta)
