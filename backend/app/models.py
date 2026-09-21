import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Rol(str, enum.Enum):
    MUNICIPIO = "municipio"
    COORDINADOR = "coordinador"
    ONG = "ong"
    AUDITOR = "auditor"


class EstadoEmergencia(str, enum.Enum):
    BORRADOR = "borrador"
    REGISTRADA = "registrada"
    LOTES_PUBLICADOS = "lotes_publicados"
    EN_CONVOCATORIA = "en_convocatoria"
    CERRADA = "cerrada"


class TipoLote(str, enum.Enum):
    PRINCIPAL = "principal"
    APOYO = "apoyo"


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    nombre: Mapped[str] = mapped_column(String(120))
    rol: Mapped[Rol] = mapped_column(Enum(Rol, name="rol"), index=True)
    organizacion: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    emergencias: Mapped[list["Emergencia"]] = relationship(back_populates="municipio")
    ofertas: Mapped[list["Oferta"]] = relationship(back_populates="ong")


class Emergencia(Base):
    __tablename__ = "emergencias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    municipio_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    tipo_desastre: Mapped[str] = mapped_column(String(80))
    nivel_gravedad: Mapped[str] = mapped_column(String(40))
    zona_afectada: Mapped[str] = mapped_column(String(200))
    descripcion: Mapped[str] = mapped_column(Text)
    estado: Mapped[EstadoEmergencia] = mapped_column(
        Enum(EstadoEmergencia, name="estado_emergencia"),
        default=EstadoEmergencia.REGISTRADA,
    )
    bonita_case_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ventana_ofertas_iso: Mapped[str | None] = mapped_column(String(32), nullable=True)
    plazo_adjudicacion_iso: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    municipio: Mapped[Usuario] = relationship(back_populates="emergencias")
    lotes: Mapped[list["Lote"]] = relationship(back_populates="emergencia", cascade="all, delete-orphan")
    ofertas: Mapped[list["Oferta"]] = relationship(back_populates="emergencia", cascade="all, delete-orphan")


class Lote(Base):
    __tablename__ = "lotes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    emergencia_id: Mapped[int] = mapped_column(ForeignKey("emergencias.id"), index=True)
    recurso: Mapped[str] = mapped_column(String(120))
    cantidad: Mapped[int] = mapped_column(Integer)
    tipo: Mapped[TipoLote] = mapped_column(Enum(TipoLote, name="tipo_lote"), default=TipoLote.PRINCIPAL)
    publicado: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    emergencia: Mapped[Emergencia] = relationship(back_populates="lotes")
    ofertas: Mapped[list["Oferta"]] = relationship(back_populates="lote")


class Oferta(Base):
    __tablename__ = "ofertas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    emergencia_id: Mapped[int] = mapped_column(ForeignKey("emergencias.id"), index=True)
    lote_id: Mapped[int] = mapped_column(ForeignKey("lotes.id"), index=True)
    ong_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    detalle_recursos: Mapped[str] = mapped_column(Text)
    cantidad_ofrecida: Mapped[int] = mapped_column(Integer)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    emergencia: Mapped[Emergencia] = relationship(back_populates="ofertas")
    lote: Mapped[Lote] = relationship(back_populates="ofertas")
    ong: Mapped[Usuario] = relationship(back_populates="ofertas")
