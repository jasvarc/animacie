#!/usr/bin/env python3
"""Vygeneruje index.html so zoznamom animácií zoskupených podľa predmetu.

Spúšťa sa automaticky pri každom push (GitHub Actions), lokálne: python generate_index.py
Pravidlá:
- zahrnie len priečinky, v ktorých existuje index.html
- ignoruje priečinky začínajúce na "." alebo "_"
- priečinok má tvar <predmet>-<nazov>; skupina = text pred prvou pomlčkou
- názov odkazu = <title> z index.html animácie, inak názov priečinka
- priečinok bez pomlčky patrí do skupiny "Ostatné"
- vzhľad (farby, panely, typografia) zodpovedá samotným animáciám
"""
import html
import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
PAGE_TITLE = "Pachove animácie"
PAGE_SUB = "Interaktívne učebné animácie – vyber si predmet a téma sa otvorí na celú obrazovku."
OTHER_LABEL = "Ostatné"
DEFAULT_ACCENT = "#f3b453"
# Dobrovoľná podpora (Ko-fi) – box vpravo vedľa hlavičky
SUPPORT_TEXT = "Robím to hlavne pre deti, ale môžete ma podporiť dobrovoľnou „kávou“ ☕"
SUPPORT_BTN = "☕ Podporiť kávou"
# Okno s platobným formulárom (Ko-fi embed, rovnaká adresa ako používa ich vlastný widget).
# Ko-fi sa načíta až po kliknutí na tlačidlo.
KOFI_PAGE = "https://ko-fi.com/jasvarc"
KOFI_EMBED = "https://ko-fi.com/jasvarc/?hidefeed=true&widget=true&embed=true"
SUPPORT_JS = """  <script>
  (function () {
    var dlg = document.getElementById('kofi-dialog');
    var btn = document.getElementById('kofi-open');
    var frame = document.getElementById('kofi-frame');
    if (!dlg || !btn || !frame) return;
    if (typeof dlg.showModal !== 'function') {   // starý prehliadač: otvor Ko-fi v novej karte
      btn.addEventListener('click', function () {
        window.open(btn.getAttribute('data-page'), '_blank', 'noopener');
      });
      return;
    }
    btn.addEventListener('click', function () {
      if (!frame.getAttribute('src')) frame.setAttribute('src', frame.getAttribute('data-src'));
      dlg.showModal();
    });
    dlg.addEventListener('click', function (e) { if (e.target === dlg) dlg.close(); });
    dlg.querySelector('.kofi-close').addEventListener('click', function () { dlg.close(); });
  })();
  </script>"""

# Buy Me a Coffee – plávajúce tlačidlo vpravo dole (farba = zlatý akcent stránky)
BMC_WIDGET = """  <script data-name="BMC-Widget" data-cfasync="false" src="https://cdnjs.buymeacoffee.com/1.0.0/widget.prod.min.js" data-id="jasvarc" data-description="Podporte ma kávou!" data-message="" data-color="#f3b453" data-position="Right" data-x_margin="18" data-y_margin="18"></script>"""

# kľúč = prefix priečinka (malými písmenami) -> (zobrazovaný názov, akcentová farba)
# Farby sú z palety animácií. Čo tu nie je, dostane prefix s veľkým prvým písmenom a zlatý akcent.
SUBJECTS = {
    "biologia":    ("Biológia",    "#7fdc8f"),
    "geografia":   ("Geografia",   "#6fb4ff"),
    "matematika":  ("Matematika",  "#f3b453"),
    "informatika": ("Informatika", "#b9a3ff"),
    "fyzika":      ("Fyzika",      "#ff7a6b"),
    "chemia":      ("Chémia",      "#5fd6c8"),
    "dejepis":     ("Dejepis",     "#e0a36a"),
    "vlastiveda":  ("Vlastiveda",  "#9ad66a"),
    "prirodoveda": ("Prírodoveda", "#7fdc8f"),
}


def subject_of(dirname: str):
    """Vráti (kľúč skupiny, zobrazovaný názov, akcentová farba)."""
    if "-" not in dirname:
        return "", OTHER_LABEL, "#8d98b3"
    key = dirname.split("-", 1)[0].strip().lower()
    if not key:
        return "", OTHER_LABEL, "#8d98b3"
    if key in SUBJECTS:
        return (key, *SUBJECTS[key])
    return key, key[:1].upper() + key[1:], DEFAULT_ACCENT


