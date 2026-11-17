#!/usr/bin/env python3
"""Збирає docx-скрипти з materials/scripts/scripts.json (потрібен python-docx: pip install python-docx)."""
import json
from pathlib import Path
from docx import Document
from docx.shared import Pt, RGBColor

root = Path(__file__).resolve().parent.parent
NAVY = RGBColor(0x03, 0x30, 0x6F)
for s in json.loads((root / "materials/scripts/scripts.json").read_text(encoding="utf-8")):
    d = Document()
    d.styles["Normal"].font.name = "Calibri"; d.styles["Normal"].font.size = Pt(11)
    h = d.add_heading(f"Скрипт · {s['age'].replace('-', '–')} років", level=0)
    d.add_paragraph(s["name"]).runs[0].bold = True
    t = d.add_table(rows=0, cols=2); t.style = "Light Grid Accent 1"
    for k, v in s["facts"]:
        c = t.add_row().cells; c[0].text = k; c[1].text = v
    for b in s["blocks"]:
        hh = d.add_heading(b["title"], level=2)
        for r in hh.runs: r.font.color.rgb = NAVY
        for ln in b["lines"]:
            p = d.add_paragraph()
            if ln.get("h"): p.add_run(ln["h"] + " ").bold = True
            p.add_run(ln["t"])
    hh = d.add_heading("Коротке повідомлення для месенджера", level=2)
    for r in hh.runs: r.font.color.rgb = NAVY
    for line in s["short"].split("\n"): d.add_paragraph(line)
    out = root / f"materials/scripts/Скрипт {s['age']} років.docx"
    d.save(out); print("OK", out.name)
