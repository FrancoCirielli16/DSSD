from pydantic import BaseModel, ConfigDict, Field

from app.models import Gravedad

ETIQUETAS = {
    "tipo": "Tipo",
    "nivel_gravedad": "Nivel de gravedad",
    "zona_afectada": "Zona afectada",
    "descripcion": "Descripción",
}


class EmergenciaIn(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "tipo": "Inundación",
                "nivel_gravedad": "ALTA",
                "zona_afectada": "Rosario",
                "descripcion": "Evacuación preventiva de familias",
            }
        },
    )

    # Largos máximos = los de las columnas (Postgres los hace cumplir; SQLite no).
    tipo: str = Field(
        min_length=1,
        max_length=40,
        description="Tipo de emergencia",
        examples=["Inundación"],
    )
    nivel_gravedad: Gravedad = Field(description="Nivel de gravedad de la emergencia", examples=["ALTA"])
    zona_afectada: str = Field(
        min_length=1,
        max_length=200,
        description="Zona geográfica afectada",
        examples=["Rosario"],
    )
    descripcion: str = Field(
        min_length=1,
        max_length=2000,
        description="Descripción operativa",
        examples=["Evacuación preventiva de familias"],
    )
