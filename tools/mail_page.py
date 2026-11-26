#!/usr/bin/env python3
"""Erzeugt die lokale Versandseite kontakte/versand.html aus kontakte/entwuerfe.adoc.

Aufruf (im Repo-Verzeichnis):  python3 -I tools/mail_page.py

Absenderdaten stehen in kontakte/absender.json (bleibt lokal, kontakte/ ist in .gitignore):
  {"vorname": "...", "nachname": "...", "stadt": "..."}

Jede Mail wird über einen Knopf in Proton Mail geöffnet (fertig ausgefüllt) und dort
von Hand gesendet. Nichts wird automatisch verschickt.
"""
import csv
import html
import json
import re
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
K = ROOT / "kontakte"
EMAIL = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")


def parse(adoc):
    parts = re.split(r"^== (\d+)\. (.+)$", adoc, flags=re.M)
    out = []
    for i in range(1, len(parts), 3):
        nr, name, body = parts[i], parts[i + 1].strip(), parts[i + 2]
        an = re.search(r"^An:: (.+)$", body, re.M).group(1).strip()
        subj = re.search(r"^\*Betreff:\* (.+)$", body, re.M).group(1).strip()
        text = re.search(r"^\.\.\.\.\n(.*?)\n\.\.\.\.$", body, re.M | re.S).group(1)
        out.append({"nr": nr, "name": name, "an": an, "subject": subj, "text": text})
    return out


def main():
    mails = parse((K / "entwuerfe.adoc").read_text(encoding="utf-8"))
    rows = {r["nr"]: r for r in csv.DictReader(open(K / "auswahl.csv", encoding="utf-8"))}
    ab_path = K / "absender.json"
    ab = json.loads(ab_path.read_text(encoding="utf-8")) if ab_path.exists() else {}
    missing = [k for k in ("vorname", "nachname", "stadt") if not ab.get(k)]

    cards = []
    for m in mails:
        t = m["text"]
        if not missing:
            t = (t.replace("[Vorname]", ab["vorname"]).replace("[Nachname]", ab["nachname"])
                  .replace("[Stadt]", ab["stadt"]))
        addr = m["an"].split()[0]
        r = rows.get(m["nr"], {})
        site = r.get("fundstelle", "")
        site_url = site if site.startswith("http") else (
            "https://" + site if re.match(r"^[\w-]+(\.[\w-]+)+(/\S*)?$", site) else "")
        sent = r.get("angeschrieben_am", "")
        if EMAIL.match(addr):
            mailto = "mailto:" + addr + "?" + urllib.parse.urlencode(
                {"subject": m["subject"], "body": t}, quote_via=urllib.parse.quote)
            proton = "https://mail.proton.me/u/0/inbox#mailto=" + urllib.parse.quote(mailto, safe="")
            send = (f'<a class="btn main" href="{html.escape(proton)}" target="_blank" rel="noopener">In Proton öffnen</a>'
                    f'<a class="btn" href="{html.escape(mailto)}">mailto</a>')
            hint = "" if "prüfen" not in m["an"] and "nicht bestätigt" not in m["an"] else \
                f'<p class="warn">Adresse unsicher: {html.escape(m["an"])}</p>'
        else:
            send = ""
            hint = f'<p class="warn">Keine Mail-Adresse: {html.escape(m["an"])}. Text kopieren und ins Formular einfügen.</p>'
        site_link = f'<a class="btn" href="{html.escape(site_url)}" target="_blank" rel="noopener">Website / Haltung prüfen</a>' if site_url else ""
        cards.append(f"""
<section class="card" id="m{m['nr']}" data-nr="{m['nr']}">
  <header>
    <label><input type="checkbox" class="done"> <span class="nr">{m['nr']}</span> {html.escape(m['name'])}</label>
    <span class="meta">{html.escape(r.get('land', ''))} · {html.escape(r.get('rolle', ''))}{' · gesendet ' + html.escape(sent) if sent else ''}</span>
  </header>
  {hint}
  <p class="to">An: <code>{html.escape(addr if EMAIL.match(addr) else '–')}</code> · Betreff: <b>{html.escape(m['subject'])}</b></p>
  <details><summary>Text ansehen</summary><pre>{html.escape(t)}</pre></details>
  <div class="btns">{send}<button class="btn copy" type="button">Text kopieren</button>{site_link}</div>
  <textarea hidden>{html.escape(t)}</textarea>
</section>""")

    warn = ("" if not missing else
            f'<p class="warn big">Absender fehlt in kontakte/absender.json: {", ".join(missing)}. '
            "Die Platzhalter stehen noch im Text.</p>")
    page = f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Civilian – Versand</title>
