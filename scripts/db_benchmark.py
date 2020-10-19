"""
    Finding the fastest way to insert CSV streams into a database
    with upserts. Hit on this.

"""

import csv
from io import StringIO
from pathlib import Path

from opennem.db import get_database_engine
from opennem.pipelines.wem.facility_scada import (
    facility_scada_generate_records,
)

scada_test_file = Path(__file__).parent.parent / Path(
    "data/wem/facility-scada-2020-10.csv"
)


sql = """
CREATE TEMP TABLE __tmp
(LIKE facility_scada INCLUDING DEFAULTS)
ON COMMIT DROP;

COPY __tmp FROM STDIN WITH (FORMAT CSV, HEADER FALSE, DELIMITER ',');

INSERT INTO facility_scada
    SELECT *
    FROM __tmp
ON CONFLICT (trading_interval, network_id, facility_code) DO UPDATE set
    generated = EXCLUDED.generated,
    eoi_quantity = EXCLUDED.eoi_quantity
;
"""


def get_file_content():
    with open(scada_test_file) as fh:
        data = fh.read()

    return data


def test_insert():
    data = get_file_content()

    csv_reader = csv.DictReader(data.split("\n"))
    csv_buffer = StringIO()
    fieldnames = [
        "created_by",
        "created_at",
        "updated_at",
        "network_id",
        "trading_interval",
        "facility_code",
        "generated",
        "eoi_quantity",
    ]

    csvwriter = csv.DictWriter(csv_buffer, fieldnames=fieldnames,)

    for record in facility_scada_generate_records(csv_reader):
        csvwriter.writerow(record)

    conn = get_database_engine().raw_connection()

    cursor = conn.cursor()
    csv_buffer.seek(0)

    # cursor.copy_expert(sql, csv_buffer)

    # conn.commit()


if __name__ == "__main__":
    test_insert()
