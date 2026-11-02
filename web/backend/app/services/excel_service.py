"""
Excel export/import helpers built on openpyxl.

Exports produce binary .xlsx bytes (StreamingResponse-friendly) with RTL-safe
headers and styled cells; imports parse uploaded workbooks into row dicts keyed
by the column header.
"""

from io import BytesIO
from typing import Any, Iterable

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
HEADER_FONT = Font(color="FFFFFF", bold=True, size=11)
MAX_WIDTH = 50


def build_workbook(sheet_name: str, headers: list[str], rows: Iterable[Iterable[Any]]) -> bytes:
    """Serialize a simple table (header row + data rows) into .xlsx bytes."""
    wb = Workbook()
    ws = wb.active
    ws.title = (sheet_name or "Sheet1")[:31]

    ws.append(headers)
    for cell in ws[1]:
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = __cell_border()

    for row in rows:
        ws.append(list(row))

    # RTL sheet is friendlier for Arabic readers; freeze the header row.
    ws.sheet_view.rightToLeft = True
    ws.freeze_panes = "A2"
    for idx, header in enumerate(headers, start=1):
        letter = get_column_letter(idx)
        width = max(len(str(header or "")), 10)
        for cell in ws[letter]:
            if cell.value is not None:
                width = max(width, min(len(str(cell.value)) + 2, MAX_WIDTH))
        ws.column_dimensions[letter].width = width

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


def __cell_border():
    from openpyxl.styles import Border, Side

    side = Side(style="thin", color="D9D9D9")
    return Border(left=side, right=side, top=side, bottom=side)


def workbook_from_bytes(data: bytes) -> Workbook:
    """Load an uploaded workbook, returning formulas as cached values."""
    return load_workbook(BytesIO(data), data_only=True)


def parse_sheet(data: bytes) -> tuple[list[str], list[list[Any]]]:
    """Parse the first worksheet into (headers, data rows)."""
    ws = load_workbook(BytesIO(data), data_only=True).active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return [], []
    headers = [str(c).strip() if c is not None else "" for c in rows[0]]
    data = [list(r) for r in rows[1:]]
    return headers, data