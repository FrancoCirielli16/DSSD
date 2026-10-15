import enum
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field
from app.models import CategoriaRecurso, EstadoOng, Riesgo, EstadoCompromiso


class TipoRecursoOut(BaseModel):
    codigo: str
    nombre: str
    categoria: CategoriaRecurso
    unidad: str
    certificacion_requerida: str | None


class CertificacionOut(BaseModel):
    codigo: str
    nombre: str
    descripcion: str | None
    tipos_recurso: list[str]  # códigos de los tipos de recurso que habilita


class OngOut(BaseModel):
    cuit: str
    nombre: str
    estado: EstadoOng

    model_config = ConfigDict(from_attributes=True)


class OngCertificacionOut(BaseModel):
    codigo: str
    nombre: str
    riesgo_max: Riesgo
    vence_el: date
    vigente: bool


class InventarioOut(BaseModel):
    tipo_recurso: str
    nombre: str
    unidad: str
    cantidad_total: int
    cantidad_comprometida: int
    disponible: int
    # Hasta qué riesgo puede operar la ONG este recurso hoy; None si no tiene certificación vigente.
    riesgo_permitido: Riesgo | None


class FichaOngOut(OngOut):
    certificaciones: list[OngCertificacionOut]
    inventario: list[InventarioOut]


class DisponibilidadOngOut(BaseModel):
    cuit: str
    ong: str
    disponible: int


class DisponibilidadOut(BaseModel):
    tipo_recurso: str
    nombre: str
    unidad: str
    cantidad_total: int
    cantidad_comprometida: int
    disponible: int
    por_ong: list[DisponibilidadOngOut]


class InventarioItemIn(BaseModel):
    tipo_recurso: str = Field(description="Código del tipo de recurso", examples=["PARAMEDICO"])
    cantidad_total: int = Field(ge=0, description="Stock total declarado", examples=[10])


class InventarioIn(BaseModel):
    items: list[InventarioItemIn] = Field(min_length=1, description="Stock por tipo de recurso")

    model_config = ConfigDict(json_schema_extra={"example": {"items": [{"tipo_recurso": "PARAMEDICO", "cantidad_total": 10}]}})


class NivelCompetencia(str, enum.Enum):
    PLENA = "PLENA"  # certificación vigente y suficiente para la gravedad
    PARCIAL = "PARCIAL"  # certificación vigente pero de menor riesgo que la gravedad
    SUPERVISADA = "SUPERVISADA"  # sin certificación vigente (o ONG no habilitada)


class Asignacion(str, enum.Enum):
    PRINCIPAL = "PRINCIPAL"
    APOYO = "APOYO"


class ItemValidacionIn(BaseModel):
    cuit: str = Field(description="CUIT de la ONG", examples=["30-54666544-5"])
    tipo_recurso: str = Field(description="Código del recurso", examples=["PARAMEDICO"])
    cantidad: int = Field(gt=0, description="Cantidad solicitada", examples=[4])


class ValidacionIn(BaseModel):
    gravedad: Riesgo = Field(description="Riesgo de la emergencia", examples=["ALTO"])
    items: list[ItemValidacionIn] = Field(min_length=1, description="Recursos a validar")

    model_config = ConfigDict(json_schema_extra={"example": {"gravedad": "ALTO", "items": [{"cuit": "30-54666544-5", "tipo_recurso": "PARAMEDICO", "cantidad": 4}]}})


class ResultadoValidacionOut(BaseModel):
    cuit: str
    ong: str | None  # None = ONG no registrada
    tipo_recurso: str
    nombre_recurso: str
    unidad: str
    solicitado: int
    disponible: int
    alcanza: bool
    nivel: NivelCompetencia
    riesgo_permitido: Riesgo | None
    asignacion_sugerida: Asignacion
    observaciones: list[str]


class ValidacionOut(BaseModel):
    alcanza_todo: bool
    resultados: list[ResultadoValidacionOut]


class CierreItemIn(BaseModel):
    tipo_recurso: str = Field(description="Código del recurso a liberar", examples=["PARAMEDICO"])
    cantidad: int = Field(gt=0, description="Cantidad comprometida a liberar", examples=[4])


class CierreIn(BaseModel):
    cuit: str = Field(min_length=1, max_length=13, description="CUIT de la ONG", examples=["30-54666544-5"])
    referencia: str = Field(min_length=1, max_length=80, description="Referencia idempotente del cierre", examples=["emergencia-12"])
    items: list[CierreItemIn] = Field(min_length=1, description="Recursos a liberar")

    model_config = ConfigDict(json_schema_extra={"example": {"cuit": "30-54666544-5", "referencia": "emergencia-12", "items": [{"tipo_recurso": "PARAMEDICO", "cantidad": 4}]}})


class CierreItemOut(BaseModel):
    tipo_recurso: str
    nombre: str
    unidad: str
    cantidad_liberada: int
    cantidad_total: int
    cantidad_comprometida: int
    disponible: int


class CierreOut(BaseModel):
    id: int
    cuit: str
    ong: str
    referencia: str
    informado_en: datetime
    items: list[CierreItemOut]


class AdjudicacionItemIn(BaseModel):
    inventario_id: int = Field(gt=0, description="Identificador de inventario a comprometer", examples=[21])
    cantidad: int = Field(gt=0, description="Cantidad a adjudicar", examples=[4])


class AdjudicacionIn(BaseModel):
    referencia_id: str = Field(min_length=1, max_length=80, description="Referencia única para idempotencia", examples=["emergencia-12-ong-7"])
    ong_id: int = Field(gt=0, description="Identificador de la ONG", examples=[7])
    emergencia_id: int = Field(gt=0, description="Identificador de la emergencia", examples=[12])
    items: list[AdjudicacionItemIn] = Field(min_length=1, description="Inventarios y cantidades a comprometer")

    model_config = ConfigDict(json_schema_extra={"example": {"referencia_id": "emergencia-12-ong-7", "ong_id": 7, "emergencia_id": 12, "items": [{"inventario_id": 21, "cantidad": 4}]}})


class AdjudicacionItemOut(BaseModel):
    inventario_id: int
    cantidad: int


class AdjudicacionOut(BaseModel):
    id: int
    referencia_id: str
    ong_id: int
    emergencia_id: int
    fecha_creacion: datetime
    items: list[AdjudicacionItemOut]
class ItemCompromisoIn(BaseModel):
    tipo_recurso_id: int = Field(gt=0, description="Identificador del tipo de recurso", examples=[3])
    cantidad: int = Field(gt=0, description="Cantidad comprometida", examples=[4])

class CompromisoIn(BaseModel):
    emergencia_id: int = Field(gt=0, description="Identificador de la emergencia", examples=[12])
    ong_id: int = Field(gt=0, description="Identificador de la ONG", examples=[7])
    items: list[ItemCompromisoIn] = Field(min_length=1, description="Recursos comprometidos")

class CompromisoItemOut(BaseModel):
    tipo_recurso_id: int
    cantidad: int
    model_config = ConfigDict(from_attributes=True)

class CompromisoOut(BaseModel):
    id: int
    emergencia_id: int
    ong_id: int
    estado: EstadoCompromiso
    items: list[CompromisoItemOut]
    model_config = ConfigDict(from_attributes=True)

class LiberacionOut(BaseModel):
    compromiso_id: int
    estado: EstadoCompromiso
    mensaje: str
