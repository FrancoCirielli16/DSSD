"""lote.tipo (principal/apoyo) y emergencia.plazo_adjudicacion

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-22
"""
from alembic import op
import sqlalchemy as sa


revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # batch: en SQLite recrea la tabla; en Postgres es un ALTER común. El CHECK va explícito y
    # con nombre para que exista igual en los dos motores y el downgrade pueda borrarlo.
    with op.batch_alter_table('lote') as batch:
        batch.add_column(sa.Column('tipo', sa.String(length=20), nullable=False, server_default='PRINCIPAL'))
        batch.create_check_constraint('tipolote', "tipo IN ('PRINCIPAL', 'APOYO')")
    with op.batch_alter_table('emergencia') as batch:
        batch.add_column(sa.Column('plazo_adjudicacion', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('emergencia') as batch:
        batch.drop_column('plazo_adjudicacion')
    with op.batch_alter_table('lote') as batch:
        batch.drop_constraint('tipolote', type_='check')
        batch.drop_column('tipo')
