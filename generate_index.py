#!/usr/bin/env python3
"""Vygeneruje index.html so zoznamom animácií zoskupených podľa predmetu.

Spúšťa sa automaticky pri každom push (GitHub Actions), lokálne: python generate_index.py
Pravidlá:
- zahrnie len priečinky, v ktorých existuje index.html
- ignoruje priečinky začínajúce na "." alebo "_"
- priečinok má tvar <predmet>-<nazov>; skupina = text pred prvou pomlčkou
- názov odkazu = <title> z index.html animácie, inak názov priečinka
- priečinok bez pomlčky patrí do skupiny "Ostatné"
"""
import html
import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
PAGE_TITLE = "Moje animácie"
OTHER_LABEL = "Ostatné"

# Voliteľné: pekné zobrazované názvy predmetov (kľúč = prefix priečinka, malými písmenami).
# Čo tu nie je, zobrazí sa ako prefix s veľkým prvým písmenom.
SUBJECT_LABELS = {
    "biologia": "Biológia",
    "matematika": "Matematika",
    "fyzika": "Fyzika",
    "chemia": "Chémia",
    "geografia": "Geografia",
    "informatika": "Informatika",
    "vlastiveda": "Vlastiveda",
    "prirodoveda": "Prírodoveda",
    "dejepis": "Dejepis",
}


def subject_of(dirname: str):
    """Vráti (kľúč skupiny, zobrazovaný názov)."""
    if "-" not in dirname:
        return "", OTHER_LABEL
    key = dirname.split("-", 1)[0].strip().lower()
    if not key:
        return "", OTHER_LABEL
    return key, SUBJECT_LABELS.get(key, key[:1].upper() + key[1:])


groups = defaultdict(list)  # kľúč -> [(dirname, title)]
labels = {}

for d in sorted(ROOT.iterdir(), key=lambda p: p.name.lower()):
    if not d.is_dir() or d.name.startswith((".", "_")):
        continue
    page = d / "index.html"
    if not page.is_file():
        continue
    text = page.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"<title>(.*?)</title>", text, re.I | re.S)
    title = " ".join(m.group(1).split()) if m else ""
    key, label = subject_of(d.name)
    labels[key] = label
    groups[key].append((d.name, title or d.name))

total = sum(len(v) for v in groups.values())

# Skupiny abecedne podľa zobrazovaného názvu, "Ostatné" vždy na konci.
ordered_keys = sorted(groups, key=lambda k: (k == "", labels[k].lower()))

sections = []
for key in ordered_keys:
    cards = "\n".join(
        f'        <li><a href="{quote(name)}/">{html.escape(title)}'
        f'<span>{html.escape(name)}/</span></a></li>'
        for name, title in groups[key]
    )
    sections.append(
        f'    <section>\n'
        f'      <h2>{html.escape(labels[key])} <small>({len(groups[key])})</small></h2>\n'
        f'      <ul>\n{cards}\n      </ul>\n'
        f'    </section>'
    )

body = "\n".join(sections) if sections else '    <p class="empty">Zatiaľ tu nie sú žiadne animácie.</p>'

doc = f"""<!DOCTYPE html>
<html lang="sk">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(PAGE_TITLE)}</title>
  <style>
    :root {{ color-scheme: light dark; }}
    body {{ font-family: system-ui, sans-serif; max-width: 720px; margin: 0 auto; padding: 2rem 1rem; line-height: 1.5; }}
    h1 {{ margin-bottom: .25rem; }}
    h2 {{ margin: 2rem 0 .75rem; padding-bottom: .25rem; border-bottom: 2px solid #8884; font-size: 1.25rem; }}
    h2 small {{ font-weight: 400; opacity: .6; }}
    p.sub {{ margin-top: 0; opacity: .7; }}
    ul {{ list-style: none; padding: 0; margin: 0; display: grid; gap: .75rem; }}
    li a {{ display: block; padding: 1rem 1.25rem; border: 1px solid #8884; border-radius: 10px;
            text-decoration: none; color: inherit; font-weight: 600; }}
    li a:hover {{ border-color: #4a90d9; background: #4a90d91a; }}
    li a span {{ display: block; font-weight: 400; font-size: .85rem; opacity: .6; }}
    .empty {{ opacity: .6; }}
  </style>
</head>
<body>
  <h1>{html.escape(PAGE_TITLE)}</h1>
  <p class="sub">Počet animácií: {total}</p>
{body}
</body>
</html>
"""

(ROOT / "index.html").write_text(doc, encoding="utf-8")
print(f"index.html vygenerovaný, animácií: {total}, predmetov: {len(groups)}")
