from opennem.db import db_connect
from opennem.db.models.bom import metadata as metadata_bom
from opennem.db.models.opennem import metadata as metadata_opennem

if __name__ == "__main__":
    engine = db_connect()

    metadata_opennem.drop_all(engine)
    metadata_opennem.create_all(engine)
    print("Created opennem schema.")

    metadata_bom.drop_all(engine)
    metadata_bom.create_all(engine)
    print("Created bom schema ....")

    print("Done initdb.")