def plural(n: int, one: str, few: str, many: str) -> str:
    if n == 1:
        return f"{n} {one}"
    if 2 <= n <= 4:
        return f"{n} {few}"
    return f"{n} {many}"


groups = defaultdict(list)  # kľúč -> [(dirname, title)]
meta = {}                   # kľúč -> (label, accent)

for d in sorted(ROOT.iterdir(), key=lambda p: p.name.lower()):
    if not d.is_dir() or d.name.startswith((".", "_")):
        continue
    page = d / "index.html"
    if not page.is_file():
        continue
    text = page.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"<title>(.*?)</title>", text, re.I | re.S)
    title = " ".join(m.group(1).split()) if m else ""
    key, label, accent = subject_of(d.name)
    meta[key] = (label, accent)
    groups[key].append((d.name, title or d.name))

total = sum(len(v) for v in groups.values())

# Skupiny abecedne podľa zobrazovaného názvu, "Ostatné" vždy na konci;
# animácie v skupine abecedne podľa zobrazeného názvu.
ordered_keys = sorted(groups, key=lambda k: (k == "", meta[k][0].lower()))

sections = []
for key in ordered_keys:
    label, accent = meta[key]
    items = sorted(groups[key], key=lambda it: it[1].lower())
    cards = "\n".join(
        f'        <li><a class="card" href="{quote(name)}/">'
        f'<span class="t">{html.escape(title)}</span><span class="go" aria-hidden="true">→</span></a></li>'
        for name, title in items
    )
    sections.append(
        f'    <section style="--acc:{accent}">\n'
        f'      <h2><i></i>{html.escape(label)}<small>{len(items)}</small></h2>\n'
        f'      <ul>\n{cards}\n      </ul>\n'
        f'    </section>'
    )

if sections:
    body = "\n".join(sections)
else:
    body = '    <p class="empty">Zatiaľ tu nie sú žiadne animácie.</p>'

summary = (
    f"{plural(total, 'animácia', 'animácie', 'animácií')} · "
    f"{plural(len(groups), 'predmet', 'predmety', 'predmetov')}"
)

