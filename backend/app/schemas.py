from datetime import datetime

from pydantic import BaseModel, Field

from app.models import EstadoEmergencia, Rol, TipoLote


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginIn(BaseModel):
    username: str
    password: str


class UsuarioOut(BaseModel):
    id: int
    username: str
    nombre: str
    rol: Rol
    organizacion: str | None = None

    model_config = {"from_attributes": True}


class EmergenciaCreate(BaseModel):
    tipo_desastre: str = Field(min_length=2, max_length=80)
    nivel_gravedad: str = Field(min_length=2, max_length=40)
    zona_afectada: str = Field(min_length=2, max_length=200)
    descripcion: str = Field(min_length=5)
    ventana_ofertas_iso: str = Field(default="PT72H", description="Duración ISO-8601 para Bonita")


class EmergenciaOut(BaseModel):
    id: int
    municipio_id: int
    tipo_desastre: str
    nivel_gravedad: str
    zona_afectada: str
    descripcion: str
    estado: EstadoEmergencia
    bonita_case_id: str | None
    ventana_ofertas_iso: str | None
    plazo_adjudicacion_iso: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class LoteCreate(BaseModel):
    recurso: str = Field(min_length=2, max_length=120)
    cantidad: int = Field(gt=0)
    tipo: TipoLote = TipoLote.PRINCIPAL


class LoteOut(BaseModel):
    id: int
    emergencia_id: int
    recurso: str
    cantidad: int
    tipo: TipoLote
    publicado: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PublicarLotesIn(BaseModel):
    ventana_ofertas_iso: str = "PT72H"
    plazo_adjudicacion_iso: str = "PT48H"


class OfertaCreate(BaseModel):
    lote_id: int
    detalle_recursos: str = Field(min_length=3)
    cantidad_ofrecida: int = Field(gt=0)


class OfertaUpdate(BaseModel):
    detalle_recursos: str | None = None
    cantidad_ofrecida: int | None = Field(default=None, gt=0)


class OfertaOut(BaseModel):
    id: int
    emergencia_id: int
    lote_id: int
    ong_id: int
    detalle_recursos: str
    cantidad_ofrecida: int
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OfertaConsolidadaOut(BaseModel):
    """Payload que Bonita pedirá con GET /api/emergencias/{id}/ofertas (HU-2.5)."""

    emergencia_id: int
    ofertas: list[OfertaOut]
