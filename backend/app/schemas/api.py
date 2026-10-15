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
    username: str = Field(min_length=1, description="Nombre de usuario", examples=["coordinador"])
    password: str = Field(min_length=1, description="Contraseña del usuario", examples=["secreto"])

    model_config = ConfigDict(json_schema_extra={"example": {"username": "coordinador", "password": "secreto"}})


class TipoRecursoOut(BaseModel):
    codigo: str
    nombre: str
    categoria: str
    unidad: str
    certificacion_requerida: str | None = None


class LoteOut(BaseModel):
    id: int
    recurso: str
    tipo_recurso: str | None = None
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
    # Tarea que Bonita tiene pendiente para quien consulta; solo el detalle la completa.
    tarea_bonita: str | None = None

    model_config = ConfigDict(from_attributes=True)


class PublicarIn(BaseModel):
    ventana_fin: datetime = Field(description="Fecha y hora UTC de cierre de la convocatoria", examples=["2026-10-16T18:00:00Z"])

    model_config = ConfigDict(json_schema_extra={"example": {"ventana_fin": "2026-10-16T18:00:00Z"}})


class OfertaItemIn(BaseModel):
    lote_id: int = Field(description="Identificador del lote ofrecido", examples=[12])
    recurso: str = Field(min_length=1, max_length=120, description="Detalle del recurso ofrecido", examples=["Paramédicos"])
    cantidad: int = Field(gt=0, description="Cantidad ofrecida", examples=[4])


class OfertaIn(BaseModel):
    # Cada envío es la oferta completa. Lista vacía = retirar la oferta (queda como versión nueva sin ítems).
    items: list[OfertaItemIn] = Field(description="Ítems de la oferta completa; vacío retira la oferta")

    model_config = ConfigDict(json_schema_extra={"example": {"items": [{"lote_id": 12, "recurso": "Paramédicos", "cantidad": 4}]}})


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
    retirada: bool = False  # la versión vigente no tiene ítems

    model_config = ConfigDict(from_attributes=True)
