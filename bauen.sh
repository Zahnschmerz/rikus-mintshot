#!/bin/bash
# ---------------------------------------------------------------------------
# Rikus Mintshot — Paket bauen
#
# Aufruf:   ./bauen.sh          (im Wurzelverzeichnis des Projekts)
# Ergebnis: rikus-mintshot_<version>_all.deb + .sha256 im selben Ordner
#
# Die Versionsnummer wird AUS packaging/control gelesen — sie steht also nur
# an EINER Stelle.
#
# ⚠️ ZWEI DINGE, DIE HIER NICHT VERHANDELBAR SIND:
#
#   -Zxz              Neueres dpkg packt ohne Vorgabe mit »zstd«. Aeltere
#                     Systeme (Debian 11, MX 21) koennen zstd-Pakete NICHT
#                     oeffnen. Das faellt auf dem eigenen Rechner nie auf.
#
#   --root-owner-group  Wird als normaler Benutzer gebaut, gehoerten sonst alle
#                     Dateien im Paket diesem Benutzer. Auf einem fremden
#                     Rechner gehoerte das Programm dann irgendeinem dortigen
#                     Benutzer — bei einem Programm mit Systemrechten eine
#                     Sicherheitsluecke.
# ---------------------------------------------------------------------------
set -euo pipefail
cd "$(dirname "$0")"

VERSION=$(grep '^Version:' packaging/control | awk '{print $2}')
PAKET="rikus-mintshot_${VERSION}_all.deb"
BAUM=$(mktemp -d)
trap 'rm -rf "$BAUM"' EXIT

echo "Baue Rikus Mintshot $VERSION"

# --- Baum zusammenstellen: IMMER frisch aus dem Projekt --------------------
mkdir -p "$BAUM/DEBIAN" "$BAUM/opt/rikus-mintshot" \
         "$BAUM/usr/share/applications" "$BAUM/usr/share/doc/rikus-mintshot"
cp packaging/control packaging/postinst packaging/postrm "$BAUM/DEBIAN/"
cp packaging/rikus-mintshot.desktop "$BAUM/usr/share/applications/"
cp packaging/copyright "$BAUM/usr/share/doc/rikus-mintshot/"
cp rikus-mintshot.py ANLEITUNG.md GUIDE.md README.md README.de.md \
   CHANGELOG.md LICENSE "$BAUM/opt/rikus-mintshot/"
cp -r daten "$BAUM/opt/rikus-mintshot/"
find "$BAUM" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true

# --- Aenderungsprotokoll fuer apt/dpkg -------------------------------------
# -n = keinen Zeitstempel mitspeichern, damit gleiche Eingabe gleiches Paket ergibt
gzip -9n -c CHANGELOG.md > "$BAUM/usr/share/doc/rikus-mintshot/changelog.gz"

# --- Groesse eintragen (sonst meldet apt dem Nutzer "0 B") -----------------
GROESSE=$(du -sk --exclude=DEBIAN "$BAUM" | cut -f1)
sed -i "/^Installed-Size:/d" "$BAUM/DEBIAN/control"
sed -i "/^Architecture:/a Installed-Size: $GROESSE" "$BAUM/DEBIAN/control"

# --- Rechte glattziehen ----------------------------------------------------
find "$BAUM" -type d -exec chmod 755 {} +
find "$BAUM" -type f -exec chmod 644 {} +
chmod 755 "$BAUM/opt/rikus-mintshot/rikus-mintshot.py" \
          "$BAUM/DEBIAN/postinst" "$BAUM/DEBIAN/postrm"

# --- Pruefsummen der Dateien ins Paket (fuer debsums/dpkg -V) --------------
( cd "$BAUM" && find . -path ./DEBIAN -prune -o -type f -print0 \
  | xargs -0 md5sum | sed 's| \./| |' > DEBIAN/md5sums )
chmod 644 "$BAUM/DEBIAN/md5sums"

# --- Bauen -----------------------------------------------------------------
dpkg-deb -Zxz --root-owner-group --build "$BAUM" "$PAKET" >/dev/null

# --- Pruefsumme: NUR der blosse Dateiname, kein Pfad -----------------------
# Sonst schlaegt "sha256sum -c" bei jedem Fremden fehl, weil es den Pfad
# nicht gibt — und der eigene Ordnername waere mitveroeffentlicht.
sha256sum "$PAKET" > "${PAKET}.sha256"

# --- Gegenprobe: lieber hier scheitern als beim Nutzer ---------------------
echo
echo "Gegenprobe:"
ar t "$PAKET" | grep -q 'data.tar.xz' \
  && echo "  ✅ mit xz gepackt (laeuft auch auf aelteren Systemen)" \
  || { echo "  ❌ NICHT xz — Abbruch"; exit 1; }
dpkg-deb -c "$PAKET" | grep -qv 'root/root' \
  && { echo "  ❌ Dateien gehoeren nicht root — Abbruch"; exit 1; } \
  || echo "  ✅ alle Dateien gehoeren root"
[ -n "$(dpkg-deb -f "$PAKET" Installed-Size)" ] \
  && echo "  ✅ Installed-Size: $(dpkg-deb -f "$PAKET" Installed-Size) KB" \
  || { echo "  ❌ Installed-Size fehlt"; exit 1; }
dpkg-deb --ctrl-tarfile "$PAKET" | tar -t | grep -q md5sums \
  && echo "  ✅ md5sums vorhanden" || { echo "  ❌ md5sums fehlen"; exit 1; }
echo "  ✅ $PAKET ($(stat -c%s "$PAKET") Bytes)"
echo "  ✅ $(cat "${PAKET}.sha256")"
