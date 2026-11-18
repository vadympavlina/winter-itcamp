#!/usr/bin/env python3
"""Сканує lessons/, materials/ і перезаписує lessons.js та materials.js (лише стандартна бібліотека).

lessons/6-8, lessons/9-14   «День N — Назва.html» -> день N, назва «Назва» (інакше <title>)
                            presentation-<вік>-day-<N>.html -> презентація до дня N
lessons/extras.json         додаткові посилання до уроків: [{age, day, label, url}]
materials/programs          PDF програм (у назві файлу має бути 6-8 або 9-14)
materials/scripts           scripts.json — текст скриптів продажу (потім python3 scripts/build-docx.py збирає з нього docx)
materials/photo             фото табору (jpg/png/webp)
"""
import json, re, html
from pathlib import Path

root = Path(__file__).resolve().parent.parent
AGES = ("6-8", "9-14")

def num_key(p):
    m = re.match(r"\D*(\d+)", p.stem)
    return (int(m.group(1)) if m else 10**6, p.name.lower())

def age_of(name):
    # шукаємо 9-14 першим, щоб не сплутати з "12" в іншій групі
    for a in ("9-14", "6-8"):
        if a in name:
            return a
    return None

def rel(f):
    return f.relative_to(root).as_posix()

# ---------- уроки ----------
lessons = []
for age in AGES:
    pres = {}
    for f in (root / "lessons" / age).glob("presentation-*.html"):
        m = re.search(r"day-(\d+)", f.stem, re.I)
        if m: pres[int(m.group(1))] = rel(f)
    for f in sorted((root / "lessons" / age).glob("*.html"), key=num_key):
        if f.name.lower().startswith("presentation-"):
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")[:20000]
        t = re.search(r"<title[^>]*>(.*?)</title>", text, re.S | re.I)
        d = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']', text, re.S | re.I)
        m = re.match(r"^\s*День\s+(\d+)\s*[—–:.-]*\s*(.*)$", f.stem, re.I)
        title = m.group(2).strip() if m and m.group(2).strip() else (
            html.unescape(t.group(1)).strip() if t and t.group(1).strip() else f.stem)
        lessons.append({"age": age, "day": int(m.group(1)) if m else None, "title": title,
                        "desc": html.unescape(d.group(1)).strip() if d else "", "file": rel(f),
                        "presentation": pres.get(int(m.group(1)), "") if m else "", "links": []})
extras = root / "lessons" / "extras.json"
if extras.exists():
    for e in json.loads(extras.read_text(encoding="utf-8")):
        for l in lessons:
            if l["age"] == e["age"] and l["day"] == e["day"]:
                l["links"].append({"label": e["label"], "url": e["url"]})
(root / "lessons.js").write_text(
    "// Згенеровано: python3 scripts/update-lessons.py\nwindow.LESSONS = "
    + json.dumps(lessons, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")

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
sj = root / "materials" / "scripts" / "scripts.json"
if sj.exists():
    for x in json.loads(sj.read_text(encoding="utf-8")):
        f = root / "materials" / "scripts" / f"Скрипт {x['age']} років.docx"
        x["file"] = rel(f) if f.exists() else ""
        scripts.append(x)

photos = [{"title": f.stem, "file": rel(f)} for f in listdir("photo", {".jpg", ".jpeg", ".png", ".webp"})]

(root / "materials.js").write_text(
    "// Згенеровано: python3 scripts/update-lessons.py\nwindow.MATERIALS = "
    + json.dumps({"programs": programs, "scripts": scripts, "photos": photos}, ensure_ascii=False, indent=1) + ";\n",
    encoding="utf-8")
print(f"Готово: уроків {len(lessons)}, програм {len(programs)}, скриптів {len(scripts)}, фото {len(photos)}")
