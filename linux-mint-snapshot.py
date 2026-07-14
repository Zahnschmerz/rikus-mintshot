#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Rikus Mintshot (v5.0) — 1:1 clone of the running system as a bootable live ISO.
# Published by / Herausgeber: Gilbert Rikus — License: GPL-3.0-or-later
#
# v5 = the "clone model" (Gilbert's product decision, 2026-07-07, MX-Snapshot-like):
#   * The snapshot is a 1:1 CLONE: account, settings and saved logins ALWAYS included.
#     Big folders (Documents, Pictures, VMs ...) can be left out via checkboxes.
#   * The live stick boots STRAIGHT into the owner's own session (real user, autologin),
#     not into an artificial "mint" user.
#   * The installer (Calamares) does a 1:1 clone install: no user-creation page,
#     no locale/keyboard pages — it only prepares the target disk and the bootloader.
#   * The app itself lives in /opt/linux-mint-snapshot (installed by the assistant),
#     so it is part of every clone — like mx-snapshot on MX Linux.
#   * Everything else proven in v4 stays: language table DE/EN, dynamic distro/user
#     values, sudo -n/pkexec, first-start assistant, crash-safe build engine.
#   * Self test: MINT_SNAP_TEST=1 ./linux-mint-snapshot.py --selbsttest

import os
import re
import sys
import glob
import json
import getpass
import shutil
import subprocess
import threading
import datetime

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Pango, GdkPixbuf

VERSION = "5.4"
APP_ORDNER = os.path.dirname(os.path.abspath(__file__))
SYSTEM_ORDNER = '/opt/linux-mint-snapshot'
DATEN = os.path.join(APP_ORDNER, 'daten')
KONFIG_ORDNER = os.path.expanduser('~/.config/linux-mint-snapshot')
LOG_DATEI = os.path.join(KONFIG_ORDNER, 'letzter-lauf.log')
PID_DATEI = os.path.join(KONFIG_ORDNER, 'lauf.pid')
EINRICHT_LOG = os.path.join(KONFIG_ORDNER, 'einrichtung.log')
WEGLASSEN_DATEI = os.path.join(KONFIG_ORDNER, 'weglassen.json')
ZUSATZ_DATEI = os.path.join(KONFIG_ORDNER, 'zusatz-ordner.json')
ISO_ORDNER = '/home/snapshot'
REFRACTA_DEB_URL = ('https://master.dl.sourceforge.net/project/refracta/tools/'
                    'refractasnapshot-base_10.2.12_all.deb?viasf=1')
CALA_MARKER = 'lms-config-v5'
PROZENT_MUSTER = re.compile(r'(\d{1,3})%')
SCHRITT_MUSTER = re.compile(r'(?:Schritt|Step) (\d)')

FAKE_MOTOR = (
    "echo 'Selbsttest: pruefe Voraussetzungen'; sleep 1; "
    "echo 'mksquashfs startet'; "
    "for p in 5 25 50 75 95; do echo \"[==    ] 100/2000 ${p}%\"; sleep 1; done; "
    "echo 'Creating CD/DVD image file...'; sleep 1; "
    "touch \"$MINT_SNAP_TESTORDNER/selbsttest.iso\"; "
    "echo 'All finished!'"
)

# ======================= Sprache =======================

def _systemsprache():
    lang = (os.environ.get('LC_ALL') or os.environ.get('LC_MESSAGES')
            or os.environ.get('LANG') or 'en')
    return 'de' if lang.lower().startswith('de') else 'en'

SPRACHE = _systemsprache()

SPRACHNAMEN = {  # Anzeigename fuers Boot-Menue (Muttersprache des Nutzers)
    'de': 'Deutsch', 'en': 'English', 'fr': 'Français', 'es': 'Español',
    'it': 'Italiano', 'pt': 'Português', 'nl': 'Nederlands', 'pl': 'Polski',
    'cs': 'Čeština', 'hu': 'Magyar', 'sv': 'Svenska', 'da': 'Dansk',
    'fi': 'Suomi', 'nb': 'Norsk', 'tr': 'Türkçe', 'ru': 'Русский',
    'uk': 'Українська', 'el': 'Ελληνικά', 'ro': 'Română', 'bg': 'Български',
}

