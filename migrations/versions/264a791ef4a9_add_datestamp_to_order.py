"""add datestamp to order

Revision ID: 264a791ef4a9
Revises: b9470b6a9e57
Create Date: 2022-08-14 13:53:34.590591

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '264a791ef4a9'
down_revision = 'b9470b6a9e57'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('order', sa.Column('datestamp', sa.Date(), nullable=True))
    op.create_index(op.f('ix_order_datestamp'), 'order', ['datestamp'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_order_datestamp'), table_name='order')
    op.drop_column('order', 'datestamp')
    # ### end Alembic commands ###
