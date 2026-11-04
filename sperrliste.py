#!/usr/bin/env python3
"""Sperrliste für Widersprüche gegen die Darstellung in Mein RVED (Art. 21 DSGVO), in zwei Stufen:

  profil  Das Seglerprofil zeigt nur den Hinweis „Privates Profil“. Name und Platzierungen bleiben in den Ergebnislisten.
  anonym  Die Person erscheint überall als „Segler/in anonymisiert“ (ohne Verein, ohne Profil, ohne Suchtreffer).

Die Liste enthält nur SHA-256-Werte, keine Namen. Schlüssel und Hash entsprechen genau MeinRVED/Sperrliste.swift.
Geschrieben werden beide Fassungen: Tools/Termine/sperrliste.json (wird per GitHub Pages veröffentlicht) und
MeinRVED/sperrliste.json (im App-Paket, wirkt auch ohne Netz).

  python3 sperrliste.py hinzufuegen --stufe anonym "Oliver Syring" [--sl 123] [--variante "Olli Syring" ...]
  python3 sperrliste.py hinzufuegen --stufe profil "Oliver Syring" --sl 123
  python3 sperrliste.py entfernen "Oliver Syring" [--sl 123]   # Widerspruch zurückgenommen
  python3 sperrliste.py pruefen "Syring, Oliver" [--sl 123]   # Stufe anzeigen
  python3 sperrliste.py schluessel "Dr. Oliver Süring"         # Schlüssel und Hash (zum Abgleich mit der App)

Ein neuer Eintrag ersetzt eine andere Stufe derselben Person. Danach veröffentlichen:
  sh Tools/Termine/veroeffentlichen.sh "Sperrliste aktualisiert"

Namen der Widersprechenden NICHT in dieses Repository schreiben (es ist öffentlich). Den Widerspruch selbst
(wer, wann, welche Stufe, welche Schreibweisen) nur im E-Mail-Postfach aufbewahren.
"""
import argparse
import datetime
import hashlib
import json
import pathlib
import unicodedata

HIER = pathlib.Path(__file__).resolve().parent
ZIELE = [HIER / "sperrliste.json", HIER.parent.parent / "MeinRVED" / "sperrliste.json"]
TITEL = {"dr", "prof", "dipl", "ing"}


def schluessel(name: str) -> str:
    s = name.replace("ß", "ss").replace("ẞ", "ss")
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)).lower()
    tokens, aktuell = [], ""
    for c in s:
        if c.isalpha():
            aktuell += c
        elif aktuell:
            tokens.append(aktuell)
            aktuell = ""
    if aktuell:
        tokens.append(aktuell)
    return " ".join(sorted(t for t in tokens if t not in TITEL))


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def hash_name(name: str) -> str:
    k = schluessel(name)
    if not k:
        raise SystemExit(f"Kein gültiger Name: {name!r}")
    return sha("meinrved:name:" + k)


def hash_sl(sl: int) -> str:
    return sha(f"meinrved:sl:{sl}")


STUFEN = ("anonym", "profil")


def laden() -> dict:
    """Stand der Liste; beide Dateien werden zusammengeführt (falls eine von Hand geändert wurde)."""
    liste = {k: set() for k in STUFEN}
    for p in ZIELE:
        if p.exists():
            daten = json.loads(p.read_text(encoding="utf-8"))
            for k in STUFEN:
                liste[k] |= set(daten.get(k, []))
    liste["profil"] -= liste["anonym"]
    return liste


def speichern(liste: dict) -> None:
    daten = {
        "hinweis": "Widersprüche nach Art. 21 DSGVO gegen die Darstellung in Mein RVED. Nur SHA-256-Werte, keine Namen. "
                   "anonym = überall anonymisiert, profil = nur das Seglerprofil ist privat.",
        "stand": datetime.date.today().isoformat(),
        "anonym": sorted(liste["anonym"]),
        "profil": sorted(liste["profil"] - liste["anonym"]),
    }
    text = json.dumps(daten, ensure_ascii=False, indent=2) + "\n"
    for p in ZIELE:
        p.write_text(text, encoding="utf-8")
        print(f"geschrieben: {p}")


def werte(a) -> set:
    return {hash_name(n) for n in [a.name, *getattr(a, "variante", [])]} | {hash_sl(n) for n in a.sl}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="befehl", required=True)
    h = sub.add_parser("hinzufuegen")
    h.add_argument("--stufe", choices=STUFEN, required=True)
    h.add_argument("name")
    h.add_argument("--sl", type=int, action="append", default=[], help="Segler-Nummer bei wsge.de (segler/?sl=…)")
    h.add_argument("--variante", action="append", default=[], help="weitere Schreibweise des Namens")
    e = sub.add_parser("entfernen")
    e.add_argument("name")
    e.add_argument("--sl", type=int, action="append", default=[])
    e.add_argument("--variante", action="append", default=[])
    p = sub.add_parser("pruefen")
    p.add_argument("name")
    p.add_argument("--sl", type=int, action="append", default=[])
    s = sub.add_parser("schluessel")
    s.add_argument("name")
    a = ap.parse_args()

    if a.befehl == "schluessel":
        print(schluessel(a.name), hash_name(a.name))
        return
    liste = laden()
    if a.befehl == "pruefen":
        w = werte(a)
        stufe = next((k for k in STUFEN if w & liste[k]), "keine")
        print(f"Stufe: {stufe}")
    elif a.befehl == "entfernen":
        w = werte(a)
        vorher = sum(len(liste[k]) for k in STUFEN)
        for k in STUFEN:
            liste[k] -= w
        speichern(liste)
        print(f"{vorher - sum(len(liste[k]) for k in STUFEN)} Einträge entfernt.")
        print("Im App-Paket bleibt der Eintrag bis zum nächsten Update, falls er dort schon enthalten war.")
    else:
        w = werte(a)
        andere = "profil" if a.stufe == "anonym" else "anonym"
        liste[andere] -= w
        neu = w - liste[a.stufe]
        liste[a.stufe] |= w
        speichern(liste)
        print(f"{len(neu)} neue Einträge in Stufe {a.stufe}.")
        print('Danach: sh Tools/Termine/veroeffentlichen.sh "Sperrliste aktualisiert"')
        if a.stufe == "anonym":
            print("Mit dem nächsten App-Update die Seed-Dateien (MeinRVED/Seed) und das Quellen-Archiv bereinigen.")


if __name__ == "__main__":
    main()
