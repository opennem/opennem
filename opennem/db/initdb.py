from opennem.db import db_connect
from opennem.db.models.wem import metadata as metadata_wem

if __name__ == "__main__":
    engine = db_connect()
    metadata_wem.drop_all(engine)
    metadata_wem.create_all(engine)
