#!/usr/bin/env python3
"""Erzeugt die mehrsprachige Webseite aus i18n/*.json.

Aufruf (im Repo-Verzeichnis):  python3 -I tools/build_site.py

Ergebnis:
  index.html          Sprachauswahl (Satz 1 in allen Sprachen)
  <lang>/index.html   eine Seite pro Sprache
  assets/site.css     gemeinsames Stylesheet

Texte nie in den erzeugten HTML-Dateien ändern, sondern in i18n/<lang>.json.
"""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE_URL = "https://civiliansworldwide.github.io/civilian/"
PAD_URL = "https://cryptpad.fr/doc/#/2/doc/edit/30r0iYtAhwu1goUApkqiWXdv/"
CONTACT = "civilian6 [at] proton.me"
GITHUB = "https://github.com/civiliansworldwide/civilian"

# Reihenfolge auf der Startseite und in der Sprachleiste
ORDER = ["de", "en", "es", "fr", "pt", "it", "ru", "uk", "pl", "el", "tr", "ar",
         "he", "fa", "ur", "hi", "bn", "zh", "ja", "ko", "id", "vi", "sw", "am"]

# Nur für diese Sprachen gibt es schon Druckvorlagen
PRINT = {
    "de": {"h": "Zum Drucken",
           "items": [("../druck/zivilistenpass.html", "Zivilistenpass (A4, zum Falten)"),
                     ("../druck/pamphlet-a4.html", "Flugblatt (A4 = 2× A5)")],
           "note": "Im Browser drucken: A4 quer, Ränder „Keine“, Skalierung 100 %. "
                   "Der Pass ist kein amtliches Dokument. Behalte deinen echten Pass."},
}
MORE = {
    "de": [(f"{GITHUB}/blob/main/konzept.adoc", "Konzept"),
           (f"{GITHUB}/blob/main/route.adoc", "Pilgerroute Berlin → Jerusalem")],
}

e = html.escape


def load():
    langs = {}
    for code in ORDER:
        d = json.loads((ROOT / "i18n" / f"{code}.json").read_text(encoding="utf-8"))
        assert d["lang"] == code, code
        langs[code] = d
    return langs


def head(lang, dir_, title, desc, css, alternates, canonical):
    alt = "\n".join(
        f'<link rel="alternate" hreflang="{c}" href="{BASE_URL}{c}/">' for c in alternates)
    return f"""<!doctype html>
<html lang="{lang}" dir="{dir_}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canonical}">
{alt}
<link rel="alternate" hreflang="x-default" href="{BASE_URL}">
<link rel="stylesheet" href="{css}">
<!-- Erzeugt von tools/build_site.py aus i18n/*.json. Keine Cookies, kein Tracking. -->
</head>
"""


def langbar(langs, current, prefix):
    out = []
    for c in ORDER:
        n = e(langs[c]["name"])
        if c == current:
            out.append(f'<span aria-current="page" lang="{c}">{n}</span>')
        else:
            out.append(f'<a href="{prefix}{c}/" lang="{c}" hreflang="{c}">{n}</a>')
    return '<nav class="langs" aria-label="Languages">' + " ".join(out) + "</nav>"


def page(langs, code):
    d = langs[code]
    fill = lambda s: s.replace("{word}", e(d["word"])).replace(
        "{tag}", f'<span class="tag">{e(d["tag"])}</span>')
    charter = "\n".join(f"    <li>{e(s)}</li>" for s in d["charter"])
    steps = "\n".join(f"    <li>{fill(s)}</li>" for s in d["steps"])
    intro = "\n".join(f"  <p>{s}</p>" for s in d["intro"])  # enthält bewusst <strong>
    draft = (f'<p class="draft">{e(d["draft"])} '
             f'<a href="{GITHUB}/blob/main/i18n/{code}.json">i18n/{code}.json</a></p>'
             if d["draft"] else "")
    pr = ""
    if code in PRINT:
        p = PRINT[code]
        btns = "".join(f'<a class="btn" href="{h}">{e(t)}</a>' for h, t in p["items"])
        pr = f"""
  <h2>{e(p['h'])}</h2>
  <div class="btns">{btns}</div>
  <p class="note">{e(p['note'])}</p>
"""
    more = "".join(f'<a class="btn" href="{h}">{e(t)}</a>' for h, t in MORE.get(code, []))
    return head(code, d["dir"], f'{d["title"]} – Civilian', d["claim"], "../assets/site.css",
                ORDER, f"{BASE_URL}{code}/") + f"""<body>
<main>
  {langbar(langs, code, "../")}
  {draft}
  <div class="mark" aria-hidden="true">{e(d['word'])}</div>
  <h1>{e(d['title'])}</h1>
  <p class="sub">{e(d['sub'])}</p>

{intro}

  <p class="claim">{e(d['claim'])}</p>

  <h2>{e(d['h_believe'])}</h2>
  <ol class="charter">
{charter}
  </ol>

  <h2>{e(d['h_do'])}</h2>
  <ol class="steps">
{steps}
  </ol>
  <p class="safety" role="note">{e(d['note'])}</p>
{pr}
  <h2>{e(d['h_write'])}</h2>
  <p>{e(d['write'])}</p>
  <div class="btns"><a class="btn" href="{PAD_URL}">{e(d['btn_pad'])}</a>{more}</div>

  <h2>{e(d['h_not'])}</h2>
  <p>{e(d['not'])}</p>

  <footer>
    <p dir="ltr">{CONTACT} · <a href="{GITHUB}">GitHub</a></p>
    <p>{e(d['privacy'])}</p>
  </footer>
</main>
</body>
</html>
"""


