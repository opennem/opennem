"""
OpenNEM Excel File Utils


"""


from typing import Any

import xlrd
from openpyxl.workbook.workbook import Workbook


def convert_to_xlxs(content: Any) -> Workbook:
    """Convert old workbook formats xls into xlxs"""
    xlsBook = xlrd.open_workbook(file_contents=content)
    workbook = Workbook()

    for i in range(0, xlsBook.nsheets):
        xlsSheet = xlsBook.sheet_by_index(i)
        sheet = workbook.active if i == 0 else workbook.create_sheet()
        sheet.title = xlsSheet.name

        for row in range(0, xlsSheet.nrows):
            for col in range(0, xlsSheet.ncols):
                sheet.cell(
                    row=row + 1, column=col + 1
                ).value = xlsSheet.cell_value(row, col)

    return workbook
