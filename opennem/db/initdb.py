from opennem.db import db_connect
from opennem.db.models.opennem import metadata as metadata_opennem


def init_opennem(engine):
    metadata_opennem.drop_all(engine)
    metadata_opennem.create_all(engine)


if __name__ == "__main__":
    engine = db_connect()

    init_opennem(engine)