T_ALLE = {
 'de': {
  'untertitel': "1:1-Klon deines Linux-Mint-Systems als startfähige ISO — mit einem Klick",
  'herausgeber': "Herausgeber: Gilbert Rikus · GPL-3 · v{v}",
  'knopf_ueber': "ℹ️ Über",
  'frame_auswahl': " Was kommt in den Schnappschuss? ",
  'klon_info': "Wähle, was in den Schnappschuss kommt:",
  'home_ohne': "Nur System (root) — klein & schnell  (★ empfohlen)",
  'home_mit': "System (root) + Home — alles dabei (deine Dateien & dein Konto)",
  'weglassen_titel': "Einzelne große Ordner weglassen? (Häkchen = bleibt draußen)",
  'fortgeschritten_titel': "⚙️  Für Fortgeschrittene: einzelne Ordner weglassen",
  'privat_hinweis': ("🔒 Der Stick enthält dein Konto und deine Zugänge —\n"
                     "sicher verwahren und nicht an Fremde weitergeben."),
  'groesse_offen': "wird gemessen …",
  'anzeige_vms': "Virtuelle Maschinen (VMs)",
  'anzeige_steam': "Steam-Spiele",
  'anzeige_flatpak': "Flatpak-Programme (systemweit)",
  'zusatz_knopf': "➕ Weiteren Ordner weglassen …",
  'zusatz_titel': "Ordner zum Weglassen wählen",
  'zusatz_add': "Weglassen",
  'zusatz_abbr': "Abbrechen",
  'zusatz_nurhome_titel': "Nur eigene Ordner",
  'zusatz_nurhome_text': ("Bitte nur einen Ordner INNERHALB deines Persönlichen Ordners wählen.\n"
                          "Ein System-Ordner oder der Persönliche Ordner selbst würde den Klon\n"
                          "leeren oder unbootbar machen."),
  'knopf_bauen': "  📸  Schnappschuss jetzt erstellen  ",
  'knopf_abbruch': "✋ Abbrechen",
  'bereit': "Bereit — klicke auf »Schnappschuss jetzt erstellen«.",
  'bereit_kurz': "Bereit.",
  'konfig_fehlt': "Konfiguration fehlt",
  'schritt1': "Schritt 1 von 3: Prüfe Voraussetzungen und kopiere das System … (dauert am längsten)",
  'schritt2': "Schritt 2 von 3: Komprimiere das System …",
  'schritt3': "Schritt 3 von 3: Baue die startfähige ISO …",
  'schritt4': "Fast fertig: mache die ISO Secure-Boot-fähig …",
  'fertig_phase': "✅ Fertig: {iso}",
  'fertig_titel': "✅ Schnappschuss fertig!",
  'fertig_text': ("{iso}\nGröße: {groesse}  →  der USB-Stick muss mindestens so groß sein.\n\n"
                  "Nächster Schritt: unten auswählen und »Auf USB-Stick schreiben« klicken.\n\n"
                  "Gut zu wissen: Der Stick startet direkt in deine gewohnte Umgebung\n"
                  "(Benutzer »{liveuser}«). Zum Installieren liegt das Symbol\n"
                  "»System installieren« auf dem Schreibtisch — die Installation\n"
                  "übernimmt alles 1:1, auch dein Konto.\n\n"
                  "🔒 Der Stick enthält deine Zugänge — sicher verwahren!"),
  'kein_abbild_phase': "❌ Es ist keine neue ISO entstanden.",
  'kein_abbild_titel': "Kein Abbild entstanden",
  'kein_abbild_text': ("Der Lauf endete ohne neue ISO.\n"
                       "Ein Blick in »Technische Einzelheiten« zeigt den Grund."),
  'abbruch_titel': "Bau wirklich abbrechen?",
  'abbruch_text': "Die halbfertigen Arbeitsdateien werden aufgeräumt.",
  'abgebrochen': "Abgebrochen — Arbeitsdateien aufgeräumt.",
  'lauf_gefunden': "Laufender Bau gefunden — Anzeige wieder angekoppelt …",
  'details': "Technische Einzelheiten (nur für den Notfall)",
  'frame_liste': " Fertige Abbilder ",
  'spalte_datei': "Datei", 'spalte_groesse': "Größe", 'spalte_erstellt': "Erstellt",
  'knopf_stick': "🖊️ Auf USB-Stick schreiben",
  'knopf_pruef': "🔍 Stick kontrollieren (Prüfsumme)",
  'knopf_loesch': "🗑️ Löschen",
  'ablage': "Ablageort: <b>{ordner}</b>   ·   Freier Platz: <b>{platz}</b>",
  'erst_auswaehlen_titel': "Bitte erst auswählen",
  'auswahl_schreiben': "Wähle in der Liste die ISO aus, die auf den Stick soll.",
  'auswahl_pruefen': "Wähle in der Liste die ISO aus, mit der der Stick verglichen werden soll.",
  'auswahl_loeschen': "Wähle in der Liste die ISO aus, die gelöscht werden soll.",
  'pruef_laeuft': "🔍 Kontrolliere den Stick — dauert einige Minuten, bitte warten …",
  'kein_stick_titel': "Kein USB-Stick gefunden",
  'kein_stick_text': "Bitte den Stick einstecken und erneut kontrollieren.",
  'stick_ok_titel': "✅ Stick ist PERFEKT",
  'stick_ok_text': ("Der Stick {geraet} stimmt bit-genau mit\n{iso} überein.\n\n"
                    "So benutzt du den Stick:\n"
                    "1. Rechner neu starten und das Boot-Menü öffnen\n"
                    "    (meist F12 — je nach Gerät auch F2, F8 oder Esc)\n"
                    "2. Den USB-Stick auswählen\n"
                    "3. Im Startmenü den ersten Eintrag wählen\n"
                    "4. Das System startet direkt in deine gewohnte Umgebung\n"
                    "5. Zum Installieren: Doppelklick auf »System installieren«\n"
                    "    direkt auf dem Schreibtisch — es wird 1:1 übernommen"),
  'stick_falsch_titel': "❌ Stick weicht ab!",
  'stick_falsch_text': ("Der Stick {geraet} stimmt NICHT mit der ISO überein.\n"
                        "Bitte neu schreiben oder anderen Stick nehmen."),
  'pruef_fehler': "Kontrolle fehlgeschlagen",
  'loesch_titel': "{iso} wirklich löschen?",
  'loesch_text': "Auch die zugehörigen Prüfsummen-Dateien werden entfernt.",
  'einr_titel': "Ersteinrichtung nötig",
  'einr_text': ("Damit die App ISOs bauen kann, fehlt auf diesem Rechner noch:\n\n{fehlt}\n\n"
                "Soll ich das jetzt automatisch installieren und einrichten?\n"
                "Dabei wird die App auch fest ins System eingebaut — dadurch ist sie\n"
                "in jedem Schnappschuss gleich mit drin.\n"
                "(Dafür wird einmal dein Passwort gebraucht. Internet nötig.\n"
                "Hinweis: Der Baustein »live-boot« erneuert dabei die Start-Datei\n"
                "des Systems — das ist normal und beim gewöhnlichen Start ohne Wirkung.)"),
  'einr_laeuft': "🔧 Richte ein … (Einzelheiten im Klapp-Bereich unten)",
  'einr_fertig_titel': "✅ Einrichtung abgeschlossen",
  'einr_fertig_text': "Alles bereit — du kannst jetzt deinen ersten Schnappschuss erstellen.",
  'einr_fehler_titel': "Einrichtung unvollständig",
  'einr_fehler_text': ("Es sind Fehler aufgetreten. Die Einzelheiten stehen im\n"
                       "Klapp-Bereich unten und in {log}."),
  'einr_knopf': "🔧 Jetzt einrichten",
  'einr_spaeter': "Später",
  'einr_hinweis_phase': "⚠️ Ersteinrichtung nötig — Klick auf »Jetzt einrichten« unten.",
 },
 'en': {
  'untertitel': "1:1 clone of your Linux Mint system as a bootable ISO — one click",
  'herausgeber': "Published by Gilbert Rikus · GPL-3 · v{v}",
  'knopf_ueber': "ℹ️ About",
  'frame_auswahl': " What goes into the snapshot? ",
  'klon_info': "Choose what goes into the snapshot:",
  'home_ohne': "System (root) only — small & fast  (★ recommended)",
  'home_mit': "System (root) + Home — everything (your files & account)",
  'weglassen_titel': "Leave out individual big folders? (checked = stays out)",
  'fortgeschritten_titel': "⚙️  Advanced: leave out individual folders",
  'privat_hinweis': ("🔒 The stick contains your account and credentials —\n"
                     "keep it in a safe place and never hand it to strangers."),
  'groesse_offen': "measuring …",
  'anzeige_vms': "Virtual machines (VMs)",
  'anzeige_steam': "Steam games",
  'anzeige_flatpak': "Flatpak apps (system-wide)",
  'zusatz_knopf': "➕ Leave out another folder …",
  'zusatz_titel': "Choose a folder to leave out",
  'zusatz_add': "Leave out",
  'zusatz_abbr': "Cancel",
  'zusatz_nurhome_titel': "Only your own folders",
  'zusatz_nurhome_text': ("Please pick a folder INSIDE your personal home folder.\n"
                          "A system folder or the home folder itself would empty the clone\n"
                          "or make it unbootable."),
  'knopf_bauen': "  📸  Create snapshot now  ",
  'knopf_abbruch': "✋ Cancel",
  'bereit': "Ready — click »Create snapshot now«.",
  'bereit_kurz': "Ready.",
  'konfig_fehlt': "Configuration missing",
  'schritt1': "Step 1 of 3: Checking requirements and copying the system … (longest part)",
  'schritt2': "Step 2 of 3: Compressing the system …",
  'schritt3': "Step 3 of 3: Building the bootable ISO …",
  'schritt4': "Almost done: making the ISO Secure-Boot-capable …",
  'fertig_phase': "✅ Done: {iso}",
  'fertig_titel': "✅ Snapshot finished!",
  'fertig_text': ("{iso}\nSize: {groesse}  →  your USB stick must be at least this big.\n\n"
                  "Next step: select it below and click »Write to USB stick«.\n\n"
                  "Good to know: the stick boots straight into your usual environment\n"
                  "(user »{liveuser}«). To install, double-click the »Install System«\n"
                  "icon right on the desktop — the installation is a 1:1 takeover,\n"
                  "including your account.\n\n"
                  "🔒 The stick contains your credentials — keep it safe!"),
  'kein_abbild_phase': "❌ No new ISO was created.",
  'kein_abbild_titel': "No image created",
  'kein_abbild_text': ("The run ended without a new ISO.\n"
                       "»Technical details« below shows the reason."),
  'abbruch_titel': "Really cancel the build?",
  'abbruch_text': "Half-finished working files will be cleaned up.",
  'abgebrochen': "Cancelled — working files cleaned up.",
  'lauf_gefunden': "Found a running build — display re-attached …",
  'details': "Technical details (for emergencies only)",
  'frame_liste': " Finished images ",
  'spalte_datei': "File", 'spalte_groesse': "Size", 'spalte_erstellt': "Created",
  'knopf_stick': "🖊️ Write to USB stick",
  'knopf_pruef': "🔍 Verify stick (checksum)",
  'knopf_loesch': "🗑️ Delete",
  'ablage': "Location: <b>{ordner}</b>   ·   Free space: <b>{platz}</b>",
  'erst_auswaehlen_titel': "Please select first",
  'auswahl_schreiben': "Select the ISO in the list that should go onto the stick.",
  'auswahl_pruefen': "Select the ISO in the list to compare the stick against.",
  'auswahl_loeschen': "Select the ISO in the list that should be deleted.",
  'pruef_laeuft': "🔍 Verifying the stick — takes a few minutes, please wait …",
  'kein_stick_titel': "No USB stick found",
  'kein_stick_text': "Please plug in the stick and verify again.",
  'stick_ok_titel': "✅ Stick is PERFECT",
  'stick_ok_text': ("The stick {geraet} matches\n{iso} bit for bit.\n\n"
                    "How to use the stick:\n"
                    "1. Restart the computer and open the boot menu\n"
                    "    (usually F12 — on some machines F2, F8 or Esc)\n"
                    "2. Choose the USB stick\n"
                    "3. Pick the first entry in the start menu\n"
                    "4. The system boots straight into your usual environment\n"
                    "5. To install: double-click »Install System«\n"
                    "    right on the desktop — a 1:1 takeover"),
  'stick_falsch_titel': "❌ Stick differs!",
  'stick_falsch_text': ("The stick {geraet} does NOT match the ISO.\n"
                        "Please write it again or use another stick."),
  'pruef_fehler': "Verification failed",
  'loesch_titel': "Really delete {iso}?",
  'loesch_text': "The matching checksum files will be removed too.",
  'einr_titel': "First-time setup required",
  'einr_text': ("Before this app can build ISOs, this computer is still missing:\n\n{fehlt}\n\n"
                "Install and configure everything automatically now?\n"
                "This also installs the app into the system itself — that way it is\n"
                "included in every snapshot.\n"
                "(Your password is needed once. Internet required.\n"
                "Note: the »live-boot« component refreshes the system's start file —\n"
                "that is normal and has no effect on ordinary boots.)"),
  'einr_laeuft': "🔧 Setting up … (details in the expander below)",
  'einr_fertig_titel': "✅ Setup complete",
  'einr_fertig_text': "All set — you can create your first snapshot now.",
  'einr_fehler_titel': "Setup incomplete",
  'einr_fehler_text': ("Errors occurred. Details are in the expander below\n"
                       "and in {log}."),
  'einr_knopf': "🔧 Set up now",
  'einr_spaeter': "Later",
  'einr_hinweis_phase': "⚠️ First-time setup required — click »Set up now« below.",
 },
}
T = T_ALLE[SPRACHE]

# ======================= System-Dynamik =======================

