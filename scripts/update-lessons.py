#!/usr/bin/env python3
"""Сканує lessons/6-8 та lessons/9-12 і перезаписує lessons.js.
Файл «День N — Назва.html» -> день N, назва «Назва». Інакше назва береться з <title>.
Опис — з <meta name="description"> (якщо є). Порядок — за номером дня."""
import json, re, html
from pathlib import Path

root = Path(__file__).resolve().parent.parent
out = []
for age in ("6-8", "9-12"):
    def key(p):
        m = re.match(r"\D*(\d+)", p.stem)
        return (int(m.group(1)) if m else 10**6, p.name.lower())
    for f in sorted((root / "lessons" / age).glob("*.html"), key=key):
        text = f.read_text(encoding="utf-8", errors="ignore")[:20000]
        t = re.search(r"<title[^>]*>(.*?)</title>", text, re.S | re.I)
        d = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']', text, re.S | re.I)
        m = re.match(r"^\s*День\s+(\d+)\s*[—–:.-]*\s*(.*)$", f.stem, re.I)
        title = m.group(2).strip() if m and m.group(2).strip() else (
            html.unescape(t.group(1)).strip() if t and t.group(1).strip() else f.stem)
        out.append({
            "age": age,
            "day": int(m.group(1)) if m else None,
            "title": title,
            "desc": html.unescape(d.group(1)).strip() if d else "",
            "file": f"lessons/{age}/{f.name}",
        })
(root / "lessons.js").write_text(
    "// Згенеровано: python3 scripts/update-lessons.py\nwindow.LESSONS = "
    + json.dumps(out, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")
print(f"Готово: {len(out)} уроків")
