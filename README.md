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

Am einfachsten geht das im Browser: https://meinrved.syring-digital.de/verwaltung/ (Quelle `verwaltung/index.html`, braucht einen
GitHub-Zugangsschlüssel mit „Contents: Read and write“ für dieses Repo). Oder im Terminal; jeder Befehl holt zuerst den Stand von GitHub,
„hinzufuegen“ und „entfernen“ veröffentlichen sofort:

    python3 sperrliste.py hinzufuegen --stufe anonym "Vorname Nachname" --sl <WSGE-Nummer> --variante "andere Schreibweise"
    python3 sperrliste.py hinzufuegen --stufe profil "Vorname Nachname" --sl <WSGE-Nummer>
    python3 sperrliste.py entfernen "Vorname Nachname" --sl <WSGE-Nummer>
    python3 sperrliste.py holen      # vor jedem App-Build: Stand von GitHub ins App-Paket übernehmen

`veroeffentlichen.sh` holt die Sperrliste ebenfalls zuerst von GitHub, damit Änderungen aus dem Browser nicht überschrieben werden.

Das Skript schreibt auch `MeinRVED/sperrliste.json` (im App-Paket). Schlüssel und Hash müssen mit `MeinRVED/Sperrliste.swift` übereinstimmen.

## Aktuelles (Meldungen der Startseite)

`aktuelles.json` enthält die Meldungen, die die App unter „Aktuelles“ anzeigt (Felder `title`, `date`, `url`; oben steht die neueste).
Veröffentlicht unter `https://syring-digital.github.io/meinrved-termine/aktuelles.json`; die App (ab 0.25.1) lädt sie beim Öffnen der Startseite.
Gepflegt wird sie im Browser unter https://meinrved.syring-digital.de/verwaltung/ (Reiter „Aktuelles“, gleicher Zugangsschlüssel wie für die Sperrliste):
Hinzufügen, Bearbeiten, Löschen, Umsortieren, dann „Speichern“. Titel, Datum und Link werden von Hand eingetragen.
Wie bei der Sperrliste ist der Stand auf GitHub maßgeblich; `veroeffentlichen.sh` zieht ihn vor dem Abgleich.
