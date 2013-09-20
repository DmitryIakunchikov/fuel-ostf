#    Copyright 2013 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""initial migration

Revision ID: 1fcb29d29e03
Revises: None
Create Date: 2013-06-26 17:40:23.908062

"""

# revision identifiers, used by Alembic.
revision = '1fcb29d29e03'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###

    op.create_table(
        'test_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(length=128), nullable=True),
        sa.Column('data', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'tests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=512), nullable=True),
        sa.Column('status', sa.String(length=128), nullable=True),
        sa.Column('taken', sa.Float(), nullable=True),
        sa.Column('data', sa.Text(), nullable=True),
        sa.Column('test_run_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['test_run_id'], ['test_runs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('tests')
    op.drop_table('test_runs')
    ### end Alembic commands ###
