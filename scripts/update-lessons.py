#!/usr/bin/env python3
"""Сканує lessons/, materials/ і перезаписує lessons.js та materials.js (лише стандартна бібліотека).

lessons/6-8, lessons/9-12   «День N — Назва.html» -> день N, назва «Назва» (інакше <title>)
materials/programs          PDF програм (у назві файлу має бути 6-8 або 9-12)
materials/scripts           DOCX скриптів продажу (6-8 / 9-12 у назві); текст читається зі самого файлу
materials/photo             фото табору (jpg/png/webp)
"""
import json, re, html, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

root = Path(__file__).resolve().parent.parent
AGES = ("6-8", "9-12")

def num_key(p):
    m = re.match(r"\D*(\d+)", p.stem)
    return (int(m.group(1)) if m else 10**6, p.name.lower())

def age_of(name):
    # шукаємо 9-12 першим, щоб не сплутати з "12" в іншій групі
    for a in ("9-12", "6-8"):
        if a in name:
            return a
    return None

def rel(f):
    return f.relative_to(root).as_posix()

# ---------- уроки ----------
lessons = []
for age in AGES:
    for f in sorted((root / "lessons" / age).glob("*.html"), key=num_key):
        text = f.read_text(encoding="utf-8", errors="ignore")[:20000]
        t = re.search(r"<title[^>]*>(.*?)</title>", text, re.S | re.I)
        d = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']', text, re.S | re.I)
        m = re.match(r"^\s*День\s+(\d+)\s*[—–:.-]*\s*(.*)$", f.stem, re.I)
        title = m.group(2).strip() if m and m.group(2).strip() else (
            html.unescape(t.group(1)).strip() if t and t.group(1).strip() else f.stem)
        lessons.append({"age": age, "day": int(m.group(1)) if m else None, "title": title,
                        "desc": html.unescape(d.group(1)).strip() if d else "", "file": rel(f)})
(root / "lessons.js").write_text(
    "// Згенеровано: python3 scripts/update-lessons.py\nwindow.LESSONS = "
    + json.dumps(lessons, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")

# ---------- docx -> абзаци ----------
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
def read_docx(path):
    with zipfile.ZipFile(path) as z:
        tree = ET.fromstring(z.read("word/document.xml"))
    paras = []
    for p in tree.iter(W + "p"):
        runs = []
        for r in p.iter(W + "r"):
            rpr = r.find(W + "rPr")
            bold = rpr is not None and rpr.find(W + "b") is not None and \
                rpr.find(W + "b").get(W + "val", "true") not in ("0", "false")
            s = ""
            for el in r:
                if el.tag == W + "t": s += el.text or ""
                elif el.tag in (W + "br", W + "cr"): s += "\n"
                elif el.tag == W + "tab": s += "\t"
            if s:
                if runs and runs[-1]["b"] == bold: runs[-1]["t"] += s
                else: runs.append({"t": s, "b": bold})
        if runs and "".join(x["t"] for x in runs).strip():
            # прибираємо кінцеві переноси
            runs[-1]["t"] = runs[-1]["t"].rstrip("\n")
            paras.append(runs)
    return paras

# ---------- матеріали ----------
def listdir(sub, exts):
    d = root / "materials" / sub
    return sorted((f for f in d.glob("*") if f.suffix.lower() in exts), key=num_key) if d.exists() else []

programs = []
for f in listdir("programs", {".pdf"}):
    a = age_of(f.name)
    prev = root / "assets" / "previews" / f"program-{a}.jpg"
    programs.append({"age": a, "title": f.stem, "file": rel(f), "preview": rel(prev) if prev.exists() else ""})

scripts = []
for f in listdir("scripts", {".docx"}):
    paras = read_docx(f)
    scripts.append({"age": age_of(f.name), "title": f.stem, "file": rel(f), "paras": paras})

photos = [{"title": f.stem, "file": rel(f)} for f in listdir("photo", {".jpg", ".jpeg", ".png", ".webp"})]

(root / "materials.js").write_text(
    "// Згенеровано: python3 scripts/update-lessons.py\nwindow.MATERIALS = "
    + json.dumps({"programs": programs, "scripts": scripts, "photos": photos}, ensure_ascii=False, indent=1) + ";\n",
    encoding="utf-8")
print(f"Готово: уроків {len(lessons)}, програм {len(programs)}, скриптів {len(scripts)}, фото {len(photos)}")
