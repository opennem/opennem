from opennem.db.models.opennem import (
    Base,
    WemBalancingSummary,
    WemFacility,
    WemFacilityScada,
    WemParticipant,
    metadata,
)

if __name__ == "__main__":
    from opennem.db import db_connect

    engine = db_connect()
    metadata.drop_all(engine)
    metadata.create_all(engine)
