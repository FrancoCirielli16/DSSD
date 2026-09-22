from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import TipoLote

ETIQUETAS = {
    "recurso": "Recurso",
    "cantidad": "Cantidad",
    "unidad": "Unidad",
    "tipo": "Tipo de lote",
    "ventana_fin": "Cierre de la ventana de ofertas",
}


class LoteIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    recurso: str = Field(min_length=1, max_length=120)
    cantidad: int = Field(gt=0)
    unidad: str = Field(min_length=1, max_length=30)
    tipo: TipoLote = TipoLote.PRINCIPAL


class PublicacionIn(BaseModel):
    """La ventana la elige el Coordinador al publicar; el timer de Bonita la lee al activarse
    `Cargar Ofertas de Ayuda`, así que una fecha pasada cerraría la convocatoria al instante."""

    ventana_fin: datetime
