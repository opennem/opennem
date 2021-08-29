"""Excel parser for OpenNEM"""
from typing import BinaryIO, Dict, List, Optional, Tuple

from openpyxl import load_workbook
from openpyxl.workbook.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet
from pydantic import BaseConfig

from opennem.utils.mime import mime_from_content
from opennem.utils.xls import convert_to_xlxs


def detect_sheat_data_dimensions(sheet: Worksheet) -> Tuple[int, int]:
    """Calculates how many rows and columns to skip on a sheet"""
    min_col = 0
    min_row = 0

    for col in sheet.columns:
        _col_values = [i.value for i in col if i.value]

        if len(_col_values) == 0:
            min_col += 1
        else:
            break

    for row in sheet.rows:
        _row_values = [i.value for i in row if i.value]

        if len(_row_values) < sheet.max_column:
            min_row += 1
        else:
            break

    return min_col, min_row


def parse_workbook_sheet(sheet: Worksheet) -> List[Dict]:
    min_col, min_row = detect_sheat_data_dimensions(sheet)

    print("{} has min_col {} and min_row {}".format(sheet.title, min_col, min_row))

    return []


def parse_workbook(
    fh: BinaryIO, model: Optional[BaseConfig] = None, convert_xls: bool = True
) -> Workbook:
    """Parse an excel file (with conversion) into a dict of lists for each sheet"""

    fh.seek(0)
    fh_mime = mime_from_content(fh)
    wb: Optional[Workbook] = None

    if fh_mime in ["application/CDFV2"]:
        if convert_to_xlxs:
            wb = convert_to_xlxs(fh)
    else:
        wb = load_workbook(fh)

    if not wb:
        raise Exception("Could not parse workbook")

    # workbook_parsed = {}

    # for _sheet in wb.sheetnames:
    #     _parsed_sheet = parse_workbook_sheet(wb[_sheet])

    #     workbook_parsed[_sheet] = _parsed_sheet

    return wb
