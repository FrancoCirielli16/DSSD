from datetime import datetime, timezone
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from app.models import EstadoEmergencia, Gravedad, Rol, TipoLote


# SQLite descarta la zona y lo que se guarda siempre es UTC: sin esto el navegador lee la hora
# como local y la muestra corrida.
UtcDatetime = Annotated[
    datetime, AfterValidator(lambda d: d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d)
]


class UsuarioOut(BaseModel):
    id: int
    username: str
    nombre: str
    rol: Rol

    model_config = ConfigDict(from_attributes=True)


class LoginIn(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class BonitaRoleIn(BaseModel):
    role: Rol


class BonitaIdentityOut(BaseModel):
    user_id: str
    username: str
    nombre: str
    grupos: list[str]
    roles: list[str]


class LoteOut(BaseModel):
    id: int
    recurso: str
    cantidad: int
    unidad: str
    tipo: TipoLote

    model_config = ConfigDict(from_attributes=True)


class EmergenciaOut(BaseModel):
    id: int
    tipo: str
    nivel_gravedad: Gravedad
    zona_afectada: str
    descripcion: str
    estado: EstadoEmergencia
    bonita_case_id: int | None
    ventana_ofertas_fin: UtcDatetime | None
    creada_en: UtcDatetime
    municipio_nombre: str | None = None
    municipio_provincia: str | None = None
    lotes: list[LoteOut] = []

    model_config = ConfigDict(from_attributes=True)


class LoteCreateIn(BaseModel):
    recurso: str = Field(min_length=1, max_length=120)
    cantidad: int = Field(gt=0)
    unidad: str = Field(min_length=1, max_length=30)
    tipo: TipoLote = TipoLote.PRINCIPAL


class PublicarIn(BaseModel):
    ventana_fin: datetime


class OfertaItemIn(BaseModel):
    lote_id: int
    recurso: str = Field(min_length=1, max_length=120)
    cantidad: int = Field(gt=0)


class OfertaIn(BaseModel):
    items: list[OfertaItemIn] = Field(min_length=1)


class OfertaItemOut(BaseModel):
    lote_id: int
    recurso: str
    cantidad: int
    version: int

    model_config = ConfigDict(from_attributes=True)


class OfertaOut(BaseModel):
    id: int
    emergencia_id: int
    ong_id: int
    ong_nombre: str
    version_actual: int
    items: list[OfertaItemOut]

    model_config = ConfigDict(from_attributes=True)
