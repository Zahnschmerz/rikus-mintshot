#!/bin/bash
# Rikus Mintshot — Stick-Persistenz-Helfer.
# Legt auf einem USB-Stick, der bereits die Snapshot-ISO traegt, im FREIEN Platz
# dahinter eine Persistenz-Partition (Label "persistence", ext4) an und schreibt
# die persistence.conf hinein. Die ISO-Partitionen bleiben UNANGETASTET.
#
# Aufruf (als root):  persistenz-auf-stick.sh  <GERAET>  <all|home>  [groesse_MiB]
#   GERAET       z.B. /dev/sdb   (NUR die ganze Platte, keine Partition)
#   all|home     all  = alles merken (/ union)   home = nur /home merken
#   groesse_MiB  optional; leer/0 = restlichen freien Platz nutzen
set -e
DEV="$1"; MODUS="$2"; GROESSE="${3:-0}"
BASE=$(basename "$DEV")

# --- Sicherheitsnetze ---
[ -b "$DEV" ] || { echo "FEHLER: $DEV ist kein Blockgeraet."; exit 1; }
[ "$(cat /sys/block/$BASE/removable 2>/dev/null)" = "1" ] || {
  echo "FEHLER: $DEV ist KEIN Wechseldatentraeger — abgebrochen (Schutz)."; exit 1; }
# muss die Snapshot-ISO tragen: Partition 1 = ISO9660
if ! blkid "${DEV}1" 2>/dev/null | grep -qi 'iso9660'; then
  echo "FEHLER: Auf $DEV liegt keine Snapshot-ISO (ISO9660). Erst die ISO schreiben."; exit 1; fi
# gibt es die Kiste schon? Dann pruefen, ob sie VOLLSTAENDIG ist — sonst reparieren.
# (Haeufigster Fehler: das Anlegen brach nach dem Formatieren ab, die Kiste blieb
#  leer -> ohne persistence.conf/rw/work gibt es KEINE Persistenz. Hier heilen wir das.)
EXIST=$(blkid -L persistence 2>/dev/null | grep "^${DEV}" | head -1 | cut -d: -f1)
if [ -n "$EXIST" ]; then
  MR=$(mktemp -d)
  if mount "$EXIST" "$MR" 2>/dev/null; then
    if [ -f "$MR/persistence.conf" ] && [ -d "$MR/rw" ] && [ -d "$MR/work" ]; then
      umount "$MR"; rmdir "$MR"
      echo "Auf $DEV existiert bereits eine vollstaendige Persistenz-Kiste — nichts zu tun."; exit 0
    fi
    # unvollstaendige/leere Kiste: die fehlende Konfiguration nachtragen (reparieren)
    if [ "$MODUS" = "home" ]; then printf '/home union\n' > "$MR/persistence.conf"
    else printf '/ union\n' > "$MR/persistence.conf"; fi
    mkdir -p "$MR/rw" "$MR/work"
    sync; umount "$MR"; rmdir "$MR"
    echo "FERTIG: unvollstaendige Persistenz-Kiste auf $EXIST repariert (Modus $MODUS)."; exit 0
  fi
  rmdir "$MR" 2>/dev/null
  echo "FEHLER: Kiste $EXIST ist vorhanden, laesst sich aber nicht einbinden."; exit 1
fi

# --- GPT-Backup ans Ende schieben (macht den freien Platz nutzbar) ---
sgdisk -e "$DEV" >/dev/null 2>&1 || true

# --- neue Partition anlegen (im freien Platz, Name+Typ Linux) ---
if [ "$GROESSE" -gt 0 ] 2>/dev/null; then ENDE="+${GROESSE}M"; else ENDE="0"; fi
sgdisk -n "0:0:${ENDE}" -t 0:8300 -c 0:persistence "$DEV" >/dev/null
partprobe "$DEV" 2>/dev/null || true
udevadm settle 2>/dev/null || true

# --- neu angelegte (hoechstnummerierte) Partition finden ---
PART=$(lsblk -lnp -o NAME "$DEV" | grep -E "^${DEV}p?[0-9]+$" | sort -V | tail -1)
[ -b "$PART" ] || { echo "FEHLER: neue Partition nicht gefunden."; exit 1; }

# --- als ext4 mit Label "persistence" formatieren ---
mke2fs -F -q -t ext4 -L persistence "$PART" >/dev/null

# --- persistence.conf hineinschreiben ---
# WICHTIG: Direkt nach dem Formatieren re-scannt udev die Partition, sie ist
# kurz "busy" -> ein sofortiger mount scheitert und die Kiste bliebe LEER
# (kein persistence.conf/rw/work = keine Persistenz). Darum: warten + mehrfach
# versuchen, und bei endgueltigem Fehlschlag hart abbrechen (nicht still leer lassen).
udevadm settle 2>/dev/null || true
sync
partprobe "$DEV" 2>/dev/null || true
M=$(mktemp -d)
_gemountet=0
for _v in 1 2 3 4 5 6 7 8; do
  if mount "$PART" "$M" 2>/dev/null; then _gemountet=1; break; fi
  udevadm settle 2>/dev/null || true
  sleep 1
done
[ "$_gemountet" = 1 ] || { echo "FEHLER: Kiste $PART liess sich nicht einbinden (Timing). Bitte erneut versuchen."; exit 1; }
if [ "$MODUS" = "home" ]; then printf '/home union\n' > "$M/persistence.conf"
else printf '/ union\n' > "$M/persistence.conf"; fi
# overlayfs braucht diese Ordner auf der Kiste, sonst schlaegt der Persistenz-Boot fehl
mkdir -p "$M/rw" "$M/work"
sync
umount "$M"; rmdir "$M"

echo "FERTIG: Persistenz-Kiste ($MODUS) auf $PART angelegt."
