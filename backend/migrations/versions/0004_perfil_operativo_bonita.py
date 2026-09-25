"""agrega asociaciones de negocio para identidades de Bonita

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-25
"""
from alembic import op
import sqlalchemy as sa


revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "perfil_operativo",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bonita_username", sa.String(length=60), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("municipio_id", sa.Integer(), nullable=True),
        sa.Column("ong_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["municipio_id"], ["municipio.id"]),
        sa.ForeignKeyConstraint(["ong_id"], ["ong.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("bonita_username"),
    )


def downgrade() -> None:
    op.drop_table("perfil_operativo")