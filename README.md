# Kalenderabo der Termine

`termine_ics.py` liest die Termin-Seiten von wsge.de (gleiche Regeln wie `EventsService.swift` in der App) und schreibt `termine.ics`.
Der Workflow `.github/workflows/termine.yml` läuft mehrmals täglich und veröffentlicht die Datei über GitHub Pages:
`https://syring-digital.github.io/meinrved-termine/termine.ics` (in der App als `webcal://`-Link).
Spiegel-Repository: `syring-digital/meinrved-termine`, übertragen mit `veroeffentlichen.sh`.

## Sperrliste (Widersprüche gegen die Darstellung in den Ergebnissen)

`sperrliste.json` wird zusammen mit `termine.ics` über GitHub Pages veröffentlicht
(`https://syring-digital.github.io/meinrved-termine/sperrliste.json`). Die App lädt sie und zeigt gesperrte Personen
in zwei Stufen: `profil` (nur das Seglerprofil ist privat) und `anonym` (überall „Segler/in anonymisiert“).
Die Liste enthält nur SHA-256-Werte, keine Namen.

    python3 sperrliste.py hinzufuegen --stufe anonym "Vorname Nachname" --sl <WSGE-Nummer> --variante "andere Schreibweise"
    python3 sperrliste.py hinzufuegen --stufe profil "Vorname Nachname" --sl <WSGE-Nummer>
    python3 sperrliste.py entfernen "Vorname Nachname" --sl <WSGE-Nummer>
    sh veroeffentlichen.sh "Sperrliste aktualisiert"

Das Skript schreibt auch `MeinRVED/sperrliste.json` (im App-Paket). Schlüssel und Hash müssen mit `MeinRVED/Sperrliste.swift` übereinstimmen.
