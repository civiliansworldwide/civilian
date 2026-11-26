#!/usr/bin/env python3
"""Gleicht die Civilian-Route mit den Reise- und Sicherheitshinweisen des
Auswärtigen Amts ab (OpenData) und schreibt lage-aa.adoc.

Aufruf: python3 -I tools/reisewarnungen.py [Ausgabedatei]
"""
import json, sys, datetime, urllib.request, pathlib

URL = "https://www.auswaertiges-amt.de/opendata/travelwarning"
OUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else
                   pathlib.Path(__file__).resolve().parent.parent / "lage-aa.adoc")

# Etappen -> ISO-Ländercodes
ROUTE = [
    ("1–2 Berlin → Görlitz/Zgorzelec", ["DE", "PL"]),
    ("3–4 Kraków → Medyka", ["PL"]),
    ("4a Innere Staffel Ukraine", ["UA"]),
    ("5 → Sarajevo → Mostar", ["HU", "HR", "BA"]),
    ("6 → Mitrovica", ["ME", "XK"]),
    ("7 → Thessaloniki → Istanbul", ["MK", "GR", "TR"]),
    ("8 Nikosia", ["CY"]),
    ("9–10 Haifa → Jaffa → Jerusalem", ["IL"]),
    ("Westjordanland / Gaza", ["PS"]),
    ("Sternweg Kaukasus", ["GE", "AM", "TR"]),
    ("Sternweg Korea", ["KR"]),
    ("Sternweg Indien – Pakistan", ["IN", "PK"]),
    ("Sternweg Goma ↔ Gisenyi", ["CD", "RW"]),
    ("Sternweg Sudan – Tschad", ["SD", "TD"]),
    ("Sternweg Myanmar – Thailand", ["MM", "TH"]),
    ("Sternweg Tijuana ↔ San Diego", ["MX", "US"]),
    ("Mekka (nur Muslime)", ["SA"]),
]

def stufe(c):
    if c.get("warning"): return 3, "Reisewarnung"
    if c.get("partialWarning"): return 2, "Teilreisewarnung"
    if c.get("situationWarning") or c.get("situationPartWarning"): return 1, "Sicherheitshinweis"
    return 0, "–"

req = urllib.request.Request(URL, headers={"User-Agent": "civilian-route-check"})
data = json.load(urllib.request.urlopen(req, timeout=30))["response"]
laender = {v["countryCode"]: v for v in data.values()
           if isinstance(v, dict) and "countryCode" in v}

heute = datetime.date.today().strftime("%d.%m.%Y")
o = [f"// automatisch erzeugt von tools/reisewarnungen.py am {heute}",
     f"Abgerufen am {heute} von {URL}[Auswärtiges Amt OpenData].", "",
     "=== Die Karte der verbrannten Erde", "",
     "Wo das Auswärtige Amt warnt, leben Menschen, die nicht weg können. "
     "Für sie geht Civilian.", ""]
for lvl, name in ((3, "Reisewarnung"), (2, "Teilreisewarnung")):
    ls = sorted(c["countryName"] for c in laender.values() if stufe(c)[0] == lvl)
    o += [f"*{name}* ({len(ls)}): " + ", ".join(ls), ""]

o += ["=== Abgleich mit der Route", "",
      '[cols="3,2,4",options="header"]', "|===", "| Etappe | Stufe | Länder"]
for etappe, codes in ROUTE:
    worst, teile = 0, []
    for cc in codes:
        c = laender.get(cc)
        if cc == "DE":
            teile.append("Deutschland: Inland"); continue
        if not c:
            teile.append(f"{cc}: keine Daten"); continue
        lvl, txt = stufe(c); worst = max(worst, lvl)
        teile.append(f"{c['countryName']}: {txt}")
    ampel = ["🟢 offen", "🟡 Hinweis", "🟠 nur lokal", "🔴 von innen tragen"][worst]
    o.append(f"| {etappe} | {ampel} | " + "; ".join(teile))
o += ["|===", "",
      "Legende: 🟢 Etappe möglich · 🟡 mit Vorsicht · 🟠 nur mit lokalen Gastgebern, "
      "Gefahrengebiete meiden · 🔴 kein Gang von außen; Stimmen werden von innen "
      "gesammelt und an der Grenze übergeben.", ""]
OUT.write_text("\n".join(o), encoding="utf-8")
print(f"{OUT} geschrieben ({len(laender)} Länder)")
