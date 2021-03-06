"""empty message

Revision ID: 130_acknowledged_at_column
Revises: 120_acknowledged_not_null
Create Date: 2015-06-17 12:55:16.630026

"""

# revision identifiers, used by Alembic.
revision = '130_acknowledged_at_column'
down_revision = '120_acknowledged_not_null'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('audit_events', sa.Column('acknowledged_at', sa.DateTime(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('audit_events', 'acknowledged_at')
    ### end Alembic commands ###
