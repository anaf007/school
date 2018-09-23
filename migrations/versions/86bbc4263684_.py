"""empty message

Revision ID: 86bbc4263684
Revises: 69bdd979a260
Create Date: 2018-09-15 19:01:09.910476

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '86bbc4263684'
down_revision = '69bdd979a260'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('address', sa.String(length=200), nullable=True))
    op.add_column('users', sa.Column('car_number', sa.String(length=80), nullable=True))
    op.add_column('users', sa.Column('id_number', sa.String(length=80), nullable=True))
    op.add_column('users', sa.Column('name', sa.String(length=80), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'name')
    op.drop_column('users', 'id_number')
    op.drop_column('users', 'car_number')
    op.drop_column('users', 'address')
    # ### end Alembic commands ###