from opennem.db import db_connect
from opennem.db.models.bom import metadata as metadata_bom
from opennem.db.models.opennem import WemFacilityScada, metadata

if __name__ == "__main__":
    print("Initdb.")

    engine = db_connect()
    print("Connected.")

    print("Opennem init.")
    metadata.drop_all(engine)
    print("Creating....")
    metadata.create_all(engine)
    print("Done.")

    print("BOM init.")
    metadata_bom.drop_all(engine)
    print("Creating....")
    metadata_bom.create_all(engine)
    print("Done.")
