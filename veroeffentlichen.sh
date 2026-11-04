#!/bin/sh
# Überträgt Tools/Termine in das GitHub-Repository syring-digital/meinrved-termine (Spiegel außerhalb von iCloud).
set -e
SRC="$(cd "$(dirname "$0")" && pwd)"
DST="$HOME/Library/Application Support/MeinRVED-Termine/repo"
if [ ! -d "$DST/.git" ]; then
  git clone -q https://github.com/syring-digital/meinrved-termine.git "$DST"
  # öffentliches Repository: anonyme GitHub-Adresse statt privater E-Mail
  git -C "$DST" config user.name "Jakob Syring"
  git -C "$DST" config user.email "345268148+syring-digital@users.noreply.github.com"
fi
# Die Sperrliste kann auch über die Webseite (verwaltung/) geändert werden: maßgeblich ist der Stand auf GitHub.
# Erst holen, damit rsync sie nicht mit einer älteren lokalen Fassung überschreibt.
git -C "$DST" pull -q --ff-only origin main
if [ -f "$DST/sperrliste.json" ]; then
  cp "$DST/sperrliste.json" "$SRC/sperrliste.json"
  cp "$DST/sperrliste.json" "$SRC/../../MeinRVED/sperrliste.json"
fi
rsync -a --delete --exclude .git --exclude site --exclude __pycache__ "$SRC"/ "$DST"/
cd "$DST"
git add -A
if git diff --cached --quiet; then echo "Keine Änderungen."; exit 0; fi
git commit -q -m "${1:-Stand aus Mein RVED übernommen}"
git push -q origin HEAD:main
echo "Übertragen: $(git log --oneline -1)"