<style>
 body {{ font: 16px/1.5 system-ui, "DejaVu Sans", sans-serif; background: #f4f2ee; color: #161616; margin: 0; }}
 main {{ max-width: 52rem; margin: 0 auto; padding: 1.5rem 1rem 4rem; }}
 h1 {{ font-size: 1.5rem; margin: 0 0 .3rem; }}
 .rules {{ background: #fff; border-left: 4px solid #8a3b12; padding: .6rem 1rem; }}
 .card {{ background: #fff; border: 1px solid #ddd; border-radius: 6px; padding: .8rem 1rem; margin: .8rem 0; }}
 .card.is-done {{ opacity: .45; }}
 header {{ display: flex; flex-wrap: wrap; justify-content: space-between; gap: .3rem 1rem; }}
 header label {{ font-weight: 700; cursor: pointer; }}
 .nr {{ display: inline-block; min-width: 1.6rem; color: #8a3b12; }}
 .meta {{ color: #666; font-size: .85rem; }}
 .to {{ margin: .4rem 0; font-size: .9rem; }}
 pre {{ white-space: pre-wrap; font: .85rem/1.45 "DejaVu Sans Mono", monospace; background: #faf9f6; padding: .7rem; }}
 .btns {{ display: flex; flex-wrap: wrap; gap: .5rem; margin-top: .5rem; }}
 .btn {{ font: inherit; font-size: .9rem; padding: .4rem .8rem; border: 1.5px solid #161616; background: #fff;
        color: #161616; text-decoration: none; cursor: pointer; border-radius: 3px; }}
 .btn.main {{ background: #161616; color: #fff; }}
 .warn {{ color: #8a1d12; font-size: .9rem; margin: .3rem 0; }}
 .warn.big {{ font-weight: 700; font-size: 1rem; background: #fff0ec; padding: .6rem; }}
 .count {{ font-weight: 700; }}
</style></head><body><main>
<h1>Civilian – Mails einzeln versenden</h1>
<p class="count" id="count"></p>
{warn}
<div class="rules">
 <p><b>Für jede Mail:</b> 1. Website ansehen, Haltung prüfen (keine einseitige Parteinahme). 2. „In Proton öffnen“
 (vorher bei Proton angemeldet sein). 3. Text lesen, ggf. anpassen, senden. 4. Häkchen setzen.</p>
 <p>Kein CC/BCC, kein Serienbrief, nicht nachfassen. Das Häkchen wird nur in diesem Browser gespeichert;
 sag Claude, welche Nummern raus sind, dann kommt das Datum in auswahl.csv.</p>
</div>
{''.join(cards)}
</main>
<script>
 const KEY = "civilian-versand";
 const done = new Set(JSON.parse(localStorage.getItem(KEY) || "[]"));
 const upd = () => {{
   document.querySelectorAll(".card").forEach(c => c.classList.toggle("is-done", done.has(c.dataset.nr)));
   document.getElementById("count").textContent = done.size + " von " + document.querySelectorAll(".card").length + " erledigt";
   localStorage.setItem(KEY, JSON.stringify([...done]));
 }};
 document.querySelectorAll(".card").forEach(c => {{
   const cb = c.querySelector(".done");
   cb.checked = done.has(c.dataset.nr);
   cb.addEventListener("change", () => {{ cb.checked ? done.add(c.dataset.nr) : done.delete(c.dataset.nr); upd(); }});
   c.querySelector(".copy").addEventListener("click", async e => {{
     const t = c.querySelector("textarea").value;
     try {{ await navigator.clipboard.writeText(t); }} catch (_) {{
       const ta = c.querySelector("textarea"); ta.hidden = false; ta.select(); document.execCommand("copy"); ta.hidden = true; }}
     e.target.textContent = "Kopiert ✓"; setTimeout(() => e.target.textContent = "Text kopieren", 1500);
   }});
 }});
 upd();
</script>
</body></html>
"""
    (K / "versand.html").write_text(page, encoding="utf-8")
    n_mail = sum(1 for m in mails if EMAIL.match(m["an"].split()[0]))
    print(f"{len(mails)} Einträge, davon {n_mail} mit Mail-Adresse -> kontakte/versand.html"
          + (f"  (Absender fehlt: {', '.join(missing)})" if missing else ""))


if __name__ == "__main__":
    main()