def start(langs):
    items = "\n".join(
        f'  <li lang="{c}" dir="{langs[c]["dir"]}"><a href="{c}/">'
        f'<span class="w">{e(langs[c]["word"])}</span>'
        f'<span class="s">{e(langs[c]["charter"][0])}</span>'
        f'<span class="n">{e(langs[c]["name"])}</span></a></li>'
        for c in ORDER)
    codes = json.dumps(ORDER)
    return head("en", "ltr", "Civilian – We are just civilians",
                "I don't want war. And I believe the people on the other side don't want it either.",
                "assets/site.css", ORDER, BASE_URL) + f"""<body class="start">
<main>
  <div class="mark" aria-hidden="true">CIVILIAN</div>
  <p class="pick" id="pick" hidden></p>
  <ol class="choose">
{items}
  </ol>
  <footer>
    <p>{CONTACT} · <a href="{GITHUB}">GitHub</a></p>
  </footer>
</main>
<script>
  // Nur ein Hinweis auf die Browsersprache, keine automatische Weiterleitung, nichts wird gespeichert.
  const codes = {codes};
  const want = (navigator.languages || [navigator.language || ""]).map(l => l.slice(0, 2).toLowerCase());
  const hit = want.find(l => codes.includes(l));
  if (hit) {{
    const li = document.querySelector('.choose li[lang="' + hit + '"]');
    const p = document.getElementById("pick");
    p.appendChild(li.querySelector("a").cloneNode(true));
    p.hidden = false;
  }}
</script>
</body>
</html>
"""


