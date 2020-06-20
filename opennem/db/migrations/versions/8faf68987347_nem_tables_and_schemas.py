"""nem tables and schemas

Revision ID: 8faf68987347
Revises: 01d74b813948
Create Date: 2020-06-21 01:17:04.081725

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8faf68987347"
down_revision = "01d74b813948"
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_opennem():
    pass


def downgrade_opennem():
    pass