def _lauf(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:
        return ''

def distro_name():
    name = _lauf(['lsb_release', '-is']) or ''
    ver = _lauf(['lsb_release', '-rs']) or ''
    if name.lower() == 'linuxmint':
        name = 'Linux Mint'
    if not name:
        daten = {}
        try:
            for zeile in open('/etc/os-release'):
                if '=' in zeile:
                    k, w = zeile.strip().split('=', 1)
                    daten[k] = w.strip('"')
        except FileNotFoundError:
            pass
        name = daten.get('NAME', 'Linux')
        ver = daten.get('VERSION_ID', '')
    return f"{name} {ver}".strip()

DISTRO = distro_name()
DISTRO_KURZ = re.sub(r'[^A-Za-z0-9]+', '', DISTRO.split(' ' )[0] + DISTRO.split(' ')[1] if len(DISTRO.split(' ')) > 1 else DISTRO) or 'Linux'

# Der Live-Stick startet als der ECHTE Besitzer des Systems (Klon-Modell):
LIVE_USER = getpass.getuser()

def nutzer_locale():
    lang = os.environ.get('LANG') or 'en_US.UTF-8'
    return lang if '.' in lang else lang + '.UTF-8'

def nutzer_tastatur():
    try:
        for zeile in open('/etc/default/keyboard'):
            if zeile.startswith('XKBLAYOUT='):
                return zeile.split('=', 1)[1].strip().strip('"').split(',')[0] or 'us'
    except FileNotFoundError:
        pass
    return SPRACHE if SPRACHE != 'en' else 'us'

def nutzer_zeitzone():
    try:
        return open('/etc/timezone').read().strip()
    except FileNotFoundError:
        ziel = os.path.realpath('/etc/localtime')
        return ziel.split('zoneinfo/')[-1] if 'zoneinfo/' in ziel else 'UTC'

def sprach_anzeige():
    code = (os.environ.get('LANG') or 'en')[:2].lower()
    return SPRACHNAMEN.get(code, code)

def groesse_lesbar(bytes_):
    for einheit in ('B', 'KB', 'MB', 'GB', 'TB'):
        if bytes_ < 1024 or einheit == 'TB':
            return f"{bytes_:.1f} {einheit}" if einheit != 'B' else f"{int(bytes_)} B"
        bytes_ /= 1024

def root_praefix():
    """Passwortloses sudo, wenn vorhanden (z. B. lm) — sonst pkexec-Passwortdialog."""
    if subprocess.run(['sudo', '-n', 'true'], capture_output=True).returncode == 0:
        return 'sudo -n'
    return 'pkexec'

def dicke_ordner():
    """Kandidaten fuer die Weglassen-Haekchen: die grossen sichtbaren Ordner des
    Nutzers (XDG-Namen beruecksichtigen Uebersetzungen wie 'Bilder') + Sonderfaelle.
    Die unsichtbaren Einstellungs-Ordner stehen NIE zur Wahl — 1:1-Prinzip."""
    home = os.path.expanduser('~')
    xdg = {}
    try:
        for zeile in open(os.path.join(home, '.config/user-dirs.dirs')):
            m = re.match(r'XDG_(\w+)_DIR="?\$HOME/([^"\n]+)"?', zeile.strip())
            if m:
                xdg[m.group(1)] = os.path.join(home, m.group(2))
    except OSError:
        pass
    kandidaten = []
    for schluessel, fallback in (('DOCUMENTS', 'Documents'), ('PICTURES', 'Pictures'),
                                 ('VIDEOS', 'Videos'), ('MUSIC', 'Music'),
                                 ('DOWNLOAD', 'Downloads'), ('DESKTOP', 'Desktop')):
        pfad = xdg.get(schluessel, os.path.join(home, fallback))
        if os.path.isdir(pfad) and pfad != home:
            kandidaten.append((pfad, os.path.basename(pfad.rstrip('/'))))
    for unterordner, anzeige in (('VMs', T['anzeige_vms']),
                                 ('.local/share/Steam', T['anzeige_steam'])):
        pfad = os.path.join(home, unterordner)
        if os.path.isdir(pfad):
            kandidaten.append((pfad, anzeige))
    # Flatpak: die GROSSEN Programme liegen systemweit in /var/lib/flatpak (mehrere
    # GB, NICHT im Home) — genau die soll man weglassen koennen (ehrliches Kaestchen).
    if os.path.isdir('/var/lib/flatpak'):
        kandidaten.append(('/var/lib/flatpak', T['anzeige_flatpak']))
    return kandidaten

# ======================= Ersteinrichtung =======================

BAU_PAKETE = ('calamares live-boot live-config-systemd live-boot-initramfs-tools '
              'xorriso isolinux syslinux-common squashfs-tools grub-efi-amd64-bin '
              'grub-pc-bin dosfstools rsync '
              # Secure Boot: fertig signierte Bausteine (Microsoft/Canonical) + mtools fuers EFI-Image
              'shim-signed grub-efi-amd64-signed mtools')

# ---- Secure-Boot-Bausteine (fertig signiert von Microsoft/Canonical) ----
# Microsoft-signierter shim (Erststarter), Canonical-signierter GRUB, MokManager.
SHIM_SIGNED = '/usr/lib/shim/shimx64.efi.signed.latest'
SHIM_SIGNED_ALT = '/usr/lib/shim/shimx64.efi.signed'
GRUB_SIGNED = '/usr/lib/grub/x86_64-efi-signed/grubx64.efi.signed'
MOKMANAGER = '/usr/lib/shim/mmx64.efi'
ISOHDPFX = '/usr/lib/ISOLINUX/isohdpfx.bin'
# GUID des EFI-System-Partition-Typs (fuer die echte ESP in der ISO)
ESP_TYP_GUID = 'C12A7328-F81F-11D2-BA4B-00A0C93EC93B'

def _system_app_version():
    try:
        for zeile in open(os.path.join(SYSTEM_ORDNER, 'linux-mint-snapshot.py')):
            m = re.match(r'VERSION = "([^"]+)"', zeile)
            if m:
                return m.group(1)
    except OSError:
        pass
    return None

def fehlende_teile():
    fehlt = []
    if not shutil.which('refractasnapshot'):
        fehlt.append('refractasnapshot (SourceForge)')
    if not shutil.which('calamares'):
        fehlt.append('calamares')
    for prog, paket in (('mksquashfs', 'squashfs-tools'), ('xorriso', 'xorriso'),
                        ('rsync', 'rsync')):
        if not shutil.which(prog):
            fehlt.append(paket)
    if not os.path.isdir('/usr/lib/live/config'):
        fehlt.append('live-config')
    if not os.path.isdir('/usr/lib/grub/x86_64-efi'):
        fehlt.append('grub-efi-amd64-bin')
    if not (os.path.exists('/usr/lib/ISOLINUX/isolinux.bin')
            or os.path.exists('/usr/lib/syslinux/modules/bios/ldlinux.c32')):
        fehlt.append('isolinux')
    # Secure-Boot-Bausteine (damit die ISO auch mit eingeschaltetem Secure Boot startet)
    if not shutil.which('mformat'):
        fehlt.append('mtools')
    if not (os.path.exists(SHIM_SIGNED) or os.path.exists(SHIM_SIGNED_ALT)):
        fehlt.append('shim-signed')
    if not os.path.exists(GRUB_SIGNED):
        fehlt.append('grub-efi-amd64-signed')
    try:
        cala_aktuell = CALA_MARKER in open('/etc/calamares/settings.conf').read()
    except OSError:
        cala_aktuell = False
    if not cala_aktuell:
        fehlt.append('Calamares-Konfiguration (1:1-Klon)' if SPRACHE == 'de'
                     else 'Calamares configuration (1:1 clone)')
    for hook in ('0029-live-user-anlegen', '2000-installer-desktop-icon'):
        if not os.path.exists(f'/usr/lib/live/config/{hook}'):
            fehlt.append(f'Live-Baustein {hook}' if SPRACHE == 'de' else f'live component {hook}')
    if not os.path.exists('/etc/skel/Desktop/system-installieren.desktop'):
        fehlt.append('Installer-Schreibtisch-Symbol' if SPRACHE == 'de' else 'installer desktop icon')
    if _system_app_version() != VERSION:
        fehlt.append('App im System (/opt) — Teil jedes Schnappschusses' if SPRACHE == 'de'
                     else 'app inside the system (/opt) — part of every snapshot')
    return fehlt

def einricht_skript():
    """Bash-Skript fuer alles, was Root braucht (laeuft EINMAL ueber sudo/pkexec)."""
    ver = DISTRO.split()[-1] if DISTRO.split() else ''
    return f'''#!/bin/bash
# Ersteinrichtung Rikus Mintshot v{VERSION} — laeuft als root, Protokoll siehe App.
set -x
export DEBIAN_FRONTEND=noninteractive
FEHLER=0

# update-Fehler (z. B. cdrom-Quelle im Live-System) nicht als Scheitern werten
apt-get update || true
apt-get install -y {BAU_PAKETE} || FEHLER=1

if ! command -v refractasnapshot >/dev/null; then
  T=$(mktemp -d)
  if wget -q -O "$T/refractasnapshot-base.deb" "{REFRACTA_DEB_URL}"; then
    dpkg -i "$T/refractasnapshot-base.deb" || apt-get -f install -y || FEHLER=1
  else
    echo "DOWNLOAD-FEHLER refractasnapshot"; FEHLER=1
  fi
  rm -rf "$T"
fi
dpkg --configure -a || true
# Falls das Paket seine Konfigurationsdatei nicht anlegen konnte: Vorlage einspielen
[ -f /etc/refractasnapshot.conf ] || cp "{DATEN}/refractasnapshot.conf.vorlage" /etc/refractasnapshot.conf || FEHLER=1

# Calamares-Konfiguration (bewiesene 1:1-Klon-Vorlagen aus dem App-Paket)
rm -rf /etc/calamares
mkdir -p /etc/calamares
cp -r "{DATEN}/calamares/." /etc/calamares/
B=/etc/calamares/branding/linuxmint/branding.desc
[ -n "{ver}" ] && sed -i 's/22\\.3/{ver}/g' "$B"

# Live-Bausteine (Schreibtisch-Symbol; 0029 ist beim Klon-Modell untaetig, bleibt als Reserve)
install -m 0755 "{DATEN}/live-hooks/0029-live-user-anlegen" /usr/lib/live/config/
install -m 0755 "{DATEN}/live-hooks/2000-installer-desktop-icon" /usr/lib/live/config/
mkdir -p /etc/skel/Desktop
install -m 0755 "{DATEN}/desktop/system-installieren.desktop" /etc/skel/Desktop/

# Calamares aus dem normalen Menue verstecken (Symbol auf dem Live-Schreibtisch ist der Weg)
if [ -f /usr/share/applications/calamares.desktop ]; then
  mkdir -p /usr/local/share/applications
  cp /usr/share/applications/calamares.desktop /usr/local/share/applications/calamares.desktop
  grep -q '^NoDisplay=true' /usr/local/share/applications/calamares.desktop || \
    echo 'NoDisplay=true' >> /usr/local/share/applications/calamares.desktop
fi

# App fest ins System einbauen (/opt) — dadurch steckt sie in jedem Schnappschuss
if [ "{APP_ORDNER}" != "{SYSTEM_ORDNER}" ]; then
  mkdir -p "{SYSTEM_ORDNER}"
  cp -r "{APP_ORDNER}/." "{SYSTEM_ORDNER}/"
  rm -rf "{SYSTEM_ORDNER}/__pycache__"
fi
chmod 0755 "{SYSTEM_ORDNER}/linux-mint-snapshot.py"
cat > /usr/share/applications/linux-mint-snapshot.desktop <<'MENUE'
[Desktop Entry]
Type=Application
Name=Rikus Mintshot
Comment=1:1 clone of your system as a bootable ISO / 1:1-Klon deines Systems als startfähige ISO
Comment[de]=1:1-Klon deines Linux-Mint-Systems als startfähige ISO — mit einem Klick
Exec=python3 {SYSTEM_ORDNER}/linux-mint-snapshot.py
Icon={SYSTEM_ORDNER}/daten/icon.png
Terminal=false
Categories=System;Utility;
Keywords=snapshot;iso;backup;live;usb;clone;sicherung;abbild;klon;
MENUE

mkdir -p {ISO_ORDNER}
chown {getpass.getuser()} {ISO_ORDNER} 2>/dev/null

exit $FEHLER
'''

# Klon-Modell: NUR echte Bremsen und Fallen bleiben draussen — alles andere ist 1:1.
KLON_AUSSCHLUESSE = '''
# Rikus Mintshot (Klon): nur Bremsen/Fallen ausschliessen, Rest bleibt 1:1
- /timeshift/*
- /timeshift-btrfs/*
- /swapfile
- /home/*/.cache/*
- /home/*/.local/share/Trash/*
- /home/*/mnt/*
- /home/*/.gvfs
- /root/.cache/*
'''

def _shim_pfad():
    return SHIM_SIGNED if os.path.exists(SHIM_SIGNED) else SHIM_SIGNED_ALT

def secure_boot_moeglich():
    """Sind die fertig signierten Bausteine + Werkzeuge da, um eine Secure-Boot-faehige
    ISO zu bauen? (shim-signed = Microsoft, grub-efi-amd64-signed = Canonical, mtools.)"""
    return (os.path.exists(_shim_pfad()) and os.path.exists(GRUB_SIGNED)
            and os.path.exists(ISOHDPFX) and shutil.which('mformat') is not None)

def secure_boot_nachbau_bash():
    """Bash-Schnipsel (laeuft als root DIREKT nach refractasnapshot): ersetzt das
    selbstgebaute, UNSIGNIERTE EFI durch die fertig signierte Kette
    shim -> GRUB -> (Mint-)Kernel und packt die ISO mit einer echten EFI-System-
    Partition neu. Ergebnis bootet auch mit eingeschaltetem Secure Boot.
    Ist idempotent + selbstsichernd: fehlt etwas, bleibt die normale ISO unveraendert."""
    shim = _shim_pfad()
    return f'''
# ===== Secure-Boot-Nachbau =====
SB_WORK="/home/work"; SB_ISOROOT="$SB_WORK/iso"; SB_SNAP="{ISO_ORDNER}"
SB_SHIM="{shim}"; SB_GRUB="{GRUB_SIGNED}"; SB_MM="{MOKMANAGER}"; SB_PFX="{ISOHDPFX}"
if [ -d "$SB_ISOROOT/isolinux" ] && [ -f "$SB_SHIM" ] && [ -f "$SB_GRUB" ] && command -v mformat >/dev/null; then
  SB_ISO="$(ls -t "$SB_SNAP"/*.iso 2>/dev/null | head -1)"
  if [ -n "$SB_ISO" ]; then
    echo "Schritt 4: Secure-Boot-faehig machen ..."
    SB_VOL="$(blkid -o value -s LABEL "$SB_ISO" 2>/dev/null)"; [ -n "$SB_VOL" ] || SB_VOL="LinuxMintSnapshot"
    SB_FWD="$(mktemp)"
    printf 'search --no-floppy --set=root --file /isolinux/isolinux.cfg\\nset prefix=($root)/boot/grub\\nconfigfile $prefix/grub.cfg\\n' > "$SB_FWD"
    SB_EFI="$SB_ISOROOT/boot/grub/efiboot.img"
    rm -f "$SB_EFI"
    dd if=/dev/zero of="$SB_EFI" bs=1M count=40 status=none
    mformat -i "$SB_EFI" -F ::
    mmd -i "$SB_EFI" ::/EFI ::/EFI/BOOT ::/EFI/ubuntu
    mcopy -i "$SB_EFI" "$SB_SHIM" ::/EFI/BOOT/BOOTX64.EFI
    mcopy -i "$SB_EFI" "$SB_GRUB" ::/EFI/BOOT/grubx64.efi
    [ -f "$SB_MM" ] && mcopy -i "$SB_EFI" "$SB_MM" ::/EFI/BOOT/mmx64.efi
    mcopy -i "$SB_EFI" "$SB_FWD" ::/EFI/ubuntu/grub.cfg
    mkdir -p "$SB_ISOROOT/EFI/BOOT" "$SB_ISOROOT/EFI/ubuntu"
    cp "$SB_SHIM" "$SB_ISOROOT/EFI/BOOT/BOOTX64.EFI"
    cp "$SB_GRUB" "$SB_ISOROOT/EFI/BOOT/grubx64.efi"
    [ -f "$SB_MM" ] && cp "$SB_MM" "$SB_ISOROOT/EFI/BOOT/mmx64.efi"
    cp "$SB_FWD" "$SB_ISOROOT/EFI/ubuntu/grub.cfg"
    rm -f "$SB_FWD" "$SB_ISOROOT/efi/boot/bootx64.efi"
    if xorriso -as mkisofs -r -J -joliet-long -l -iso-level 3 \\
        -isohybrid-mbr "$SB_PFX" -partition_offset 16 -V "$SB_VOL" \\
        -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table \\
        -eltorito-alt-boot -e '--interval:appended_partition_2:all::' -no-emul-boot \\
        -append_partition 2 {ESP_TYP_GUID} "$SB_EFI" -appended_part_as_gpt \\
        -o "$SB_ISO.sb" "$SB_ISOROOT"; then
      mv -f "$SB_ISO.sb" "$SB_ISO"
      sha256sum "$SB_ISO" > "$SB_ISO.sha256"
      echo "Secure-Boot-ISO fertig: $(basename "$SB_ISO")"
    else
      echo "Secure-Boot-Nachbau fehlgeschlagen - normale ISO bleibt erhalten."
      rm -f "$SB_ISO.sb"
    fi
  fi
fi
rm -rf "$SB_WORK" 2>/dev/null || true
echo "All finished!"
'''

def konfig_anlegen(weglassen=None, mit_home=True):
    """Klon-Konfiguration frisch schreiben (kein Root noetig). weglassen = Liste
    absoluter Ordner-Pfade, deren INHALT draussen bleibt (Haekchen).
    mit_home=False -> das ganze /home bleibt draussen (schlanke 'Nur System'-ISO)."""
    os.makedirs(KONFIG_ORDNER, exist_ok=True)
    basis_conf = '/etc/refractasnapshot.conf'
    basis_liste = '/usr/lib/refractasnapshot/snapshot_exclude.list'
    if not os.path.exists(basis_conf):
        # Paket nur halb konfiguriert (z. B. Live-System mit cdrom-Quelle):
        # mitgelieferte Vorlage nutzen — die eigenen Werte werden eh ersetzt.
        basis_conf = os.path.join(DATEN, 'refractasnapshot.conf.vorlage')
        if not os.path.exists(basis_conf):
            return False
    try:
        basis = open(basis_conf).read()
    except OSError:
        return False

    # Ausschluss-Liste: Basis-Liste OHNE deren /home-Regeln (wir regeln das Home
    # selbst, siehe unten) + eigene Bremsen-Liste + die abgewaehlten dicken Ordner.
    zeilen = []
    if os.path.exists(basis_liste):
        for zeile in open(basis_liste):
            if zeile.strip().startswith('- /home'):
                continue
            zeilen.append(zeile.rstrip('\n'))
    liste = "\n".join(zeilen) + KLON_AUSSCHLUESSE
    if not mit_home:
        # "Ohne Homeordner": persoenliche Daten bleiben KOMPLETT draussen -> schlanke
        # ISO. Der Live-Nutzer bekommt ohnehin ein frisches Home (live-config).
        liste += "\n# Ohne Homeordner gewaehlt: alle persoenlichen Ordner ausschliessen\n- /home/*\n"
    if weglassen:
        liste += "\n# Vom Nutzer abgewaehlte grosse Ordner (Haekchen in der App):\n"
        for pfad in weglassen:
            if '\n' in pfad or '\r' in pfad:        # Zeilenumbruch im Namen wuerde Filterzeilen injizieren
                continue
            # rsync-Glob-Metazeichen woertlich nehmen (ein Ordner "[x]" waere sonst eine Zeichenklasse)
            sicher = re.sub(r'([\[\]*?])', r'\\\1', pfad)
            liste += f"- {sicher}/*\n"
    liste_pfad = os.path.join(KONFIG_ORDNER, 'klon.list')
    with open(liste_pfad, 'w') as f:
        f.write(liste)

    conf_pfad = os.path.join(KONFIG_ORDNER, 'klon.conf')
    text = basis
    ersetzungen = {
        'snapshot_excludes': f'"{liste_pfad}"',
        'snapshot_basename': f'"{DISTRO_KURZ}-Klon"',
        'snapshot_dir': f'"{ISO_ORDNER}"',           # ISO landet DORT, wo die App sie sucht
        'kernel_image': f'"{KONFIG_ORDNER}/vmlinuz"',
        'initrd_image': f'"{KONFIG_ORDNER}/initrd.img"',
        'make_sha256sum': '"yes"',
        # Kritische Schluessel ERZWINGEN -> keine Extra-Prompts (Pipe-Input begrenzt) + keine Haenger,
        # egal was in einer vorhandenen /etc/refractasnapshot.conf steht:
        'limit_cpu': '"no"',
        'edit_boot_menu': '"no"',
        'initrd_crypt': '""',
        'make_efi': '"yes"',
        # Arbeitsordner behalten: der Secure-Boot-Nachbau packt die ISO daraus neu.
        'save_work': '"yes"' if secure_boot_moeglich() else '"no"',
    }
    for schluessel, wert in ersetzungen.items():
        muster = re.compile(rf'^#?\s*{schluessel}=.*$', re.MULTILINE)
        if muster.search(text):
            text = muster.sub(f'{schluessel}={wert}', text, count=1)
        else:
            text += f'\n{schluessel}={wert}\n'
    with open(conf_pfad, 'w') as f:
        f.write(text)

    # Aufraeumen: Konfigurationssaetze des alten Zwitter-Modells (v4) entfernen
    for alt in ('ohne-home', 'mit-home'):
        for endung in ('.conf', '.list'):
            pfad = os.path.join(KONFIG_ORDNER, alt + endung)
            if os.path.exists(pfad):
                os.remove(pfad)
    return True

def menue_eintrag_anlegen():
    """Bruecke fuer den allerersten Start aus dem Home-Ordner: Nutzer-Menueeintrag,
    bis die Einrichtung den systemweiten Eintrag (/usr/share) anlegt — danach
    raeumt sich die Bruecke selbst weg (kein Doppel im Startmenue)."""
    nutzer_eintrag = os.path.expanduser('~/.local/share/applications/linux-mint-snapshot.desktop')
    if os.path.exists('/usr/share/applications/linux-mint-snapshot.desktop'):
        if os.path.exists(nutzer_eintrag):
            try:
                os.remove(nutzer_eintrag)
            except OSError:
                pass
        return
    exec_zeile = f'Exec=python3 "{os.path.join(APP_ORDNER, "linux-mint-snapshot.py")}"'
    inhalt = f"""[Desktop Entry]
Type=Application
Name=Rikus Mintshot
Comment=1:1 clone of your system as a bootable ISO / 1:1-Klon deines Systems als startfähige ISO
Comment[de]=1:1-Klon deines Linux-Mint-Systems als startfähige ISO — mit einem Klick
{exec_zeile}
Icon={os.path.join(DATEN, "icon.png")}
Terminal=false
Categories=System;Utility;
Keywords=snapshot;iso;backup;live;usb;clone;sicherung;abbild;klon;
"""
    try:
        alt = open(nutzer_eintrag).read() if os.path.exists(nutzer_eintrag) else ''
        if exec_zeile not in alt:
            os.makedirs(os.path.dirname(nutzer_eintrag), exist_ok=True)
            with open(nutzer_eintrag, 'w') as f:
                f.write(inhalt)
    except OSError:
        pass

def boot_vorlagen_fuellen():
    """Boot-Menue-Vorlagen in der Sprache DES NUTZERS erzeugen (im Konfig-Ordner);
    der Bau-Befehl kopiert sie mit Root-Rechten an die Refracta-Pfade."""
    # ${DISTRO} in den Vorlagen ersetzt REFRACTA selbst beim Bau (Name kommt via stdin);
    # hier nur die eigenen {PLATZHALTER} fuellen.
    werte = {'{SPRACHNAME}': sprach_anzeige(), '{LOCALE}': nutzer_locale(),
             '{KEYBOARD}': nutzer_tastatur(), '{TIMEZONE}': nutzer_zeitzone(),
             '{LIVEUSER}': LIVE_USER}
    ergebnis = []
    for vorlage, ziel in (('grub.cfg.template.in', 'grub.cfg.template'),
                          ('live.cfg.in', 'live.cfg')):
        text = open(os.path.join(DATEN, 'boot-vorlagen', vorlage)).read()
        for platzhalter, wert in werte.items():
            text = text.replace(platzhalter, wert)
        ziel_pfad = os.path.join(KONFIG_ORDNER, ziel)
        with open(ziel_pfad, 'w') as f:
            f.write(text)
        ergebnis.append(ziel_pfad)
    return ergebnis

# ======================= Fenster =======================

class SnapshotApp(Gtk.Window):

    def __init__(self, selbsttest=False):
        super().__init__(title="Rikus Mintshot")
        self.set_default_size(760, 700)
        self.set_border_width(14)
        self.icon_pfad = os.path.join(DATEN, 'icon.png')
        if os.path.exists(self.icon_pfad):
            self.set_icon_from_file(self.icon_pfad)

        self.selbsttest = selbsttest
        self.iso_ordner = os.environ.get('MINT_SNAP_TESTORDNER', ISO_ORDNER) \
            if selbsttest else ISO_ORDNER
        self.root = root_praefix()
        self.bau_pid = None
        self.lauf_aktiv = False
        self.bau_startzeit = None
        self._log_pos = 0
        self._log_rest = b''
        self._bau_phase = 1
        self._phase_merker = ("", -1)
        self._schritte_gesehen = set()

        # Ganzen Inhalt scrollbar machen, damit auf kleinen/HiDPI-Bildschirmen
        # auch die unteren Knoepfe (USB schreiben) immer erreichbar bleiben.
        scroll_aussen = Gtk.ScrolledWindow()
        scroll_aussen.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        # Feste (nicht ueberlagernde) Scrollleiste: sonst legt sich die aeussere
        # Overlay-Leiste ueber die innere von "Technische Einzelheiten" -> sieht aus
        # wie 2 sich ueberschneidende Schieberegler.
        scroll_aussen.set_overlay_scrolling(False)
        self.add(scroll_aussen)
        haupt = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        scroll_aussen.add(haupt)

        titel_zeile = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        titel = Gtk.Label()
        titel.set_markup("<span size='x-large' weight='bold'>📸 Rikus Mintshot</span>\n"
                         f"<span size='small'>{GLib.markup_escape_text(T['untertitel'])}</span>\n"
                         f"<span size='small' style='italic'>{GLib.markup_escape_text(T['herausgeber'].format(v=VERSION))}</span>")
        titel.set_justify(Gtk.Justification.CENTER)
        titel.set_hexpand(True)
        titel_zeile.pack_start(titel, True, True, 0)
        self.knopf_ueber = Gtk.Button(label=T['knopf_ueber'])
        self.knopf_ueber.set_valign(Gtk.Align.START)
        self.knopf_ueber.connect('clicked', self.ueber_zeigen)
        titel_zeile.pack_start(self.knopf_ueber, False, False, 0)
        haupt.pack_start(titel_zeile, False, False, 0)

        self.info_label = Gtk.Label()
        haupt.pack_start(self.info_label, False, False, 0)

        rahmen = Gtk.Frame(label=T['frame_auswahl'])
        box_wahl = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box_wahl.set_border_width(10)
        rahmen.add(box_wahl)

        lbl_klon = Gtk.Label()
        lbl_klon.set_markup(f"<b>{GLib.markup_escape_text(T['klon_info'])}</b>")
        lbl_klon.set_halign(Gtk.Align.START)
        box_wahl.pack_start(lbl_klon, False, False, 0)

        # Home-Wahl: ohne Homeordner (schlank, Standard) ODER mit Homeordner (1:1-Klon)
        self.rb_ohne_home = Gtk.RadioButton.new_with_label_from_widget(None, T['home_ohne'])
        self.rb_mit_home = Gtk.RadioButton.new_with_label_from_widget(self.rb_ohne_home, T['home_mit'])
        self.rb_ohne_home.set_active(True)   # Standard: schlank, ohne persoenliche Daten
        box_wahl.pack_start(self.rb_ohne_home, False, False, 0)
        box_wahl.pack_start(self.rb_mit_home, False, False, 0)

        # "Fuer Fortgeschrittene": Einzel-Ordner-Haekchen in einen ausklappbaren
        # Bereich, standardmaessig ZUGEKLAPPT -> Neulinge sehen nur die 2 Knoepfe oben.
        exp_fort = Gtk.Expander(label=T['fortgeschritten_titel'])
        exp_fort.set_expanded(False)
        box_fort = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        exp_fort.add(box_fort)
        lbl_weg = Gtk.Label(label=T['weglassen_titel'])
        lbl_weg.set_halign(Gtk.Align.START)
        box_fort.pack_start(lbl_weg, False, False, 4)

        gemerkt = []
        try:
            gemerkt = json.load(open(WEGLASSEN_DATEI))
        except (OSError, ValueError):
            pass
        self.haekchen = {}      # pfad -> CheckButton
        self._anzeigen = {}     # pfad -> Anzeigename
        self.gitter = Gtk.FlowBox()
        self.gitter.set_selection_mode(Gtk.SelectionMode.NONE)
        self.gitter.set_max_children_per_line(2)
        self.gitter.set_min_children_per_line(2)
        # feste grosse Ordner (XDG + VMs/Steam/Flatpak)
        for pfad, anzeige in dicke_ordner():
            self._check_hinzu(pfad, anzeige, pfad in gemerkt)
        # frueher frei hinzugefuegte Ordner (persistiert in ZUSATZ_DATEI)
        try:
            for pfad in json.load(open(ZUSATZ_DATEI)):
                if os.path.isdir(pfad):
                    self._check_hinzu(pfad, self._kurzname(pfad), pfad in gemerkt)
        except (OSError, ValueError):
            pass
        box_fort.pack_start(self.gitter, False, False, 0)
        # Knopf: beliebigen weiteren Ordner weglassen (wie MX Snapshot)
        knopf_ordner = Gtk.Button(label=T['zusatz_knopf'])
        knopf_ordner.set_halign(Gtk.Align.START)
        knopf_ordner.connect('clicked', self.ordner_waehlen)
        box_fort.pack_start(knopf_ordner, False, False, 2)
        box_wahl.pack_start(exp_fort, False, False, 6)

        lbl_privat = Gtk.Label()
        lbl_privat.set_markup(f"<span size='small' foreground='#a05050'>{GLib.markup_escape_text(T['privat_hinweis'])}</span>")
        lbl_privat.set_halign(Gtk.Align.START)
        box_wahl.pack_start(lbl_privat, False, False, 4)
        haupt.pack_start(rahmen, False, False, 0)

        zeile_start = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.knopf_bauen = Gtk.Button(label=T['knopf_bauen'])
        self.knopf_bauen.get_style_context().add_class('suggested-action')
        self.knopf_bauen.connect('clicked', self.bauen_geklickt)
        self.knopf_abbruch = Gtk.Button(label=T['knopf_abbruch'])
        self.knopf_abbruch.set_sensitive(False)
        self.knopf_abbruch.connect('clicked', self.abbrechen_geklickt)
        self.knopf_einrichten = Gtk.Button(label=T['einr_knopf'])
        self.knopf_einrichten.connect('clicked', self.einrichten_geklickt)
        self.knopf_einrichten.set_no_show_all(True)
        zeile_start.pack_start(self.knopf_bauen, True, False, 0)
        zeile_start.pack_start(self.knopf_einrichten, False, False, 0)
        zeile_start.pack_start(self.knopf_abbruch, False, False, 0)
        haupt.pack_start(zeile_start, False, False, 0)

        self.phase_label = Gtk.Label(label=T['bereit'])
        self.phase_label.set_halign(Gtk.Align.START)
        haupt.pack_start(self.phase_label, False, False, 0)

        self.balken = Gtk.ProgressBar()
        self.balken.set_show_text(True)
        haupt.pack_start(self.balken, False, False, 0)

        self.details_puffer = Gtk.TextBuffer()
        details_ansicht = Gtk.TextView(buffer=self.details_puffer)
        details_ansicht.set_editable(False)
        details_ansicht.set_monospace(True)
        details_ansicht.override_font(Pango.FontDescription('Monospace 8'))
        scroll_d = Gtk.ScrolledWindow()
        scroll_d.set_min_content_height(140)
        scroll_d.add(details_ansicht)
        expander = Gtk.Expander(label=T['details'])
        expander.add(scroll_d)
        haupt.pack_start(expander, False, False, 0)
        self.details_ansicht = details_ansicht

        rahmen_liste = Gtk.Frame(label=T['frame_liste'])
        box_liste = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box_liste.set_border_width(8)
        rahmen_liste.add(box_liste)
        self.store = Gtk.ListStore(str, str, str, str)
        self.liste = Gtk.TreeView(model=self.store)
        for i, spalte in enumerate((T['spalte_datei'], T['spalte_groesse'], T['spalte_erstellt'])):
            self.liste.append_column(Gtk.TreeViewColumn(spalte, Gtk.CellRendererText(), text=i))
        scroll_l = Gtk.ScrolledWindow()
        scroll_l.set_min_content_height(100)
        scroll_l.add(self.liste)
        box_liste.pack_start(scroll_l, True, True, 0)
        zeile = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.knopf_stick = Gtk.Button(label=T['knopf_stick'])
        self.knopf_stick.connect('clicked', self.stick_schreiben)
        self.knopf_pruef = Gtk.Button(label=T['knopf_pruef'])
        self.knopf_pruef.connect('clicked', self.stick_pruefen)
        self.knopf_loesch = Gtk.Button(label=T['knopf_loesch'])
        self.knopf_loesch.connect('clicked', self.iso_loeschen)
        for k in (self.knopf_stick, self.knopf_pruef, self.knopf_loesch):
            zeile.pack_start(k, False, False, 0)
        box_liste.pack_start(zeile, False, False, 0)
        haupt.pack_start(rahmen_liste, False, False, 0)

        if not self.selbsttest:
            menue_eintrag_anlegen()
        self.liste_aktualisieren()
        self._laufenden_bau_adoptieren()
        self._einrichtung_pruefen()
        if self.haekchen:
            threading.Thread(target=self._groessen_ermitteln, daemon=True).start()

        if self.selbsttest:
            GLib.timeout_add(1200, self._selbsttest_start)

    # ================= Hilfen =================

    def _freier_platz(self):
        # den Platz DORT messen, wo die ISO hinkommt (bei getrenntem /home wichtig)
        ziel = self.iso_ordner if os.path.isdir(self.iso_ordner) else '/'
        st = os.statvfs(ziel)
        return groesse_lesbar(st.f_bavail * st.f_frsize)

    def _eine_groesse(self, pfad):
        cb = self.haekchen.get(pfad)
        if cb is None:
            return
        try:
            out = subprocess.run(['du', '-sb', pfad], capture_output=True,
                                 text=True, timeout=300).stdout
            groesse = groesse_lesbar(int(out.split()[0]))
        except Exception:
            groesse = '?'
        GLib.idle_add(cb.set_label, f"{self._anzeigen[pfad]}  ({groesse})")

    def _groessen_ermitteln(self):
        for pfad in list(self.haekchen.keys()):
            self._eine_groesse(pfad)

    def _kurzname(self, pfad):
        home = os.path.expanduser('~')
        pfad = pfad.rstrip('/')
        return '~' + pfad[len(home):] if pfad.startswith(home) else pfad

    def _check_hinzu(self, pfad, anzeige, aktiv, sofort_messen=False):
        """Einen Ordner als Weglassen-Haekchen einhaengen (feste ODER frei gewaehlte)."""
        if pfad in self.haekchen:
            return False
        cb = Gtk.CheckButton(label=f"{anzeige}  ({T['groesse_offen']})")
        cb.set_active(aktiv)
        self.haekchen[pfad] = cb
        self._anzeigen[pfad] = anzeige
        self.gitter.add(cb)
        cb.show()
        if sofort_messen:
            threading.Thread(target=self._eine_groesse, args=(pfad,), daemon=True).start()
        return True

    def _zusatz_speichern(self):
        """Nur die frei hinzugefuegten Ordner (nicht die festen) merken."""
        feste = {p for p, _ in dicke_ordner()}
        zusatz = [p for p in self.haekchen if p not in feste]
        try:
            os.makedirs(KONFIG_ORDNER, exist_ok=True)
            with open(ZUSATZ_DATEI, 'w') as f:
                json.dump(zusatz, f)
        except OSError:
            pass

    def ordner_waehlen(self, _knopf):
        d = Gtk.FileChooserDialog(title=T['zusatz_titel'], transient_for=self,
                                  action=Gtk.FileChooserAction.SELECT_FOLDER)
        d.add_buttons(T['zusatz_abbr'], Gtk.ResponseType.CANCEL,
                      T['zusatz_add'], Gtk.ResponseType.OK)
        try:
            d.set_current_folder(os.path.expanduser('~'))
        except Exception:
            pass
        if d.run() == Gtk.ResponseType.OK:
            pfad = (d.get_filename() or '').rstrip('/')
            home = os.path.expanduser('~').rstrip('/')
            # Schutz: nur ECHTE Unterordner des eigenen Home — sonst waere der 1:1-Klon
            # leer (Home selbst gewaehlt) oder unbootbar (/etc, /usr, /boot ...).
            if not pfad or not os.path.isdir(pfad) or pfad == home or not pfad.startswith(home + '/'):
                self.melde(Gtk.MessageType.WARNING, T['zusatz_nurhome_titel'], T['zusatz_nurhome_text'])
            elif self._check_hinzu(pfad, self._kurzname(pfad), True, sofort_messen=True):
                self._zusatz_speichern()
        d.destroy()

    def setze_phase(self, text, anteil=None):
        prozent = int(anteil * 100) if anteil is not None else -1
        if (text, prozent) == self._phase_merker:
            return
        self._phase_merker = (text, prozent)
        s = SCHRITT_MUSTER.search(text)
        if s:
            self._schritte_gesehen.add(int(s.group(1)))
        def _tun():
            self.phase_label.set_markup(f"<b>{GLib.markup_escape_text(text)}</b>")
            if anteil is not None:
                self.balken.set_fraction(min(anteil, 1.0))
                self.balken.set_text(f"{prozent} %")
            return False
        GLib.idle_add(_tun)

    def melde(self, art, titel, text):
        if self.selbsttest:
            print(f"SELBSTTEST-DIALOG [{titel}]: {text.splitlines()[0] if text else ''}")
            return
        def _zeigen():
            d = Gtk.MessageDialog(transient_for=self, modal=True, message_type=art,
                                  buttons=Gtk.ButtonsType.OK, text=titel)
            d.format_secondary_text(text)
            d.run()
            d.destroy()
            return False
        GLib.idle_add(_zeigen)

    def ueber_zeigen(self, *_args):
        d = Gtk.AboutDialog(transient_for=self, modal=True)
        d.set_program_name("Rikus Mintshot")
        d.set_version(VERSION)
        d.set_comments(T['untertitel'])
        d.set_license_type(Gtk.License.GPL_3_0)
        d.set_authors(["Gilbert Rikus"])
        d.set_copyright("© Gilbert Rikus")
        if os.path.exists(self.icon_pfad):
            d.set_logo(GdkPixbuf.Pixbuf.new_from_file(self.icon_pfad))
        d.run()
        d.destroy()

    def gewaehlte_iso(self):
        model, it = self.liste.get_selection().get_selected()
        return model[it][3] if it else None

    def liste_aktualisieren(self):
        def _tun():
            self.store.clear()
            for pfad in sorted(glob.glob(os.path.join(self.iso_ordner, '*.iso')),
                               key=os.path.getmtime, reverse=True):
                st = os.stat(pfad)
                self.store.append([os.path.basename(pfad), groesse_lesbar(st.st_size),
                                   datetime.datetime.fromtimestamp(st.st_mtime).strftime('%d.%m.%Y %H:%M'),
                                   pfad])
            self.info_label.set_markup("<span size='small'>" + T['ablage'].format(
                ordner=self.iso_ordner, platz=self._freier_platz()) + "</span>")
            return False
        GLib.idle_add(_tun)

    def _puls(self):
        if self.lauf_aktiv and self.balken.get_fraction() == 0.0:
            self.balken.pulse()
        return self.lauf_aktiv

    def _details_anhaengen(self, text):
        def _tun():
            ende = self.details_puffer.get_end_iter()
            self.details_puffer.insert(ende, text)
            self.details_ansicht.scroll_mark_onscreen(self.details_puffer.get_insert())
            return False
        GLib.idle_add(_tun)

    # ================= Ersteinrichtung =================

    def _einrichtung_pruefen(self):
        if self.selbsttest:
            return
        self._fehlt = fehlende_teile()
        if self._fehlt:
            self.knopf_bauen.set_sensitive(False)
            self.knopf_einrichten.show()
            self.setze_phase(T['einr_hinweis_phase'])

    def einrichten_geklickt(self, _knopf):
        d = Gtk.MessageDialog(transient_for=self, modal=True,
                              message_type=Gtk.MessageType.QUESTION,
                              buttons=Gtk.ButtonsType.NONE,
                              text=T['einr_titel'])
        d.add_buttons(T['einr_spaeter'], Gtk.ResponseType.NO,
                      T['einr_knopf'], Gtk.ResponseType.YES)
        d.format_secondary_text(T['einr_text'].format(fehlt="\n".join("• " + f for f in self._fehlt)))
        antwort = d.run()
        d.destroy()
        if antwort != Gtk.ResponseType.YES:
            return
        skript_pfad = os.path.join(KONFIG_ORDNER, 'einrichtung.sh')
        os.makedirs(KONFIG_ORDNER, exist_ok=True)
        with open(skript_pfad, 'w') as f:
            f.write(einricht_skript())
        os.chmod(skript_pfad, 0o755)
        self.knopf_einrichten.set_sensitive(False)
        self.lauf_aktiv = True
        GLib.timeout_add(200, self._puls)
        self.setze_phase(T['einr_laeuft'])
        threading.Thread(target=self._einrichten_arbeit, args=(skript_pfad,), daemon=True).start()

    def _einrichten_arbeit(self, skript_pfad):
        with open(EINRICHT_LOG, 'w') as log:
            p = subprocess.Popen(self.root.split() + ['bash', skript_pfad],
                                 stdout=log, stderr=subprocess.STDOUT)
            p.wait()
        try:
            self._details_anhaengen(open(EINRICHT_LOG, errors='replace').read())
        except FileNotFoundError:
            pass
        self.lauf_aktiv = False
        # Es zaehlt der ENDZUSTAND, nicht der Skript-Rueckgabewert: apt/dpkg melden
        # im Live-Betrieb harmlose Zwischenfehler (cdrom-Quelle, deb-Nachinstallation).
        rest = fehlende_teile()
        if not rest:
            menue_eintrag_anlegen()  # Nutzer-Bruecke weg, systemweiter Eintrag steht
            self.melde(Gtk.MessageType.INFO, T['einr_fertig_titel'], T['einr_fertig_text'])
            def _frei():
                self.knopf_bauen.set_sensitive(True)
                self.knopf_einrichten.hide()
                self.setze_phase(T['bereit'])
                return False
            GLib.idle_add(_frei)
        else:
            self._fehlt = rest or ['?']
            self.melde(Gtk.MessageType.ERROR, T['einr_fehler_titel'],
                       T['einr_fehler_text'].format(log=EINRICHT_LOG))
            GLib.idle_add(lambda: (self.knopf_einrichten.set_sensitive(True), False)[1])

    # ================= ISO bauen =================

    def bauen_geklickt(self, _knopf):
        if self.lauf_aktiv:
            return
        self.root = root_praefix()   # JETZT bestimmen: ein sudo-Zeitstempel vom Start kann abgelaufen sein
        os.makedirs(self.iso_ordner, exist_ok=True)
        weglassen = [pfad for pfad, cb in self.haekchen.items() if cb.get_active()]
        try:
            os.makedirs(KONFIG_ORDNER, exist_ok=True)
            with open(WEGLASSEN_DATEI, 'w') as f:
                json.dump(weglassen, f)
        except OSError:
            pass
        if not self.selbsttest:
            mit_home = self.rb_mit_home.get_active()
            if not konfig_anlegen(weglassen, mit_home):
                self.melde(Gtk.MessageType.ERROR, T['konfig_fehlt'],
                           '/etc/refractasnapshot.conf')
                return
        conf = os.path.join(KONFIG_ORDNER, 'klon.conf')

        kern = os.uname().release
        for quelle, bruecke in ((f'/boot/vmlinuz-{kern}', 'vmlinuz'),
                                (f'/boot/initrd.img-{kern}', 'initrd.img')):
            if not os.path.exists(quelle):           # ohne Kernel/initrd baut refracta eine unbootbare ISO
                self.melde(Gtk.MessageType.ERROR, T['konfig_fehlt'], quelle)
                return
            ziel = os.path.join(KONFIG_ORDNER, bruecke)
            if os.path.islink(ziel) or os.path.exists(ziel):
                os.remove(ziel)
            os.symlink(quelle, ziel)

        if self.selbsttest:
            kern_befehl = FAKE_MOTOR
        else:
            grub_v, live_v = boot_vorlagen_fuellen()
            # EIN Root-Aufruf: Vorlagen einspielen + Motor starten (+ Secure-Boot-Nachbau)
            innen = (
                f'cp "{grub_v}" /usr/lib/refractasnapshot/grub.cfg.template && '
                f'cp "{live_v}" /usr/lib/refractasnapshot/iso/isolinux/live.cfg && '
                f'printf "1\\n{DISTRO}\\n" | refractasnapshot -c "{conf}"')
            if secure_boot_moeglich():
                # Nachbau in eine Datei schreiben (haelt Anfuehrungszeichen aus dem Aufruf raus)
                sb_skript = os.path.join(KONFIG_ORDNER, 'secure-boot-nachbau.sh')
                with open(sb_skript, 'w') as f:
                    f.write('#!/bin/bash\n' + secure_boot_nachbau_bash())
                innen += f' && bash "{sb_skript}"'  # nur bei ERFOLGREICHEM refracta-Bau
            kern_befehl = f"{self.root} bash -c '{innen}'"

        open(LOG_DATEI, 'w').close()
        prozess = subprocess.Popen(
            ['bash', '-c', f'{kern_befehl} >> "{LOG_DATEI}" 2>&1'],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, start_new_session=True)
        self.bau_pid = prozess.pid
        self._popen = prozess
        with open(PID_DATEI, 'w') as f:
            f.write(f"{prozess.pid} {datetime.datetime.now().isoformat()}")
        self._bau_anzeige_starten(datetime.datetime.now())

    def _laufenden_bau_adoptieren(self):
        try:
            with open(PID_DATEI) as f:
                teile = f.read().split()
            pid = int(teile[0])
            start = datetime.datetime.fromisoformat(teile[1])
        except (FileNotFoundError, ValueError, IndexError):
            return
        if os.path.exists(f'/proc/{pid}'):
            self.bau_pid = pid
            self._bau_anzeige_starten(start)
            self.setze_phase(T['lauf_gefunden'])
        else:
            os.remove(PID_DATEI)

    def _bau_anzeige_starten(self, startzeit):
        self.lauf_aktiv = True
        self.bau_startzeit = startzeit
        self._log_pos = 0
        self._log_rest = b''
        self._bau_phase = 1
        self._phase_merker = ("", -1)
        self.knopf_bauen.set_sensitive(False)
        self.knopf_abbruch.set_sensitive(True)
        for k in (self.knopf_stick, self.knopf_pruef, self.knopf_loesch):
            k.set_sensitive(False)   # waehrend des Baus keine Stick-Aktionen (teilt sich lauf_aktiv)
        self.details_puffer.set_text("")
        self.balken.set_fraction(0.0)
        self.balken.set_text("")
        GLib.timeout_add(200, self._puls)
        GLib.timeout_add(400, self._bau_tick)
        self.setze_phase(T['schritt1'])

    def _bau_tick(self):
        try:
            with open(LOG_DATEI, 'rb') as f:
                f.seek(self._log_pos)
                daten = f.read()
                self._log_pos = f.tell()
        except FileNotFoundError:
            daten = b''

        if daten:
            daten = self._log_rest + daten
            teile = re.split(rb'[\r\n]', daten)
            self._log_rest = teile.pop()
            zeilen = []
            for roh in teile:
                zeile = roh.decode('utf-8', 'replace').strip()
                if not zeile:
                    continue
                zeilen.append(zeile)
                klein = zeile.lower()
                if self._bau_phase < 2 and ('mksquashfs' in klein
                                            or 'creating 4.0 filesystem' in klein
                                            or 'squashing' in klein):
                    self._bau_phase = 2
                    self.setze_phase(T['schritt2'], 0.01)
                elif self._bau_phase < 3 and ('creating cd/dvd image' in klein
                                              or 'iso image produced' in klein):
                    self._bau_phase = 3
                    self.setze_phase(T['schritt3'], 0.90)
                elif self._bau_phase < 4 and 'secure-boot-f' in klein:
                    self._bau_phase = 4
                    self.setze_phase(T['schritt4'], 0.95)
                if self._bau_phase == 2 and ']' in zeile:
                    treffer = PROZENT_MUSTER.search(zeile)
                    if treffer:
                        self.setze_phase(T['schritt2'],
                                         0.01 + (int(treffer.group(1)) / 100) * 0.88)
            if zeilen:
                ende = self.details_puffer.get_end_iter()
                self.details_puffer.insert(ende, "\n".join(zeilen) + "\n")
                anzahl = self.details_puffer.get_line_count()
                if anzahl > 1500:
                    self.details_puffer.delete(self.details_puffer.get_start_iter(),
                                               self.details_puffer.get_iter_at_line(anzahl - 1500))
                self.details_puffer.place_cursor(self.details_puffer.get_end_iter())
                self.details_ansicht.scroll_mark_onscreen(self.details_puffer.get_insert())

        fertig = False
        if self.bau_pid:
            popen = getattr(self, '_popen', None)
            if popen is not None and popen.pid == self.bau_pid:
                fertig = popen.poll() is not None
            else:
                try:
                    with open(f'/proc/{self.bau_pid}/stat') as f:
                        zustand = f.read().rsplit(')', 1)[-1].split()[0]
                    fertig = (zustand == 'Z')
                except (FileNotFoundError, IndexError):
                    fertig = True
        if fertig:
            popen = getattr(self, '_popen', None)
            if popen is not None:
                popen.wait()
                self._popen = None
            self._lauf_fertig()
            return False
        return True

    def _lauf_fertig(self):
        self.lauf_aktiv = False
        self.bau_pid = None
        if os.path.exists(PID_DATEI):
            os.remove(PID_DATEI)
        self.knopf_bauen.set_sensitive(True)
        self.knopf_abbruch.set_sensitive(False)
        for k in (self.knopf_stick, self.knopf_pruef, self.knopf_loesch):
            k.set_sensitive(True)
        self.liste_aktualisieren()

        try:
            with open(LOG_DATEI, errors='replace') as f:
                erfolg_im_log = 'All finished!' in f.read()
        except FileNotFoundError:
            erfolg_im_log = False
        neue = [p for p in glob.glob(os.path.join(self.iso_ordner, '*.iso'))
                if self.bau_startzeit and datetime.datetime.fromtimestamp(
                    os.path.getmtime(p)) > self.bau_startzeit]

        if neue and erfolg_im_log:
            iso = max(neue, key=os.path.getmtime)
            self.balken.set_fraction(1.0)
            self.balken.set_text("100 %")
            self.setze_phase(T['fertig_phase'].format(iso=os.path.basename(iso)))
            self.melde(Gtk.MessageType.INFO, T['fertig_titel'],
                       T['fertig_text'].format(iso=os.path.basename(iso),
                                               groesse=groesse_lesbar(os.path.getsize(iso)),
                                               liveuser=LIVE_USER))
            ergebnis_ok = True
        else:
            self.balken.set_fraction(0.0)
            self.balken.set_text("")
            self.setze_phase(T['kein_abbild_phase'])
            self.melde(Gtk.MessageType.WARNING, T['kein_abbild_titel'], T['kein_abbild_text'])
            ergebnis_ok = False

        if self.selbsttest:
            schritte = ",".join(str(s) for s in sorted(self._schritte_gesehen))
            print(f"SELBSTTEST: sprache={SPRACHE} distro={DISTRO} liveuser={LIVE_USER} "
                  f"haekchen={len(self.haekchen)} schritte={schritte} "
                  f"ergebnis={'OK' if ergebnis_ok else 'FEHLER'}")
            GLib.timeout_add(500, Gtk.main_quit)
        return False

    def _selbsttest_start(self):
        print("SELBSTTEST: starte Bau-Klick")
        self.knopf_bauen.clicked()
        return False

    def abbrechen_geklickt(self, _knopf):
        if not self.lauf_aktiv:
            return
        d = Gtk.MessageDialog(transient_for=self, modal=True,
                              message_type=Gtk.MessageType.QUESTION,
                              buttons=Gtk.ButtonsType.YES_NO,
                              text=T['abbruch_titel'])
        d.format_secondary_text(T['abbruch_text'])
        antwort = d.run()
        d.destroy()
        if antwort != Gtk.ResponseType.YES:
            return
        # NUR den eigenen Bau beenden — NIE systemweit fremde Prozesse killen
        # (ein 'pkill -x rsync' wuerde z. B. ein laufendes Timeshift-Backup treffen).
        pid = self.bau_pid
        teile = []
        if pid:
            teile.append(f'kill -TERM -{pid} 2>/dev/null')  # eigene Bau-Prozessgruppe (sudo-Fall)
        # refractasnapshot ist app-eigen (laeuft nie ausserhalb) -> gezielt samt Bau-Kindern (pkexec-Fall)
        teile.append('for r in $(pgrep -f refractasnapshot 2>/dev/null); do kill -TERM -"$r" 2>/dev/null; done')
        teile.append('sleep 1')
        if pid:
            teile.append(f'kill -KILL -{pid} 2>/dev/null')
        teile.append('for r in $(pgrep -f refractasnapshot 2>/dev/null); do kill -KILL -"$r" 2>/dev/null; done')
        teile.append('rm -rf /home/work')
        subprocess.run(self.root.split() + ['bash', '-c', '; '.join(teile)], check=False)
        self.setze_phase(T['abgebrochen'])

    # ================= Stick =================

    def _stick_stromsparen_aus(self):
        try:
            subprocess.run(self.root.split() + ['bash', '-c', r'''
for D in /sys/block/*; do
  [ "$(cat $D/removable 2>/dev/null)" = "1" ] || continue
  U=$(readlink -f $D); while [ "$U" != "/" ] && [ ! -e "$U/idVendor" ]; do U=$(dirname $U); done
  [ -e "$U/idVendor" ] && echo on > $U/power/control
done'''], timeout=25, check=False)
        except Exception:
            pass

    def stick_schreiben(self, _knopf):
        iso = self.gewaehlte_iso()
        if not iso:
            self.melde(Gtk.MessageType.WARNING, T['erst_auswaehlen_titel'], T['auswahl_schreiben'])
            return
        self._stick_stromsparen_aus()
        try:
            subprocess.Popen(['mintstick', '-m', 'iso', '-i', iso])
        except Exception:
            try:
                subprocess.Popen(['mintstick', '-m', 'iso'])
            except Exception as fehler:
                self.melde(Gtk.MessageType.ERROR, "mintstick", str(fehler))

    def stick_pruefen(self, _knopf):
        iso = self.gewaehlte_iso()
        if not iso:
            self.melde(Gtk.MessageType.WARNING, T['erst_auswaehlen_titel'], T['auswahl_pruefen'])
            return
        self.setze_phase(T['pruef_laeuft'])
        self.balken.set_fraction(0.0)
        self.lauf_aktiv = True
        self._stick_stromsparen_aus()
        GLib.timeout_add(200, self._puls)
        threading.Thread(target=self._pruef_arbeit, args=(iso,), daemon=True).start()

    def _pruef_arbeit(self, iso):
        try:
            lsblk = subprocess.run(['lsblk', '-nd', '-o', 'NAME,TRAN,TYPE,MODEL'],
                                   capture_output=True, text=True).stdout
            sticks = [z.split(None, 3) for z in lsblk.splitlines()
                      if len(z.split()) >= 3 and z.split()[1] == 'usb' and z.split()[2] == 'disk']
            if not sticks:
                self.melde(Gtk.MessageType.ERROR, T['kein_stick_titel'], T['kein_stick_text'])
                return
            name = sticks[0][0]
            modell = sticks[0][3].strip() if len(sticks[0]) > 3 else ''
            geraet = f"/dev/{name}" + (f" ({modell})" if modell else "")
            geraet_pfad = f"/dev/{name}"
            groesse = os.path.getsize(iso)

            soll, werkzeug = None, 'sha256sum'
            for endung, wz in (('.sha256', 'sha256sum'), ('.md5', 'md5sum')):
                if os.path.exists(iso + endung):
                    with open(iso + endung) as f:
                        soll, werkzeug = f.read().split()[0], wz
                    break
            if soll is None:
                soll = subprocess.run(['bash', '-c', f'sha256sum "{iso}"'],
                                      capture_output=True, text=True).stdout.split()[0]

            ist = subprocess.run(
                self.root.split() + ['bash', '-c',
                                     f'head -c {groesse} {geraet_pfad} | {werkzeug}'],
                capture_output=True, text=True).stdout.split()[0]

            if ist == soll:
                self.melde(Gtk.MessageType.INFO, T['stick_ok_titel'],
                           T['stick_ok_text'].format(geraet=geraet,
                                                     iso=os.path.basename(iso)))
            else:
                self.melde(Gtk.MessageType.ERROR, T['stick_falsch_titel'],
                           T['stick_falsch_text'].format(geraet=geraet))
        except Exception as fehler:
            self.melde(Gtk.MessageType.ERROR, T['pruef_fehler'], str(fehler))
        finally:
            self.lauf_aktiv = False
            self.setze_phase(T['bereit_kurz'])

    # ================= Löschen =================

    def iso_loeschen(self, _knopf):
        iso = self.gewaehlte_iso()
        if not iso:
            self.melde(Gtk.MessageType.WARNING, T['erst_auswaehlen_titel'], T['auswahl_loeschen'])
            return
        d = Gtk.MessageDialog(transient_for=self, modal=True,
                              message_type=Gtk.MessageType.QUESTION,
                              buttons=Gtk.ButtonsType.YES_NO,
                              text=T['loesch_titel'].format(iso=os.path.basename(iso)))
        d.format_secondary_text(T['loesch_text'])
        antwort = d.run()
        d.destroy()
        if antwort == Gtk.ResponseType.YES:
            for pfad in (iso, iso + '.md5', iso + '.sha256', iso + '.log'):
                if os.path.exists(pfad):
                    os.remove(pfad)
            self.liste_aktualisieren()


if __name__ == '__main__':
    selbsttest = '--selbsttest' in sys.argv and (
        os.environ.get('MINT_SNAP_TEST') == '1' or os.environ.get('LM_SNAP_TEST') == '1')
    fenster = SnapshotApp(selbsttest=selbsttest)
    fenster.connect('destroy', Gtk.main_quit)
    fenster.show_all()
    if selbsttest:
        fenster.knopf_einrichten.hide()
    Gtk.main()
