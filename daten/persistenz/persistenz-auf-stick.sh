#!/bin/bash
# Linux Mint Snapshot — Stick-Persistenz-Helfer.
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
# gibt es die Kiste schon?
if blkid -L persistence 2>/dev/null | grep -q "^${DEV}"; then
  echo "Auf $DEV existiert bereits eine Persistenz-Kiste — nichts zu tun."; exit 0; fi

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
M=$(mktemp -d)
mount "$PART" "$M"
if [ "$MODUS" = "home" ]; then printf '/home union\n' > "$M/persistence.conf"
else printf '/ union\n' > "$M/persistence.conf"; fi
sync
umount "$M"; rmdir "$M"

echo "FERTIG: Persistenz-Kiste ($MODUS) auf $PART angelegt."
