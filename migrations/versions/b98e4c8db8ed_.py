"""empty message

Revision ID: b98e4c8db8ed
Revises: 365684c44da1
Create Date: 2018-03-04 16:16:02.214088

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'b98e4c8db8ed'
down_revision = '365684c44da1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('grades', sa.Column('school', sa.Integer(), nullable=True))
    op.drop_constraint(u'grades_ibfk_1', 'grades', type_='foreignkey')
    op.create_foreign_key(None, 'grades', 'schools', ['school'], ['id'])
    op.drop_column('grades', 'schools')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('grades', sa.Column('schools', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'grades', type_='foreignkey')
    op.create_foreign_key(u'grades_ibfk_1', 'grades', 'schools', ['schools'], ['id'])
    op.drop_column('grades', 'school')
    # ### end Alembic commands ###
