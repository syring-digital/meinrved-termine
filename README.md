# Kalenderabo der Termine

`termine_ics.py` liest die Termin-Seiten von wsge.de (gleiche Regeln wie `EventsService.swift` in der App) und schreibt `termine.ics`.
Der Workflow `.github/workflows/termine.yml` läuft mehrmals täglich und veröffentlicht die Datei über GitHub Pages:
`https://syring-digital.github.io/meinrved-termine/termine.ics` (in der App als `webcal://`-Link).
Spiegel-Repository: `syring-digital/meinrved-termine`, übertragen mit `veroeffentlichen.sh`.
