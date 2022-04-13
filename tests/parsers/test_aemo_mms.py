from opennem.core.parsers.aemo.mms import parse_aemo_mms_csv


def test_parse_aemo_mms_dispatch_scada(aemo_nemweb_dispatch_scada: str) -> None:
    content = aemo_nemweb_dispatch_scada
    r = parse_aemo_mms_csv(content)

    assert r.get_table("unit_scada"), "Has table"

    table = r.get_table("unit_scada")

    if not table:
        raise Exception("No table error")

    assert table.records, "Table has records"

    print(table.records)

    assert len(table.records) == 390, "Table has correct number of records"

    record = table.records[0]

    if not record:
        raise Exception("Invalid record")

    # assert record.settlementdate, "Record has settlement date"  # type: ignore
