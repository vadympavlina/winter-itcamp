#!/usr/bin/env python3
"""Сканує lessons/6-8 та lessons/9-12 і перезаписує lessons.js.
Назва береться з <title>, опис — з <meta name="description"> (якщо є).
Порядок — за назвою файлу (lesson-01.html, lesson-02.html ...)."""
import json, re, html
from pathlib import Path

root = Path(__file__).resolve().parent.parent
out = []
for age in ("6-8", "9-12"):
    for f in sorted((root / "lessons" / age).glob("*.html"), key=lambda p: p.name.lower()):
        text = f.read_text(encoding="utf-8", errors="ignore")[:20000]
        t = re.search(r"<title[^>]*>(.*?)</title>", text, re.S | re.I)
        d = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']', text, re.S | re.I)
        out.append({
            "age": age,
            "title": html.unescape(t.group(1)).strip() if t and t.group(1).strip() else f.stem,
            "desc": html.unescape(d.group(1)).strip() if d else "",
            "file": f"lessons/{age}/{f.name}",
        })
(root / "lessons.js").write_text(
    "// Згенеровано: python3 scripts/update-lessons.py\nwindow.LESSONS = "
    + json.dumps(out, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")
print(f"Готово: {len(out)} уроків")
