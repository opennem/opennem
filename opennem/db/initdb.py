from opennem.db import db_connect
from opennem.db.models.bom import metadata as metadata_bom
from opennem.db.models.opennem import metadata as metadata_opennem


def init_opennem(engine):
    metadata_opennem.drop_all(engine)
    metadata_opennem.create_all(engine)


def init_bom(engine):
    metadata_bom.drop_all(engine)
    metadata_bom.create_all(engine)


if __name__ == "__main__":
    engine = db_connect()

    init_opennem(engine)
    init_bom(engine)
