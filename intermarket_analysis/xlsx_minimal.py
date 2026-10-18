"""Minimal XLSX reader (stdlib only) for single-sheet exports."""

from __future__ import annotations

import re
import zipfile
from datetime import datetime, timedelta
from io import BytesIO
from xml.etree import ElementTree as ET


_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def _col_row(cell_ref: str) -> tuple[int, int]:
    match = re.match(r"^([A-Z]+)(\d+)$", cell_ref)
    if not match:
        return 0, 0
    letters, row = match.groups()
    col = 0
    for ch in letters:
        col = col * 26 + (ord(ch) - ord("A") + 1)
    return col - 1, int(row) - 1


def _excel_serial_to_date(value: float) -> str:
    base = datetime(1899, 12, 30)
    return (base + timedelta(days=float(value))).date().isoformat()


def read_first_sheet_rows(content: bytes) -> list[list[str]]:
    with zipfile.ZipFile(BytesIO(content)) as zf:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in zf.namelist():
            root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for si in root.findall("m:si", _NS):
                texts = [t.text or "" for t in si.findall(".//m:t", _NS)]
                shared.append("".join(texts))

        sheet_name = next(n for n in zf.namelist() if n.startswith("xl/worksheets/sheet"))
        sheet = ET.fromstring(zf.read(sheet_name))
        rows_map: dict[int, dict[int, str]] = {}
        max_col = 0
        for row_el in sheet.findall("m:sheetData/m:row", _NS):
            for cell in row_el.findall("m:c", _NS):
                ref = cell.attrib.get("r", "")
                col, row = _col_row(ref)
                cell_type = cell.attrib.get("t")
                value_el = cell.find("m:v", _NS)
                if value_el is None or value_el.text is None:
                    continue
                raw = value_el.text
                if cell_type == "s":
                    text = shared[int(raw)]
                else:
                    text = raw
                    try:
                        num = float(raw)
                        if 30000 < num < 60000:
                            text = _excel_serial_to_date(num)
                    except ValueError:
                        pass
                rows_map.setdefault(row, {})[col] = text
                max_col = max(max_col, col)

        if not rows_map:
            return []
        max_row = max(rows_map)
        table: list[list[str]] = []
        for r in range(max_row + 1):
            line = [rows_map.get(r, {}).get(c, "") for c in range(max_col + 1)]
            table.append(line)
        return table
