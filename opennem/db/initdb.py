from opennem.db import db_connect
from opennem.db.models.bom import metadata as metadata_bom
from opennem.db.models.opennem import WemFacilityScada, metadata

if __name__ == "__main__":
    engine = db_connect()
    metadata.drop_all(engine)
    metadata.create_all(engine)

    metadata_bom.drop_all(engine)
    metadata_bom.create_all(engine)
