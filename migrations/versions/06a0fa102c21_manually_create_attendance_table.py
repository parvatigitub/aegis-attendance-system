"""Manually create attendance table

Revision ID: 06a0fa102c21
Revises: 
Create Date: 2025-07-25 09:02:48.158655

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '06a0fa102c21'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'attendance',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=10), nullable=False),
        sa.Column('overtime_hours', sa.Float(), nullable=True),
        sa.Column('marked_by', sa.String(length=50), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
    )



def downgrade():
    op.drop_table('attendance')
