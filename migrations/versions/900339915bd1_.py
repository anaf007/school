"""empty message

Revision ID: 900339915bd1
Revises: bcceaf2c584b
Create Date: 2018-09-24 00:05:43.259003

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '900339915bd1'
down_revision = 'bcceaf2c584b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('student_entry_exits',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('student_id', sa.Integer(), nullable=True),
    sa.Column('state', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['student_id'], ['students.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('student_entry_exits')
    # ### end Alembic commands ###