CSS = """:root { --ink: #161616; --soft: #555; --line: #d8d4cc; --paper: #fbfaf7; --accent: #8a3b12; }
@media (prefers-color-scheme: dark) {
  :root { --ink: #ecebe8; --soft: #a9a7a2; --line: #3a3936; --paper: #161615; --accent: #e0a37c; }
}
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body { margin: 0; background: var(--paper); color: var(--ink);
  font: 18px/1.65 Georgia, "DejaVu Serif", "Noto Serif", "Noto Naskh Arabic", "Noto Serif Hebrew",
        "Noto Serif Devanagari", "Noto Serif Bengali", "Noto Serif CJK SC", "Noto Serif Ethiopic", serif; }
html:is([lang=zh], [lang=ja], [lang=ko]) body { line-height: 1.8; }
html:is([lang=ar], [lang=fa], [lang=ur]) body { font-size: 19.5px; line-height: 1.9; }
/* Arabische Schrift braucht eine Schrift mit Verbindungsformen, auch in den serifenlosen Elementen */
:is([lang=ar], [lang=fa], [lang=ur]) :is(h2, .mark, .draft, .btn, footer, .langs a, .langs span, .w, .n),
.langs :is([lang=ar], [lang=fa], [lang=ur]), .choose :is([lang=ar], [lang=fa], [lang=ur]) :is(.w, .n) {
  font-family: "Noto Sans Arabic", "Noto Naskh Arabic", "Segoe UI", Tahoma, sans-serif; letter-spacing: 0; }
main { max-width: 40rem; margin: 0 auto; padding: 2rem 1.25rem 4rem; }
nav, h2, footer, .btn, .draft, .langs, .steps li::before { font-family: system-ui, "DejaVu Sans", "Noto Sans", sans-serif; }
.langs { font-size: .8rem; line-height: 1.9; color: var(--soft); }
.langs a, .langs span { margin-inline-end: .55rem; white-space: nowrap; }
.langs a { color: var(--soft); }
.langs [aria-current] { color: var(--ink); font-weight: 700; }
.draft { font-size: .8rem; color: var(--soft); border: 1px dashed var(--line); padding: .4rem .7rem; margin: 1rem 0 0; }
.mark { display: inline-block; margin-top: 2.2rem; padding: .1rem .6rem; border: 2px solid var(--ink);
  font: 700 1rem/1.4 system-ui, sans-serif; letter-spacing: .2em; transform: rotate(-2deg); }
:lang(ar) .mark, :lang(fa) .mark, :lang(ur) .mark, :lang(he) .mark, :lang(hi) .mark, :lang(bn) .mark { letter-spacing: 0; }
h1 { font-size: clamp(2.1rem, 7vw, 3.1rem); line-height: 1.1; margin: 1.2rem 0 .3rem; }
.sub { font-style: italic; font-size: 1.3rem; margin: 0 0 2rem; color: var(--soft); }
.claim { font-size: 1.35rem; line-height: 1.45; font-weight: 700; margin: 2.2rem 0;
  padding-inline-start: 1rem; border-inline-start: 4px solid var(--accent); }
h2 { font-size: .8rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase;
  margin: 3rem 0 1rem; padding-bottom: .35rem; border-bottom: 2px solid var(--ink); }
:lang(ar) h2, :lang(fa) h2, :lang(ur) h2, :lang(he) h2 { letter-spacing: 0; font-size: .95rem; }
ol, ul { padding-inline-start: 1.4rem; padding-inline-end: 0; }
li { margin-bottom: .55rem; }
ol.charter li::marker { font-weight: 700; }
ol.charter li:first-child { font-weight: 700; }
.steps { list-style: none; padding: 0; counter-reset: s; }
.steps li { counter-increment: s; padding-inline-start: 2.4rem; position: relative; margin-bottom: 1rem; }
.steps li::before { content: counter(s); position: absolute; inset-inline-start: 0; top: .15rem;
  width: 1.7rem; height: 1.7rem; border: 1.5px solid var(--ink); border-radius: 50%;
  text-align: center; font-weight: 700; font-size: .85rem; line-height: 1.6rem; }
.note { border-inline-start: 3px solid var(--line); padding-block: .2rem; padding-inline-start: 1rem;
  color: var(--soft); font-size: .95rem; }
.safety { border: 2px solid var(--accent); border-radius: 4px; padding: .8rem 1rem; font-size: .97rem;
  background: color-mix(in srgb, var(--accent) 6%, transparent); }
a { color: var(--accent); }
.btns { display: flex; flex-wrap: wrap; gap: .6rem; }
.btn { display: inline-block; padding: .55rem .9rem; border: 1.5px solid var(--ink); color: var(--ink);
  text-decoration: none; font-size: .9rem; }
.btn:hover { background: var(--ink); color: var(--paper); }
.tag { font-family: system-ui, sans-serif; font-weight: 700; unicode-bidi: isolate; direction: ltr; }
footer { margin-top: 4rem; padding-top: 1rem; border-top: 1px solid var(--line); font-size: .8rem; color: var(--soft); }
/* Startseite */
.start main { max-width: 46rem; }
.choose { list-style: none; padding: 0; margin: 2rem 0 0; }
.choose li { margin: 0; border-bottom: 1px solid var(--line); }
.choose a { display: grid; grid-template-columns: 9rem 1fr; gap: .2rem 1rem; padding: .9rem .2rem;
  color: var(--ink); text-decoration: none; }
.choose a:hover { background: color-mix(in srgb, var(--accent) 8%, transparent); }
.choose .w { font: 700 .85rem/1.6 system-ui, sans-serif; letter-spacing: .08em; grid-row: span 2; padding-top: .15rem; }
.choose .s { font-size: 1.05rem; line-height: 1.45; }
.choose .n { font: .75rem system-ui, sans-serif; color: var(--soft); }
.pick { margin: 1.5rem 0 0; }
.pick a { display: grid; grid-template-columns: 9rem 1fr; gap: .2rem 1rem; padding: 1rem;
  border: 2px solid var(--ink); color: var(--ink); text-decoration: none; }
.pick .w { font: 700 .85rem/1.6 system-ui, sans-serif; grid-row: span 2; }
.pick .s { font-size: 1.2rem; font-weight: 700; line-height: 1.4; }
.pick .n { font: .75rem system-ui, sans-serif; color: var(--soft); }
@media (max-width: 34rem) {
  .choose a, .pick a { grid-template-columns: 1fr; }
  .choose .w, .pick .w { grid-row: auto; }
}
[hidden] { display: none !important; }
"""


def main():
    langs = load()
    (ROOT / "assets").mkdir(exist_ok=True)
    (ROOT / "assets" / "site.css").write_text(CSS, encoding="utf-8")
    for c in ORDER:
        (ROOT / c).mkdir(exist_ok=True)
        (ROOT / c / "index.html").write_text(page(langs, c), encoding="utf-8")
    (ROOT / "index.html").write_text(start(langs), encoding="utf-8")
    print(f"{len(ORDER)} Sprachseiten + Startseite erzeugt")


if __name__ == "__main__":
    main()