CSS = """
:root{
  --bg:#04060c;--panel:rgba(12,16,28,.86);--line:rgba(140,160,215,.22);
  --text:#e2e8f5;--muted:#a3adc6;--gold:#f3b453;--gold2:#ffd88a;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;min-height:100vh;color:var(--text);background:var(--bg);
  background-image:radial-gradient(ellipse at 50% -10%,#14204a 0%,#070b18 50%,#04060c 100%);background-attachment:fixed;
  font:17px/1.5 system-ui,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:1100px;margin:0 auto;padding:16px 16px 40px}
.card{display:flex;align-items:center;justify-content:space-between;gap:12px;
  background:var(--panel);border:1px solid var(--line);border-radius:14px;
  box-shadow:0 12px 40px rgba(0,0,0,.45);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px)}
.hero{display:flex;gap:12px;align-items:stretch;margin:8px 0 28px}
header.top{padding:18px 20px;display:flex;align-items:center;gap:18px;flex:1 1 auto}
.logo{width:96px;height:96px;flex:0 0 auto;border-radius:50%;display:block;
  box-shadow:0 0 0 2px var(--line),0 6px 18px rgba(0,0,0,.45)}
.support{flex:0 0 270px;flex-direction:column;align-items:flex-start;justify-content:center;gap:10px;padding:16px 18px}
.support p{margin:0;color:var(--muted);font-size:14px;line-height:1.45}
.support-btn{font:inherit;font-size:14px;font-weight:650;cursor:pointer;padding:8px 14px;border-radius:999px;
  border:1px solid var(--gold);background:transparent;color:var(--gold2);transition:background .15s,color .15s}
.support-btn:hover,.support-btn:focus-visible{background:var(--gold);color:#04060c}
.support-btn:focus-visible{outline:3px solid var(--gold2);outline-offset:2px}
dialog.kofi{padding:0;border:1px solid var(--line);border-radius:14px;background:#0c101c;color:var(--text);
  width:min(360px,calc(100vw - 24px));max-height:calc(100vh - 24px);overflow:hidden;
  box-shadow:0 20px 60px rgba(0,0,0,.6)}
dialog.kofi::backdrop{background:rgba(4,6,12,.72)}
.kofi-box{padding:10px 12px 12px}
.kofi-bar{display:flex;justify-content:space-between;align-items:center;gap:10px;margin:0 0 8px}
.kofi-bar span{font-size:13px;color:var(--muted)}
.kofi-bar span a{color:var(--gold2)}
.kofi-close{font:inherit;font-size:20px;line-height:1;cursor:pointer;width:34px;height:34px;border-radius:50%;
  border:1px solid var(--line);background:transparent;color:var(--text)}
.kofi-close:hover,.kofi-close:focus-visible{border-color:var(--gold);color:var(--gold2)}
#kofi-frame{display:block;width:100%;height:min(690px,calc(100vh - 110px));border:0;border-radius:10px;background:#fff}
h1{margin:0;font-size:16px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--gold)}
.sub{color:var(--muted);margin:6px 0 0}
.sum{color:var(--muted);font-size:14px;margin:10px 0 0;font-variant-numeric:tabular-nums}
section{margin-bottom:30px}
h2{display:flex;align-items:center;gap:10px;margin:0 0 12px;font-size:16px;font-weight:650;
  letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
h2 i{width:10px;height:10px;border-radius:50%;background:var(--acc);box-shadow:0 0 12px var(--acc)}
h2 small{font-size:13px;letter-spacing:0;color:var(--muted);border:1px solid var(--line);
  border-radius:999px;padding:0 9px;font-weight:500}
ul{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px}
li a{padding:16px 18px;min-height:64px;text-decoration:none;color:var(--text);font-weight:600;
  transition:background .15s,border-color .15s,transform .15s}
li a:hover,li a:focus-visible{background:rgba(255,255,255,.07);border-color:var(--acc);transform:translateY(-2px)}
li a:focus-visible{outline:3px solid var(--gold2);outline-offset:2px}
.go{color:var(--acc);font-size:20px;line-height:1;transition:transform .15s}
li a:hover .go{transform:translateX(4px)}
.empty{color:var(--muted)}
@media (max-width:760px){.hero{flex-direction:column}.support{flex-basis:auto}}
@media (max-width:420px){.logo{width:64px;height:64px}}
@media (max-width:520px){ul{grid-template-columns:1fr}}
@media (prefers-reduced-motion:reduce){li a,.go{transition:none}li a:hover{transform:none}}
"""

doc = f"""<!DOCTYPE html>
<html lang="sk">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#04060c">
  <title>{html.escape(PAGE_TITLE)}</title>
  <link rel="icon" href="data:,">
  <style>{CSS}</style>
</head>
<body>
  <div class="wrap">
    <div class="hero">
      <header class="top card">
        <img class="logo" src="logo.png" width="96" height="96" alt="Logo – chlapec a ceruzka, jasvarc.github.io/animacie">
        <div>
          <h1>{html.escape(PAGE_TITLE)}</h1>
          <p class="sub">{html.escape(PAGE_SUB)}</p>
          <p class="sum">{summary}</p>
        </div>
      </header>
      <aside class="support card">
        <p>{html.escape(SUPPORT_TEXT)}</p>
        <button type="button" class="support-btn" id="kofi-open" aria-haspopup="dialog" data-page="{html.escape(KOFI_PAGE)}">{html.escape(SUPPORT_BTN)}</button>
      </aside>
    </div>
{body}
  </div>
  <dialog class="kofi" id="kofi-dialog" aria-label="Podporiť kávou">
    <div class="kofi-box">
      <div class="kofi-bar">
        <span>Nezobrazuje sa formulár? <a href="{html.escape(KOFI_PAGE)}" target="_blank" rel="noopener">Otvoriť na Ko-fi</a></span>
        <button type="button" class="kofi-close" aria-label="Zavrieť">×</button>
      </div>
      <iframe id="kofi-frame" title="Podporiť kávou – Ko-fi" allow="payment" data-src="{html.escape(KOFI_EMBED)}" loading="lazy"></iframe>
    </div>
  </dialog>
{SUPPORT_JS}
{BMC_WIDGET}
</body>
</html>
"""

(ROOT / "index.html").write_text(doc, encoding="utf-8")
print(f"index.html vygenerovaný, animácií: {total}, predmetov: {len(groups)}")
