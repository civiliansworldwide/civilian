#!/usr/bin/env python3
"""Sucht in Wikidata nach bestehenden Friedens- und Gewaltfreiheits-Organisationen
und schreibt eine Rechercheliste (CSV) für persönliche, einzelne Anfragen.

Kein Massenversand: Die Liste ist nur ein Ausgangspunkt. Jede Organisation
wird einzeln geprüft und persönlich angeschrieben (siehe ansprache.adoc, Vorlage C).

Aufruf: python3 -I tools/wikidata_orgs.py [ausgabe.csv]
"""
import csv, sys, json, pathlib, urllib.parse, urllib.request

OUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else
                   pathlib.Path(__file__).resolve().parent.parent / "kontakte" / "organisationen.csv")

QUERY = """
SELECT ?org ?orgLabel ?landLabel ?web ?mail ?aufgeloest
       (GROUP_CONCAT(DISTINCT ?grundLabel; separator=", ") AS ?gruende) WHERE {
  {
    ?org wdt:P31/wdt:P279* wd:Q26928534 .            # Friedensorganisation
    BIND("Friedensorganisation" AS ?grundLabel)
  } UNION {
    VALUES ?feld { wd:Q454 wd:Q58848 wd:Q1194317 wd:Q76611 wd:Q2632158
                   wd:Q331662 wd:Q1200085 wd:Q708312 wd:Q794691 }
    ?org wdt:P101 ?feld .                              # Tätigkeitsfeld
    FILTER NOT EXISTS { ?org wdt:P31 wd:Q5 }           # keine Einzelpersonen
    ?feld rdfs:label ?grundLabel . FILTER(LANG(?grundLabel)="de")
  } UNION {
    ?org wdt:P166 wd:Q35637 .                          # Friedensnobelpreis
    FILTER NOT EXISTS { ?org wdt:P31 wd:Q5 }
    BIND("Friedensnobelpreis" AS ?grundLabel)
  }
  OPTIONAL { ?org wdt:P17 ?land . }
  OPTIONAL { ?org wdt:P856 ?web . }
  OPTIONAL { ?org wdt:P968 ?mail . }
  OPTIONAL { ?org wdt:P576 ?aufgeloest . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "de,en,fr,es". }
}
GROUP BY ?org ?orgLabel ?landLabel ?web ?mail ?aufgeloest
"""

url = "https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": QUERY, "format": "json"})
req = urllib.request.Request(url, headers={"User-Agent": "civilian-research/0.1",
                                           "Accept": "application/sparql-results+json"})
import time, urllib.error
for versuch in range(4):                               # Wikidata drosselt zeitweise (HTTP 429)
    try:
        rows = json.load(urllib.request.urlopen(req, timeout=120))["results"]["bindings"]
        break
    except urllib.error.HTTPError as e:
        if e.code != 429 or versuch == 3:
            raise
        print("Wikidata drosselt, warte 65 s …", file=sys.stderr)
        time.sleep(65)

orgs = {}
for r in rows:
    g = lambda k: r.get(k, {}).get("value", "")
    qid = g("org").rsplit("/", 1)[-1]
    if g("aufgeloest"):
        continue                                      # aufgelöste Organisationen überspringen
    o = orgs.setdefault(qid, {"qid": qid, "name": g("orgLabel"), "land": set(),
                              "web": set(), "mail": set(), "grund": set()})
    for k, v in (("land", g("landLabel")), ("web", g("web")),
                 ("mail", g("mail").removeprefix("mailto:")), ("grund", g("gruende"))):
        for x in v.split(", ") if k == "grund" else [v]:
            if x: o[k].add(x)

OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["qid", "name", "land", "website", "email_wikidata", "grund",
                "status", "angeschrieben_am", "antwort", "notiz"])
    for o in sorted(orgs.values(), key=lambda o: (not o["web"], sorted(o["land"]) or ["~"], o["name"])):
        if o["name"] == o["qid"]:
            continue                                  # ohne Beschriftung: unbrauchbar
        w.writerow([o["qid"], o["name"], "; ".join(sorted(o["land"])),
                    " ".join(sorted(o["web"])), " ".join(sorted(o["mail"])),
                    ", ".join(sorted(o["grund"])), "zu prüfen", "", "", ""])

n = len(orgs)
print(f"{OUT}: {n} Organisationen, "
      f"{sum(1 for o in orgs.values() if o['web'])} mit Website, "
      f"{sum(1 for o in orgs.values() if o['mail'])} mit E-Mail in Wikidata")
