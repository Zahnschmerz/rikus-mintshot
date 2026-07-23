#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Rikus Mintshot (v5.0) — 1:1 clone of the running system as a bootable live ISO.
# Published by / Herausgeber: Gilbert Rikus — License: GPL-3.0-or-later
#
# v5 = the "clone model" (Gilbert's product decision, 2026-07-07):
#   * The snapshot is a 1:1 CLONE: account, settings and saved logins ALWAYS included.
#     Big folders (Documents, Pictures, VMs ...) can be left out via checkboxes.
#   * The live stick boots STRAIGHT into the owner's own session (real user, autologin),
#     not into an artificial "mint" user.
#   * The installer (Calamares) does a 1:1 clone install: no user-creation page,
#     no locale/keyboard pages — it only prepares the target disk and the bootloader.
#   * The app itself lives in /opt/rikus-mintshot (installed by the assistant),
#     so it is part of every clone.
#   * Everything else proven in v4 stays: language table DE/EN, dynamic distro/user
#     values, sudo -n/pkexec, first-start assistant, crash-safe build engine.
#   * Self test: MINT_SNAP_TEST=1 ./rikus-mintshot.py --selbsttest

import os
import re
import sys
import glob
import json
import getpass
import shutil
import subprocess
import shlex
import threading
import datetime

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Pango, GdkPixbuf

VERSION = "7.2"
APP_ORDNER = os.path.dirname(os.path.abspath(__file__))
SYSTEM_ORDNER = '/opt/rikus-mintshot'
DATEN = os.path.join(APP_ORDNER, 'daten')
KONFIG_ORDNER = os.path.expanduser('~/.config/rikus-mintshot')
LOG_DATEI = os.path.join(KONFIG_ORDNER, 'letzter-lauf.log')
PID_DATEI = os.path.join(KONFIG_ORDNER, 'lauf.pid')
EINRICHT_LOG = os.path.join(KONFIG_ORDNER, 'einrichtung.log')
WEGLASSEN_DATEI = os.path.join(KONFIG_ORDNER, 'weglassen.json')
ZUSATZ_DATEI = os.path.join(KONFIG_ORDNER, 'zusatz-ordner.json')
ABLAGE_DATEI = os.path.join(KONFIG_ORDNER, 'ablageort.txt')
ABLAGE_STANDARD = '/home'                    # darunter entstehen snapshot/ und work/
ISO_ORDNER = os.path.join(ABLAGE_STANDARD, 'snapshot')   # Standard; per Ablageort aenderbar


def ablage_basis():
    """Gewaehlter Ablage-Basisordner (darunter snapshot/ + work/). Faellt auf /home
    zurueck, wenn nichts gespeichert ist oder der gemerkte Ort nicht mehr da ist."""
    try:
        with open(ABLAGE_DATEI) as f:
            ort = f.read().strip()
        if ort and os.path.isdir(ort):
            return ort
    except OSError:
        pass
    return ABLAGE_STANDARD


def ablage_ordner(basis=None):
    """(iso_ordner, work_ordner) fuer eine gegebene oder die gespeicherte Basis."""
    b = basis or ablage_basis()
    return os.path.join(b, 'snapshot'), os.path.join(b, 'work')


# ======================= Update-Hinweis =======================
# Das Programm wird als .deb ueber GitHub verteilt und hat KEINE apt-Quelle.
# "apt update" erfaehrt also nie davon, dass es eine neuere Fassung gibt - der
# Nutzer bleibt sitzen, ohne es zu merken. Belegt im eigenen Projekt: Hans-Josef
# Rausch testete v6.7 und meldete Fehler, als v6.8 laengst draussen war.
#
# Deshalb: eine unaufdringliche Zeile im Fenster. KEIN Popup, KEINE automatische
# Installation - nur ein Hinweis mit Link.
#
# Grundregeln, die hier nicht verhandelbar sind:
#   * Das Fenster darf NIE warten -> eigener Faden + hartes Zeitlimit.
#   * Es darf NIE abstuerzen -> schlaegt etwas fehl, bleibt die Zeile einfach weg.
#   * KEINE neue Abhaengigkeit -> urllib steckt in python3 (kein curl, kein requests).
#   * Abschaltbar -> wer nicht will, dass das Programm nach aussen telefoniert,
#     legt die Datei KEIN_UPDATE_DATEI an (steht in beiden Anleitungen).
UPDATE_API = 'https://api.github.com/repos/Zahnschmerz/rikus-mintshot/releases/latest'
UPDATE_SEITE = 'https://github.com/Zahnschmerz/rikus-mintshot/releases/latest'
KEIN_UPDATE_DATEI = os.path.join(KONFIG_ORDNER, 'kein-update-hinweis')
UPDATE_ZEITLIMIT = 4          # Sekunden; danach still aufgeben


def version_tupel(text):
    """'v6.10' -> (6, 10). Fuer den VERGLEICH von Versionen.

    ⚠️ Versionen NIEMALS als Text vergleichen: "6.10" < "6.9" ist als Text WAHR,
    der Hinweis bliebe ab 6.10 fuer immer aus. Zahlen vergleichen, nicht Buchstaben.
    """
    return tuple(int(t) for t in re.findall(r'\d+', text or '')) or (0,)


def neuere_version():
    """Fragt GitHub nach der neuesten Fassung. Rueckgabe: '6.11' oder None.

    None heisst schlicht "kein Hinweis anzeigen" - egal ob es keine neuere Fassung
    gibt, das Netz fehlt, GitHub bockt oder der Nutzer es abgeschaltet hat. Kein
    Internet ist der NORMALFALL, kein Fehler.
    """
    if os.path.exists(KEIN_UPDATE_DATEI):
        return None
    try:
        import urllib.request
        with urllib.request.urlopen(UPDATE_API, timeout=UPDATE_ZEITLIMIT) as antwort:
            tag = json.loads(antwort.read().decode('utf-8')).get('tag_name', '')
        neu = version_tupel(tag)
        if neu > version_tupel(VERSION):
            return tag.lstrip('vV') or tag
    except Exception:
        pass                  # bewusst ALLES abfangen: ein Hinweis darf nie stoeren
    return None
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
  'update_da': "🔔 Version {v} ist verfügbar",
  'update_link': "ansehen",
  'frame_auswahl': " Was kommt in den Schnappschuss? ",
  'klon_info': "Wähle, was in den Schnappschuss kommt:",
  'home_ohne': "Nur System (root) — ganz nackt, ohne persönliche Einstellungen",
  'home_einstellungen': "System + meine Einstellungen — schlank & brauchbar  (★ empfohlen)",
  'home_mit': "System + Home — alles komplett (deine Dateien, Mails & Konto)",
  'weglassen_titel': "Einzelne große Ordner weglassen? (Häkchen = bleibt draußen)",
  'fortgeschritten_titel': "⚙️  Für Fortgeschrittene: einzelne Ordner weglassen",
  'privat_hinweis': ("🔒 Der Stick enthält dein Konto und deine Zugänge —\n"
                     "sicher verwahren und nicht an Fremde weitergeben."),
  'groesse_offen': "wird gemessen …",
  'anzeige_vms': "Virtuelle Maschinen (VMs)",
  'vm_mitnehmen': "Virtuelle Maschinen mitnehmen — sie sind oft sehr groß (schnell 60 GB und mehr)",
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
  'knopf_persist': "💾 Persistenz einrichten",
  'knopf_loesch': "🗑️ Löschen",
  'ablage': "Ablageort: <b>{ordner}</b>   ·   Freier Platz: <b>{platz}</b>",
  'knopf_ablage': "📁 Ablageort ändern …",
  'ablage_tooltip': "Wähle, auf welcher Platte der Klon gebaut wird — z. B. eine zweite Festplatte mit mehr Platz.",
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
  'update_da': "🔔 Version {v} is available",
  'update_link': "view",
  'knopf_ueber': "ℹ️ About",
  'frame_auswahl': " What goes into the snapshot? ",
  'klon_info': "Choose what goes into the snapshot:",
  'home_ohne': "System (root) only — bare, without your settings",
  'home_einstellungen': "System + my settings — lean & ready to use  (★ recommended)",
  'home_mit': "System + Home — everything (your files, mail & account)",
  'weglassen_titel': "Leave out individual big folders? (checked = stays out)",
  'fortgeschritten_titel': "⚙️  Advanced: leave out individual folders",
  'privat_hinweis': ("🔒 The stick contains your account and credentials —\n"
                     "keep it in a safe place and never hand it to strangers."),
  'groesse_offen': "measuring …",
  'anzeige_vms': "Virtual machines (VMs)",
  'vm_mitnehmen': "Include virtual machines — they are often very large (60 GB and more)",
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
  'knopf_persist': "💾 Set up persistence",
  'knopf_loesch': "🗑️ Delete",
  'ablage': "Location: <b>{ordner}</b>   ·   Free space: <b>{platz}</b>",
  'knopf_ablage': "📁 Change location …",
  'ablage_tooltip': "Choose which drive the clone is built on — e.g. a second disk with more room.",
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

def vm_ordner():
    """Wo liegen virtuelle Maschinen? Sie sind fast immer der groesste Brocken im Klon.

    ⚠️ WICHTIG — sie liegen NICHT nur im Persoenlichen Ordner: QEMU/KVM (virt-manager) legt
    sie unter /var/lib/libvirt/images ab, also auf der SYSTEMPLATTE. Die drei Modi regeln aber
    nur den Persoenlichen Ordner ('ohne' haengt lediglich `- /home/*` an) -> VMs wandern in
    JEDEN Modus mit, auch in "Nur System". Am echten Geraet gemessen (18.07.2026):
        Nur System             89,4 GB  ->  ohne VM  29,4 GB   (VM-Anteil 60,0 GB)
        System + Einstellungen 96,0 GB  ->  ohne VM  36,0 GB   (VM-Anteil 60,0 GB)
    Deshalb bekommen sie eine eigene, gut sichtbare Zeile statt eines Haekchens im
    zugeklappten "Fuer Fortgeschrittene"-Bereich, das nie jemand aufmacht.

    VirtualBox nennt seinen Ordner "VirtualBox VMs" (MIT Leerzeichen) — frueher wurde nur
    "~/VMs" gesucht, weshalb VirtualBox-Nutzer nie eine Wahl hatten.
    Gibt die tatsaechlich vorhandenen Ordner zurueck (absolute Pfade, ohne Doppelte)."""
    home = os.path.expanduser('~')
    kandidaten = ['/var/lib/libvirt/images',                       # QEMU/KVM + virt-manager
                  os.path.join(home, 'VirtualBox VMs'),            # VirtualBox-Standard
                  os.path.join(home, 'VMs'),                       # haeufiger Eigenname
                  os.path.join(home, '.local/share/gnome-boxes/images')]   # GNOME Boxes
    try:                                                            # eigener VirtualBox-Ordner?
        m = re.search(r'defaultMachineFolder="([^"]*)"',
                      open(os.path.join(home, '.config/VirtualBox/VirtualBox.xml')).read())
        if m and m.group(1):
            kandidaten.append(m.group(1).replace('$HOME', home))
    except OSError:
        pass
    return [p for p in dict.fromkeys(kandidaten) if os.path.isdir(p)]


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
    # Virtuelle Maschinen stehen hier BEWUSST NICHT mehr: sie haben eine eigene, gut sichtbare
    # Zeile direkt bei der Modus-Wahl (siehe vm_ordner()) — sie kommen in JEDEM Modus mit und
    # sind meist der groesste Brocken. Zwei Bedienelemente fuer dieselbe Sache waeren verwirrend.
    for unterordner, anzeige in (('.local/share/Steam', T['anzeige_steam']),):
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
              'shim-signed grub-efi-amd64-signed mtools '
              # Start-Reihenfolge (Dualboot): efibootmgr setzt nach der Installation den eigenen
              # Firmware-Eintrag nach vorn, sonst startet der Rechner weiter Windows. Es MUSS im
              # Klon liegen (dort laeuft rikus-mintshot-bootorder). Auf den meisten Mint-Systemen
              # ist es zufaellig schon da -> auf dem eigenen PC faellt ein Fehlen NIE auf.
              'efibootmgr '
              # wget: holt in der Ersteinrichtung den Motor refractasnapshot von SourceForge
              # (siehe einricht_skript: `wget -q -O "$T/refractasnapshot-base.deb" ...`).
              # Stand 19.07.2026 gemessen: KEINES der uebrigen Pakete zieht wget nach. Auf Mint ist
              # es ab Werk da -> auf dem eigenen PC faellt das Fehlen NIE auf; auf einem schlanken
              # Debian bricht die Ersteinrichtung ab, bevor sie ueberhaupt anfaengt. Dieselbe Falle
              # wie bei efibootmgr am 17.07. -> deshalb hier UND in den Depends der .deb.
              'wget')

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
        for zeile in open(os.path.join(SYSTEM_ORDNER, 'rikus-mintshot.py')):
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
    if not os.path.exists('/usr/local/sbin/rikus-mintshot-home-fix'):
        fehlt.append('Home-Reparatur-Skript (Klon ohne Home)' if SPRACHE == 'de'
                     else 'home-repair script (clone without home)')
    if not os.path.exists('/usr/local/sbin/rikus-mintshot-netzfix'):
        fehlt.append('Netz-Portabilitaet (WLAN auf fremder Hardware)' if SPRACHE == 'de'
                     else 'network portability (WiFi on foreign hardware)')
    if not os.path.exists('/etc/systemd/system/rikus-mintshot-netzfix.service'):
        fehlt.append('Netz-Autostart (WLAN schon beim Live-Boot vom Stick)' if SPRACHE == 'de'
                     else 'network auto-start (WiFi already on live boot)')
    # Ohne diesen Dienst hat der Klon nach dem Wiederherstellen KEINE SSH-Rechnerschluessel
    # (die werden bewusst nicht mitkopiert) -> sshd startet nicht -> Fernzugang still tot.
    if not os.path.exists('/etc/systemd/system/rikus-mintshot-sshkeys.service'):
        fehlt.append('SSH-Schluessel-Sicherung (Fernzugang im Klon)' if SPRACHE == 'de'
                     else 'SSH host key safeguard (remote access in the clone)')
    if not os.path.exists('/usr/local/sbin/rikus-mintshot-dualboot'):
        fehlt.append('Dualboot-Menue (Windows neben Mint)' if SPRACHE == 'de'
                     else 'dual-boot menu (Windows alongside Mint)')
    if not os.path.exists('/usr/local/sbin/rikus-mintshot-bootorder'):
        fehlt.append('Start-Reihenfolge (Mint zuerst statt Windows)' if SPRACHE == 'de'
                     else 'boot order (Mint first instead of Windows)')
    if not os.path.exists('/etc/systemd/system/rikus-mintshot-bootorder.service'):
        fehlt.append('Start-Reihenfolge-Dienst (greift beim ersten Start des Klons)' if SPRACHE == 'de'
                     else 'boot-order service (runs on the clone\'s first start)')
    if not os.path.exists('/usr/local/sbin/rikus-mintshot-persist-save'):
        fehlt.append('Persistenz-Speicherdienst (RAM-Modus)' if SPRACHE == 'de'
                     else 'persistence save service (RAM mode)')
    if not os.path.exists('/etc/skel/Desktop/system-installieren.desktop'):
        fehlt.append('Installer-Schreibtisch-Symbol' if SPRACHE == 'de' else 'installer desktop icon')
    if _system_app_version() != VERSION:
        fehlt.append('App im System (/opt) — Teil jedes Schnappschusses' if SPRACHE == 'de'
                     else 'app inside the system (/opt) — part of every snapshot')
    # Der Ablageordner — die Stelle, an der ueberhaupt gebaut wird.
    # WARUM DAS HIER GEPRUEFT WERDEN MUSS (Hans-Josef Rausch, 19.07.2026):
    # Alles andere in dieser Liste liegt in /usr oder /etc und ist damit in JEDEM Klon enthalten.
    # Der Ablageordner liegt aber standardmaessig unter /home — und der Modus "Nur System" haengt
    # `- /home/*` an die Ausschlussliste. Nach dem Wiederherstellen eines solchen Klons fehlt er
    # also, waehrend hier alles gruen meldete -> die Ersteinrichtung (die ihn per mkdir+chown
    # anlegt) lief nie -> beim Bauen Zugriff verweigert, der Knopf tat sichtbar nichts.
    # Dieselbe Luecke wie beim Save-Dienst am 16.07.: geprueft wurde nicht, was wirklich noetig ist.
    try:
        _iso_ordner, _ = ablage_ordner()
        if not (os.path.isdir(_iso_ordner) and os.access(_iso_ordner, os.W_OK)):
            fehlt.append(f'Ablageordner {_iso_ordner} (fehlt oder nicht beschreibbar)' if SPRACHE == 'de'
                         else f'destination folder {_iso_ordner} (missing or not writable)')
    except Exception:
        pass          # Die Pruefung ist Komfort und darf die Liste nie zum Absturz bringen.
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

# Live-Bausteine: 0029 legt beim Klon OHNE Home das fehlende Live-Home an (sonst Login-Schleife)
install -m 0755 "{DATEN}/live-hooks/0029-live-user-anlegen" /usr/lib/live/config/
install -m 0755 "{DATEN}/live-hooks/2000-installer-desktop-icon" /usr/lib/live/config/
# Home-Reparatur fuers INSTALLIERTE System: legt beim Installieren fehlende Homes aus
# /etc/skel an (Calamares-shellprocess ruft dieses Skript auf — als Datei, nicht inline,
# weil Calamares $-Variablen im Befehl selbst als eigene Template-Variablen missversteht).
mkdir -p /usr/local/sbin
install -m 0755 "{DATEN}/scripts/rikus-mintshot-home-fix" /usr/local/sbin/
# Netz-Portabilitaet: loest WLAN/LAN im Klon von der Interface-Bindung (netplan "match:"),
# sonst gilt die Verbindung nur fuer die Karte der Quelle -> auf fremder Hardware ist das
# gespeicherte WLAN-Passwort "vergessen". Calamares ruft das Skript im Zielsystem auf.
install -m 0755 "{DATEN}/scripts/rikus-mintshot-netzfix" /usr/local/sbin/
# ...und als Auto-Start-Dienst: so greift die Portabilitaet schon beim LIVE-Boot vom Stick
# (nicht erst nach einer Installation) -> das gespeicherte WLAN verbindet auf fremder
# Hardware von selbst, ohne dass der Nutzer etwas tun muss.
install -m 0644 "{DATEN}/scripts/rikus-mintshot-netzfix.service" /etc/systemd/system/
systemctl enable rikus-mintshot-netzfix.service >/dev/null 2>&1 || true
# SSH-Rechnerschluessel: Der Schnappschuss laesst sie bewusst weg (sonst haetten ALLE Klone
# dieselben und koennten sich fuereinander ausgeben). In der Ausschlussliste steht dazu
# "New ones will be generated upon live boot" - das stimmt aber NUR fuer den Live-Start.
# Nach einer FESTEN INSTALLATION bleibt /etc/ssh leer, sshd startet gar nicht erst
# ("no hostkeys available -- exiting") und der Fernzugang ist tot. Und zwar STILL: am
# Rechner selbst faellt nichts auf, erst beim Zugriff von aussen - also im Notfall.
# Am 21.07.2026 am ersten echten Klon-Dauersystem (asusmint) aufgetreten und belegt.
install -m 0755 "{DATEN}/scripts/rikus-mintshot-sshkeys" /usr/local/sbin/
install -m 0644 "{DATEN}/scripts/rikus-mintshot-sshkeys.service" /etc/systemd/system/
systemctl enable rikus-mintshot-sshkeys.service >/dev/null 2>&1 || true
# Dualboot: os-prober einschalten, damit ein daneben installiertes Windows automatisch
# ins GRUB-Menue kommt (bei modernem Mint ist os-prober standardmaessig aus).
install -m 0755 "{DATEN}/scripts/rikus-mintshot-dualboot" /usr/local/sbin/
# Start-Reihenfolge: setzt den eigenen Firmware-Eintrag nach vorn. Ohne das startet der
# Rechner bei Dualboot mit mehreren Platten weiter Windows (dessen Eintrag steht dort meist
# an Platz 1) — die Platten-Reihenfolge im BIOS hilft nicht, die BootOrder liegt darueber.
# ⭐ Laeuft als EINMALIGER Dienst beim ERSTEN START des Klons, NICHT bei der Installation:
# Der Firmware-Eintrag entsteht erst beim ersten Start (17.07.2026 per Protokoll bewiesen).
# Der Dienst schaltet sich nach Erfolg selbst ab.
install -m 0755 "{DATEN}/scripts/rikus-mintshot-bootorder" /usr/local/sbin/
install -m 0644 "{DATEN}/scripts/rikus-mintshot-bootorder.service" /etc/systemd/system/
# 🛑 HIER BEWUSST KEIN "systemctl enable"! Der Dienst wuerde sonst auf DIESEM Rechner
# (der Klon-QUELLE) beim naechsten Start die Boot-Reihenfolge umstellen und koennte ein
# daneben installiertes zweites System von Platz 1 verdraengen (17.07.2026 im Trockenlauf
# gefunden, bevor es passieren konnte). Die Quelle hat ihre Reihenfolge schon so, wie ihr
# Besitzer sie will.
# Eingeschaltet wird der Dienst NUR im frisch installierten Klon — durch
# rikus-mintshot-dualboot, das Calamares im Zielsystem aufruft.
systemctl disable rikus-mintshot-bootorder.service >/dev/null 2>&1 || true
mkdir -p /etc/skel/Desktop
install -m 0755 "{DATEN}/desktop/system-installieren.desktop" /etc/skel/Desktop/

# Persistenz: Speicher-Dienst fuer den Stick-schonenden Modus (persistence-read-only).
# Dort liegen die Aenderungen im RAM (tmpfs) — beim Herunterfahren schreibt dieser
# Dienst sie in die Persistenz-Kiste zurueck. Er prueft selbst, ob er gebraucht wird
# (nur bei "persistence-read-only" in der Kernel-Zeile), sonst beendet er sich sofort.
install -m 0755 "{DATEN}/persistenz/rikus-mintshot-persist-save" /usr/local/sbin/
install -m 0644 "{DATEN}/persistenz/rikus-mintshot-persist-save.service" /etc/systemd/system/
systemctl enable rikus-mintshot-persist-save.service >/dev/null 2>&1 || true

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
chmod 0755 "{SYSTEM_ORDNER}/rikus-mintshot.py"
cat > /usr/share/applications/rikus-mintshot.desktop <<'MENUE'
[Desktop Entry]
Type=Application
Name=Rikus Mintshot
Comment=1:1 clone of your system as a bootable ISO / 1:1-Klon deines Systems als startfähige ISO
Comment[de]=1:1-Klon deines Linux-Mint-Systems als startfähige ISO — mit einem Klick
Exec=python3 {SYSTEM_ORDNER}/rikus-mintshot.py
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
- /swap-file
- /swap.img
- /swap.swap
- /home/*/.cache/*
- /home/*/.local/share/Trash/*
- /home/*/mnt/*
- /home/*/.gvfs
- /root/.cache/*
'''

# 3. Modus "System + meine Einstellungen": das Home BLEIBT (alle Einstellungen/Konten),
# aber der grosse Datenberg + jederzeit neu ladbare Sachen fliegen raus. So wird der Klon
# schlank UND sofort brauchbar. Wer etwas davon behalten will -> Expertenmodus (Haekchen).
# (~/.cache ist oben schon global ausgeschlossen.)
EINSTELLUNGEN_AUSSCHLUESSE = '''
# --- neu ladbare Zwischenspeicher (bauen sich wieder auf) ---
- /home/*/.npm/*
- /home/*/.local/share/uv/*
# --- grosse, jederzeit neu herunterladbare Pakete (viele GB) ---
- /home/*/.ollama/*
- /home/*/.hermes/*
# --- grosse Spiele ---
- /home/*/.minecraft/*
# --- persoenliche Datenordner (Medien/Dokumente, deutsch + englisch benannt) ---
- /home/*/Downloads/*
- /home/*/Herunterladungen/*
- /home/*/Bilder/*
- /home/*/Pictures/*
- /home/*/Videos/*
- /home/*/Musik/*
- /home/*/Music/*
- /home/*/Dokumente/*
- /home/*/Documents/*
- /home/*/Öffentlich/*
- /home/*/Public/*
- /home/*/Vorlagen/*
- /home/*/Templates/*
'''

def _shim_pfad():
    return SHIM_SIGNED if os.path.exists(SHIM_SIGNED) else SHIM_SIGNED_ALT

def secure_boot_moeglich():
    """Sind die fertig signierten Bausteine + Werkzeuge da, um eine Secure-Boot-faehige
    ISO zu bauen? (shim-signed = Microsoft, grub-efi-amd64-signed = Canonical, mtools.)"""
    return (os.path.exists(_shim_pfad()) and os.path.exists(GRUB_SIGNED)
            and os.path.exists(ISOHDPFX) and shutil.which('mformat') is not None)

def secure_boot_nachbau_bash(iso_ordner=None, work_ordner=None):
    """Bash-Schnipsel (laeuft als root DIREKT nach refractasnapshot): ersetzt das
    selbstgebaute, UNSIGNIERTE EFI durch die fertig signierte Kette
    shim -> GRUB -> (Mint-)Kernel und packt die ISO mit einer echten EFI-System-
    Partition neu. Ergebnis bootet auch mit eingeschaltetem Secure Boot.
    Ist idempotent + selbstsichernd: fehlt etwas, bleibt die normale ISO unveraendert.
    iso_ordner/work_ordner MUESSEN zum gewaehlten Ablageort passen (sonst findet der
    Nachbau die frische ISO nicht + raeumt den falschen Ordner auf)."""
    shim = _shim_pfad()
    if iso_ordner is None or work_ordner is None:
        iso_ordner, work_ordner = ablage_ordner()
    return f'''
# ===== Secure-Boot-Nachbau =====
SB_WORK="{work_ordner}"; SB_ISOROOT="$SB_WORK/iso"; SB_SNAP="{iso_ordner}"
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
    # --- Platz pruefen: der Umbau schreibt die neue ISO NEBEN die alte und braucht darum
    #     kurz das Doppelte an ISO-Platz. Reicht es nicht, brechen wir SAUBER mit klarer
    #     Meldung ab (statt xorriso mittendrin scheitern zu lassen) -- die fertige normale
    #     ISO bleibt unversehrt, der Nutzer wird gewarnt (kein stiller Ausfall mehr).
    SB_FREI=$(df -P "$SB_SNAP" | awk 'NR==2{{print $4*1024}}')
    SB_SZ=$(stat -c%s "$SB_ISO" 2>/dev/null || echo 0)
    if [ "${{SB_FREI:-0}}" -lt "${{SB_SZ:-0}}" ] 2>/dev/null; then
      SB_MB=$(( ( ${{SB_SZ:-0}} - ${{SB_FREI:-0}} ) / 1048576 + 100 ))
      echo "!!!SECURE-BOOT-PLATZ:$SB_MB!!! Fuer den Secure-Boot-Umbau fehlt Platz (~$SB_MB MB)."
      echo "Die ISO ist fertig, aber NICHT Secure-Boot-faehig. Platz freimachen und neu bauen."
    elif xorriso -as mkisofs -r -J -joliet-long -l -iso-level 3 \\
        -isohybrid-mbr "$SB_PFX" -partition_offset 16 -V "$SB_VOL" \\
        -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table \\
        -eltorito-alt-boot -e '--interval:appended_partition_2:all::' -no-emul-boot \\
        -append_partition 2 {ESP_TYP_GUID} "$SB_EFI" -appended_part_as_gpt \\
        -o "$SB_ISO.sb" "$SB_ISOROOT"; then
      mv -f "$SB_ISO.sb" "$SB_ISO"
      sha256sum "$SB_ISO" > "$SB_ISO.sha256"
      echo "Secure-Boot-ISO fertig: $(basename "$SB_ISO")"
    else
      rm -f "$SB_ISO.sb"
      echo "!!!SECURE-BOOT-FEHLGESCHLAGEN!!! Der Umbau ist gescheitert - die normale ISO bleibt erhalten."
    fi
  fi
fi
rm -rf "$SB_WORK" 2>/dev/null || true
echo "All finished!"
'''

def system_ballast_ausschluesse():
    """Dinge, die einen Klon unnoetig VERVIELFACHEN wuerden — automatisch erkannt, egal
    wie sie heissen. Ohne das laeuft die Platte beim Bau voll und die ISO wird unbrauchbar:
      * Aktive Swap-Dateien (aus /proc/swaps) — der Name variiert (swapfile, swap-file, ...),
        eine feste Liste verfehlt ihn leicht. Swap gehoert nie in einen Klon.
      * Ein zweites Betriebssystem als 'Frugal'-Installation im Wurzelverzeichnis
        (ein Ordner mit einer 'linuxfs'-Datei). Dessen rootfs/homefs sind SPARSE-Dateien:
        `du` zeigt wenige GB, beim Kopieren blaehen sie aber auf ihre volle Groesse auf
        (z. B. 6,5 GB -> 113 GB). Eine zweite OS gehoert ohnehin nicht in den Klon.
    Gibt absolute Pfade zurueck."""
    aus = []
    try:
        for zeile in open('/proc/swaps').read().splitlines()[1:]:
            pfad = zeile.split()[0] if zeile.split() else ''
            if pfad.startswith('/') and not pfad.startswith('/dev/'):
                aus.append(pfad)
    except OSError:
        pass
    try:
        for eintrag in os.scandir('/'):
            if (eintrag.is_dir(follow_symlinks=False)
                    and os.path.exists(os.path.join(eintrag.path, 'linuxfs'))):
                aus.append(eintrag.path)
    except OSError:
        pass
    return aus


def bau_eigene_ausschluesse(conf_pfad):
    """Die drei Ordner, die refractasnapshot ZUSAETZLICH zur Liste auslaesst.

    In refractasnapshot (Zeile 750) steht:
        --exclude="$work_dir" --exclude="$snapshot_dir" --exclude="$efi_work"
                                                        --exclude-from="$snapshot_excludes"
    Diese drei stehen also NICHT in klon.list, werden aber trotzdem nicht kopiert.
    Wer sie beim Messen mitzaehlt, bekommt einen Fehlalarm — gemessen 20.07.2026 auf lm:
    102,7 GB gemeldet statt der echten ~40 GB, weil der ISO-Ordner /home/snapshot mit
    63 GB fertiger Abbilder mitgezaehlt wurde. Der Klon davor war 15,6 GB gross.

    Die Werte kommen aus DERSELBEN Konfigurationsdatei, die der Bau gleich darauf liest —
    so koennen Messung und Bau nicht auseinanderlaufen, auch wenn der Ablageort wechselt.
    """
    ordner = []
    try:
        with open(conf_pfad) as f:
            inhalt = f.read()
    except OSError:
        return ordner
    werte = {}
    for schluessel in ('work_dir', 'snapshot_dir', 'efi_work'):
        m = re.search(r'^\s*' + schluessel + r'\s*=\s*"?([^"\n]+)"?\s*$', inhalt, re.M)
        if m:
            werte[schluessel] = m.group(1).strip()
    # efi_work steht als "${work_dir}/efi-files" oder schon aufgeloest -> beides abfangen
    for schluessel, pfad in werte.items():
        for platzhalter, ersatz in (('${work_dir}', werte.get('work_dir', '')),
                                    ('$work_dir', werte.get('work_dir', ''))):
            if ersatz:
                pfad = pfad.replace(platzhalter, ersatz)
        if pfad.startswith('/'):
            ordner.append(pfad.rstrip('/'))
    return ordner


def klon_bedarf_ermitteln(root, liste_pfad, zeit_limit=180, conf_pfad=None):
    """Wie viele Bytes schreibt der Bau WIRKLICH? — nicht geschaetzt, sondern gefragt.

    rsync macht einen Trockenlauf (`--dry-run` kopiert NICHTS) mit GENAU der Ausschlussliste,
    die refractasnapshot gleich darauf benutzt, und meldet die Gesamtgroesse des Dateibaums.
    Das ist exakt die Menge, die spaeter geschrieben wird — inklusive der Sparse-Dateien, bei
    denen `du` in die Irre fuehrt (gemessen 18.07. auf lm):
        /antiX-Frugal   belegt 10,9 GB  ->  geschrieben 155,6 GB
        VM (libvirt)    belegt 14,7 GB  ->  geschrieben  60,0 GB
        /timeshift      belegt 72,9 GB  ->  geschrieben 332,6 GB
    Selbst zusammenrechnen (belegt minus Ausschluesse) waere genau an dieser Stelle falsch.

    ROOT ist Pflicht: ohne ihn verfehlt rsync die geschuetzten Ordner — gemessen 31,5 statt
    89,4 GB bei 53x "permission denied". ZU KLEIN schaetzen ist exakt der Fehler, an dem Peter
    Linus Bau bei 44 % starb ("0 bytes remaining" bei 411 GB frei / 303 GB Daten).

    Rueckgabe: Bytes (int) — oder None, wenn es nicht klappt. Dann faellt der Aufrufer auf die
    grobe Schaetzung zurueck: der Platz-Check ist Komfort und darf den Bau NIE blockieren.
    """
    if not liste_pfad or not os.path.exists(liste_pfad):
        return None
    # Das Ziel existiert absichtlich NICHT und wird auch nicht angelegt (--dry-run schreibt nichts).
    # Gelesen wird nur "Total file size" = Summe ALLER Quelldateien — unabhaengig davon, was am
    # Ziel schon liegt (das waere "Total transferred file size" und hier die falsche Zahl).
    ziel = '/tmp/rikus-mintshot-platzprobe'
    # Die drei bau-eigenen Ausschluesse MUESSEN mit — sonst zaehlt die Messung den ISO- und
    # den Arbeitsordner mit, die der Bau nie anfasst (Fehlalarm, 20.07.2026 auf lm).
    if conf_pfad is None:
        conf_pfad = os.path.join(KONFIG_ORDNER, 'klon.conf')
    extra = ''.join(f'--exclude={shlex.quote(p)} '
                    for p in bau_eigene_ausschluesse(conf_pfad))
    befehl = (f'{root} rsync -a --dry-run --stats {extra}'
              f'--exclude-from={shlex.quote(liste_pfad)} / {shlex.quote(ziel)}')
    try:
        # LC_ALL=C: sonst wechselt der Tausendertrenner mit der Sprache und das Auslesen bricht.
        e = subprocess.run(befehl, shell=True, capture_output=True, text=True,
                           timeout=zeit_limit, env={**os.environ, 'LC_ALL': 'C'})
    except (subprocess.TimeoutExpired, OSError, ValueError):
        return None
    treffer = re.search(r'Total file size:\s*([\d.,]+)\s*bytes', e.stdout)
    if not treffer:
        return None
    zahl = re.sub(r'\D', '', treffer.group(1))          # Tausendertrenner entfernen
    return int(zahl) if zahl else None


def konfig_anlegen(weglassen=None, modus='voll', iso_ordner=None, work_ordner=None):
    """Klon-Konfiguration frisch schreiben (kein Root noetig). weglassen = Liste
    absoluter Ordner-Pfade, deren INHALT draussen bleibt (Haekchen).
    modus: 'ohne' = ganzes /home raus (nacktes System); 'einstellungen' = Home BLEIBT,
    aber der grosse Datenberg raus (schlank + brauchbar); 'voll' = 1:1-Klon mit allem.
    iso_ordner/work_ordner = gewaehlter Ablageort (Default: gespeicherte Ablage)."""
    if iso_ordner is None or work_ordner is None:
        iso_ordner, work_ordner = ablage_ordner()
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
    ballast = system_ballast_ausschluesse()
    if ballast:
        liste += "\n# Automatisch erkannt (Swap-Datei / zweites Betriebssystem — wuerde den Klon aufblaehen):\n"
        for pfad in ballast:
            sicher = re.sub(r'([\[\]*?])', r'\\\1', pfad)   # rsync-Metazeichen woertlich nehmen
            liste += f"- {sicher}\n"
    if modus == 'ohne':
        # "Nur System": persoenliche Daten bleiben KOMPLETT draussen -> schlanke
        # ISO. Der Live-Nutzer bekommt ohnehin ein frisches Home (live-config).
        liste += "\n# Nur System gewaehlt: alle persoenlichen Ordner ausschliessen\n- /home/*\n"
    elif modus == 'einstellungen':
        # "System + meine Einstellungen": Home BLEIBT (Konfig/Konten/Pika/Mails), nur
        # der grosse Datenberg + neu ladbare Sachen (grosse Pakete, Caches) fliegen raus.
        liste += EINSTELLUNGEN_AUSSCHLUESSE
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
        'snapshot_dir': f'"{iso_ordner}"',           # ISO landet DORT, wo die App sie sucht
        'work_dir': f'"{work_ordner}"',              # grosse Systemkopie -> gewaehlter Ablageort
        'efi_work': f'"{work_ordner}/efi-files"',    # EFI-Arbeitsordner mit umziehen
        'kernel_image': f'"{KONFIG_ORDNER}/vmlinuz"',
        'initrd_image': f'"{KONFIG_ORDNER}/initrd.img"',
        'make_sha256sum': '"yes"',
        # Datei-Capabilities (z.B. ping's cap_net_raw=ep) + ACLs beim Kopieren MITNEHMEN.
        # refractasnapshot kopiert mit `rsync -av`, und -a enthaelt KEINE xattrs -> ohne dies
        # verliert JEDER Klon die capabilities: ping laeuft dann nur noch mit sudo, andere
        # setcap-Programme brechen. --xattrs traegt security.capability mit; mksquashfs bewahrt
        # xattrs standardmaessig weiter. (rsync_option3 wird in refractasnapshot an den System-
        # rsync angehaengt: `rsync -av / myfs/ ... ${rsync_option3}`.)
        'rsync_option3': '"--xattrs --acls"',
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
    nutzer_eintrag = os.path.expanduser('~/.local/share/applications/rikus-mintshot.desktop')
    if os.path.exists('/usr/share/applications/rikus-mintshot.desktop'):
        if os.path.exists(nutzer_eintrag):
            try:
                os.remove(nutzer_eintrag)
            except OSError:
                pass
        return
    exec_zeile = f'Exec=python3 "{os.path.join(APP_ORDNER, "rikus-mintshot.py")}"'
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
        super().__init__(title=f"Rikus Mintshot {VERSION}")
        self.set_default_size(760, 700)
        self.set_border_width(14)
        self.icon_pfad = os.path.join(DATEN, 'icon.png')
        if os.path.exists(self.icon_pfad):
            self.set_icon_from_file(self.icon_pfad)

        self.selbsttest = selbsttest
        if selbsttest:
            self.iso_ordner = os.environ.get('MINT_SNAP_TESTORDNER', ISO_ORDNER)
            self.work_ordner = os.path.join(os.path.dirname(self.iso_ordner), 'work')
        else:
            self.iso_ordner, self.work_ordner = ablage_ordner()
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

        # Update-Hinweis: bleibt UNSICHTBAR, solange nichts Neues da ist.
        # set_no_show_all verhindert, dass das spaetere show_all() ihn doch einblendet.
        self.update_label = Gtk.Label()
        self.update_label.set_no_show_all(True)
        self.update_label.set_justify(Gtk.Justification.CENTER)
        haupt.pack_start(self.update_label, False, False, 0)
        threading.Thread(target=self._update_pruefen, daemon=True).start()

        info_zeile = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.info_label = Gtk.Label()
        self.info_label.set_halign(Gtk.Align.START)
        info_zeile.pack_start(self.info_label, True, True, 0)
        self.knopf_ablage = Gtk.Button(label=T['knopf_ablage'])
        self.knopf_ablage.set_tooltip_text(T['ablage_tooltip'])
        self.knopf_ablage.connect('clicked', self.ablageort_waehlen)
        info_zeile.pack_start(self.knopf_ablage, False, False, 0)
        haupt.pack_start(info_zeile, False, False, 0)

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
        self.rb_einstellungen = Gtk.RadioButton.new_with_label_from_widget(self.rb_ohne_home, T['home_einstellungen'])
        self.rb_mit_home = Gtk.RadioButton.new_with_label_from_widget(self.rb_ohne_home, T['home_mit'])
        self.rb_einstellungen.set_active(True)   # Standard: schlank ABER brauchbar (Einstellungen bleiben)
        box_wahl.pack_start(self.rb_ohne_home, False, False, 0)
        box_wahl.pack_start(self.rb_einstellungen, False, False, 0)
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

        # Virtuelle Maschinen: eigene, GUT SICHTBARE Zeile direkt unter der Modus-Wahl —
        # bewusst NICHT im zugeklappten "Fuer Fortgeschrittene"-Bereich, denn dort macht sie
        # kaum jemand auf. VMs kommen in JEDEM Modus mit (sie liegen unter /var, nicht im
        # Persoenlichen Ordner) und sind meist der groesste Brocken: bei Gilbert 60 von 96 GB.
        # ⚠️ UMGEKEHRTE LOGIK zu den Haekchen weiter unten: dort bedeutet "angehakt" WEGLASSEN.
        # Hier ist die Frage positiv gestellt ("mitnehmen?") -> angehakt = MITNEHMEN.
        # Voreinstellung "mitnehmen", damit nichts heimlich verschwindet (1:1-Versprechen) —
        # genau diese Ueberraschung hatte Peter Linu ("Win10 fehlt in meinen VirtualBoxen").
        # Die Wahl wird ueber WEGLASSEN_DATEI mitgespeichert: einmal setzen genuegt.
        self.vm_pfade = vm_ordner()
        self.cb_vms = None
        if self.vm_pfade:
            self.cb_vms = Gtk.CheckButton(label=T['vm_mitnehmen'])
            self.cb_vms.set_active(not any(p in gemerkt for p in self.vm_pfade))
            self.cb_vms.set_tooltip_text('\n'.join(self.vm_pfade))
            box_wahl.pack_start(self.cb_vms, False, False, 4)

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
        # Knopf: beliebigen weiteren Ordner weglassen
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
        self.knopf_persist = Gtk.Button(label=T['knopf_persist'])
        self.knopf_persist.connect('clicked', self.persistenz_anlegen)
        self.knopf_loesch = Gtk.Button(label=T['knopf_loesch'])
        self.knopf_loesch.connect('clicked', self.iso_loeschen)
        for k in (self.knopf_stick, self.knopf_pruef, self.knopf_persist, self.knopf_loesch):
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

    def ablageort_waehlen(self, _knopf):
        de = SPRACHE == 'de'
        dlg = Gtk.FileChooserDialog(
            title=("Ablageort wählen — auf welcher Platte soll gebaut werden?" if de
                   else "Choose location — which drive to build on?"),
            transient_for=self, action=Gtk.FileChooserAction.SELECT_FOLDER)
        dlg.add_button('Abbrechen' if de else 'Cancel', Gtk.ResponseType.CANCEL)
        dlg.add_button('Wählen' if de else 'Choose', Gtk.ResponseType.OK)
        start = ablage_basis()
        if os.path.isdir(start):
            dlg.set_current_folder(start)
        if dlg.run() == Gtk.ResponseType.OK:
            basis = dlg.get_filename()
            dlg.destroy()
            # Schreibbarkeit pruefen — sonst scheitert der Bau spaeter kryptisch
            probe = os.path.join(basis, '.rikus-mintshot-schreibtest')
            try:
                os.makedirs(basis, exist_ok=True)
                with open(probe, 'w') as f:
                    f.write('x')
                os.remove(probe)
            except OSError:
                self.melde(Gtk.MessageType.ERROR,
                           'Kein Schreibrecht' if de else 'Not writable',
                           (f"In »{basis}« darf nicht geschrieben werden.\n"
                            "Bitte einen anderen Ordner wählen (z. B. auf einer\n"
                            "zweiten Festplatte, die dir gehört).") if de else
                           (f"Cannot write to “{basis}”.\nPlease pick another folder "
                            "(e.g. on a second drive you own)."))
                return
            try:
                os.makedirs(KONFIG_ORDNER, exist_ok=True)
                with open(ABLAGE_DATEI, 'w') as f:
                    f.write(basis)
            except OSError:
                pass
            self.iso_ordner, self.work_ordner = ablage_ordner(basis)
            self.liste_aktualisieren()
        else:
            dlg.destroy()

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
            # ⚠️ Nur die EINGESETZTEN Werte entschaerfen, nicht die Vorlage —
            # die enthaelt selbst <b>...</b>. Ohne markup_escape_text blieb die
            # Zeile bei einem Ordnernamen mit "&" (z. B. "Musik & Filme") vollstaendig
            # LEER, ohne jede Fehlermeldung: set_markup verwirft den ganzen Text,
            # wenn ein einzelnes & darin steht. Die vier anderen set_markup-Stellen
            # im Programm waren abgesichert, nur diese nicht.
            self.info_label.set_markup("<span size='small'>" + T['ablage'].format(
                ordner=GLib.markup_escape_text(str(self.iso_ordner)),
                platz=GLib.markup_escape_text(str(self._freier_platz()))) + "</span>")
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

    def _update_pruefen(self):
        """Laeuft im EIGENEN Faden, damit das Fenster nie auf das Netz wartet.

        Das Ergebnis darf nicht von hier aus in die Oberflaeche geschrieben werden -
        GTK vertraegt keine Zugriffe aus fremden Faeden. Deshalb der Rueckweg ueber
        GLib.idle_add, das die Anzeige im Oberflaechen-Faden erledigt.
        """
        try:
            neu = neuere_version()
            if neu:
                GLib.idle_add(self._update_zeigen, neu)
        except Exception:
            pass                  # ein Hinweis darf das Programm niemals stoeren

    def _update_zeigen(self, neu):
        """Blendet die Hinweiszeile ein. Laeuft im Oberflaechen-Faden (via idle_add)."""
        try:
            # ⚠️ Die Versionsnummer kommt AUS DEM INTERNET und landet in set_markup.
            # Ein "&" darin macht ohne Absicherung die GANZE Zeile unsichtbar - ohne
            # jede Fehlermeldung. Genau dieser Fehler steckte bis 6.10 in der Ablage-Zeile.
            text = GLib.markup_escape_text(T['update_da'].format(v=neu))
            link = GLib.markup_escape_text(T['update_link'])
            self.update_label.set_markup(
                f"<span size='small' foreground='#2e7d32'>{text} — "
                f"<a href='{GLib.markup_escape_text(UPDATE_SEITE)}'>{link}</a></span>")
            self.update_label.show()
        except Exception:
            pass
        return False              # idle_add: nur einmal ausfuehren

    def _ablage_bereitstellen(self):
        """Ablageordner anlegen und beschreibbar machen. Rueckgabe: True = der Bau kann starten.

        WARUM ES DIESE METHODE GIBT (Hans-Josef Rausch, 19.07.2026):
        Hier stand frueher ein nacktes `os.makedirs(self.iso_ordner, exist_ok=True)`. Nach dem
        WIEDERHERSTELLEN eines Klons, der im Modus "Nur System" gebaut wurde, geht das schief:
          * "Nur System" haengt `- /home/*` an die Ausschlussliste -> /home/snapshot ist NICHT im Klon
          * `fehlende_teile()` prueft nur /usr und /etc -> meldet "eingerichtet" -> die
            Ersteinrichtung laeuft nie, und NUR sie legt den Ordner an (mkdir + chown)
          * /home gehoert root (drwxr-xr-x) -> ein normaler Benutzer darf dort nichts anlegen
        Ergebnis: PermissionError, ungebremst aus dem Klick-Handler -> fuer den Nutzer tat der
        Knopf einfach NICHTS. Seine Meldung: "Mintshot konnte zwar gestartet werden, aber kein
        neuer Schnappschuss erstellt werden" - auch nach Neuinstallation nicht, denn das .deb
        legt diesen Ordner ebenfalls nicht an (im postinst kommt er nicht vor).

        Reihenfolge: selbst versuchen -> mit Verwalter-Rechten nachhelfen (die haben wir an
        dieser Stelle ohnehin schon) -> sonst ehrlich melden statt stillem Nichts.
        """
        try:
            os.makedirs(self.iso_ordner, exist_ok=True)
        except OSError:
            pass                      # kein Abbruch: gleich kommt der Versuch mit Root
        if not (os.path.isdir(self.iso_ordner) and os.access(self.iso_ordner, os.W_OK)):
            # Genau das, was sonst die Ersteinrichtung tut - nur eben jetzt.
            ziel = shlex.quote(self.iso_ordner)
            try:
                subprocess.run(f'{self.root} mkdir -p {ziel} && '
                               f'{self.root} chown {shlex.quote(getpass.getuser())} {ziel}',
                               shell=True, capture_output=True, timeout=60)
            except (OSError, subprocess.TimeoutExpired, ValueError):
                pass
        if os.path.isdir(self.iso_ordner) and os.access(self.iso_ordner, os.W_OK):
            return True
        de = SPRACHE == 'de'
        self.melde(Gtk.MessageType.ERROR,
                   'Ablageort lässt sich nicht anlegen' if de else 'Cannot create the destination folder',
                   (f"{self.iso_ordner}\n\n"
                    "Dieser Ordner fehlt und ließ sich auch nicht anlegen.\n\n"
                    "Das passiert vor allem nach dem Wiederherstellen eines Klons, der im Modus\n"
                    "„Nur System“ gebaut wurde: Dabei bleibt alles unterhalb von /home draußen —\n"
                    "auch dieser Ordner. Und /home gehört dem Verwalter, deshalb darf ein\n"
                    "normaler Benutzer dort nichts anlegen.\n\n"
                    "Abhilfe: Knopf „📁 Ablageort ändern“ und einen Ordner wählen, in dem du\n"
                    "schreiben darfst (zum Beispiel in deinem Persönlichen Ordner)." ) if de else
                   (f"{self.iso_ordner}\n\n"
                    "This folder is missing and could not be created.\n\n"
                    "This mainly happens after restoring a clone built in \"System (root) only\"\n"
                    "mode: everything below /home is left out then — including this folder. And\n"
                    "/home belongs to the administrator, so a normal user cannot create anything\n"
                    "there.\n\n"
                    "Fix: use the „📁 Location“ button and pick a folder you can write to (your\n"
                    "home folder, for instance)."))
        return False

    def bauen_geklickt(self, _knopf):
        if self.lauf_aktiv:
            return
        self.root = root_praefix()   # JETZT bestimmen: ein sudo-Zeitstempel vom Start kann abgelaufen sein
        if not self._ablage_bereitstellen():
            return

        # Die Platz-Warnung stand frueher GENAU HIER — und damit zu frueh: die Ausschlussliste
        # (klon.list) entsteht erst weiter unten in konfig_anlegen(). Ohne sie liess sich der Bedarf
        # nur grob raten ("so viel wie das System belegt"), und dieses Raten lag in beide Richtungen
        # daneben: bei Peter Linu zu klein (durchgewunken -> Abbruch bei 44 %), auf Gilberts eigenem
        # Rechner viel zu gross (181 GB angenommen, echter Klon 29 GB -> Fehlalarm bei jedem Bau).
        # Sie sitzt jetzt direkt HINTER konfig_anlegen() und fragt rsync nach der echten Menge.

        weglassen = [pfad for pfad, cb in self.haekchen.items() if cb.get_active()]
        # VM-Zeile: Haken WEG = virtuelle Maschinen draussen lassen (umgekehrte Logik, s. o.).
        # Wandert mit in WEGLASSEN_DATEI -> die Wahl bleibt beim naechsten Bau erhalten.
        if getattr(self, 'cb_vms', None) is not None and not self.cb_vms.get_active():
            weglassen += [p for p in self.vm_pfade if p not in weglassen]
        try:
            os.makedirs(KONFIG_ORDNER, exist_ok=True)
            with open(WEGLASSEN_DATEI, 'w') as f:
                json.dump(weglassen, f)
        except OSError:
            pass
        if not self.selbsttest:
            if self.rb_ohne_home.get_active():
                modus = 'ohne'
            elif self.rb_einstellungen.get_active():
                modus = 'einstellungen'
            else:
                modus = 'voll'
            if not konfig_anlegen(weglassen, modus, self.iso_ordner, self.work_ordner):
                self.melde(Gtk.MessageType.ERROR, T['konfig_fehlt'],
                           '/etc/refractasnapshot.conf')
                return

            # ---- Platz-Warnung MIT DER ECHTEN MENGE (die Ausschlussliste steht jetzt) ----
            # Gebraucht wird das DOPPELTE: der Bau legt erst eine Kopie des Systems ab (myfs) und
            # packt sie danach DANEBEN noch einmal zusammen (squashfs) — beides liegt gleichzeitig
            # auf der Platte. Bei kaum komprimierbaren Daten (Fotos, Videos, VM-Platten) ist das
            # gepackte Abbild fast so gross wie die Kopie. Nur WARNEN, nie blockieren.
            try:
                st_z = os.statvfs(self.iso_ordner if os.path.isdir(self.iso_ordner) else '/')
                frei = st_z.f_bavail * st_z.f_frsize
                self.setze_phase('Platzbedarf wird ermittelt ...' if SPRACHE == 'de'
                                 else 'Checking disk space ...')
                while Gtk.events_pending():     # Anzeige auffrischen, bevor rsync kurz blockiert
                    Gtk.main_iteration()
                menge = klon_bedarf_ermitteln(self.root, os.path.join(KONFIG_ORDNER, 'klon.list'))
                genau = menge is not None
                if not genau:
                    # Rueckfall, falls rsync nicht antwortet: grob wie frueher (alles auf der
                    # Systemplatte). Ungenau, aber eine grobe Warnung ist besser als gar keine.
                    st_s = os.statvfs('/')
                    menge = (st_s.f_blocks - st_s.f_bfree) * st_s.f_frsize
                brauch = menge * 2
                if frei < brauch:
                    de = SPRACHE == 'de'
                    unsicher = ('' if genau else
                                ("\n(Grobe Schätzung — die genaue Messung war nicht möglich.)\n"
                                 if de else
                                 "\n(Rough estimate — the exact measurement was not possible.)\n"))
                    dlg = Gtk.MessageDialog(
                        transient_for=self, modal=True, message_type=Gtk.MessageType.WARNING,
                        buttons=Gtk.ButtonsType.OK_CANCEL,
                        text=("Es könnte zu wenig Speicherplatz sein" if de
                              else "There may be too little disk space"))
                    dlg.format_secondary_text(
                        (f"Ablageort: {self.iso_ordner}\n"
                         f"Dort frei:            {groesse_lesbar(frei)}\n"
                         f"Dein Klon wird ca.:   {groesse_lesbar(menge)}\n"
                         f"Gebraucht beim Bau:   {groesse_lesbar(brauch)}\n"
                         f"{unsicher}\n"
                         "Der Bau legt zuerst eine Kopie deines Systems ab und packt sie danach\n"
                         "DANEBEN noch einmal zusammen. Beides liegt gleichzeitig auf der Platte —\n"
                         "deshalb braucht der Bau kurzzeitig etwa das DOPPELTE.\n\n"
                         "Läuft der Platz mittendrin aus, bricht der Bau ab — die ISO wird dann\n"
                         "unbrauchbar.\n\n"
                         "Tipp: große Ordner abwählen, einen schlankeren Modus wählen, oder den\n"
                         "Ablageort auf eine Platte mit mehr Platz legen (Knopf „Ablageort“).\n\n"
                         "Trotzdem fortfahren?") if de else
                        (f"Destination: {self.iso_ordner}\n"
                         f"Free there:         {groesse_lesbar(frei)}\n"
                         f"Your clone will be: {groesse_lesbar(menge)}\n"
                         f"Needed to build:    {groesse_lesbar(brauch)}\n"
                         f"{unsicher}\n"
                         "The build first copies your system, then packs a compressed image\n"
                         "NEXT TO that copy. Both sit on the disk at the same time — so the\n"
                         "build briefly needs about TWICE that size.\n\n"
                         "If space runs out mid-build, it aborts — the ISO becomes unusable.\n\n"
                         "Tip: deselect large folders, pick a leaner mode, or put the destination\n"
                         "on a drive with more room (“Location” button).\n\n"
                         "Continue anyway?"))
                    antwort = dlg.run()
                    dlg.destroy()
                    if antwort != Gtk.ResponseType.OK:
                        return
            except Exception:
                pass   # Platz-Check ist reiner Komfort — nie den Bau daran scheitern lassen

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
                # Sicherheitsnetz fuers WLAN: eine Kopie der gespeicherten Verbindungen
                # wandert ins Abbild. Findet NetworkManager sie beim Start des Klons nicht
                # (die netplan-Erzeugung ist die einzige Quelle und kann ausfallen), holt
                # der Autostart-Dienst sie von dort zurueck. Nie den Bau daran scheitern
                # lassen -> "|| true".
                f'{{ /usr/local/sbin/rikus-mintshot-netzfix --sichern || true ; }} && '
                f'cp "{grub_v}" /usr/lib/refractasnapshot/grub.cfg.template && '
                f'cp "{live_v}" /usr/lib/refractasnapshot/iso/isolinux/live.cfg && '
                # Die Start-Datei (initrd) MUSS den Live-Start (live-boot) enthalten, sonst
                # "Kernel Panic" beim Booten vom Stick. live-boot liefert die Bausteine, aber
                # die initrd wird nach dessen Installation nicht automatisch neu gebaut, und
                # refractasnapshot baut sie ebenfalls NICHT neu -> auf frisch eingerichteten
                # Rechnern fehlt der Live-Start. Absichern: fehlt er, initrd einmal neu bauen.
                f'{{ lsinitramfs /boot/initrd.img-{kern} 2>/dev/null | grep -q scripts/live '
                f'|| update-initramfs -u -k {kern} ; }} && '
                f'printf "1\\n{DISTRO}\\n" | refractasnapshot -c "{conf}"')
            if secure_boot_moeglich():
                # Nachbau in eine Datei schreiben (haelt Anfuehrungszeichen aus dem Aufruf raus)
                sb_skript = os.path.join(KONFIG_ORDNER, 'secure-boot-nachbau.sh')
                with open(sb_skript, 'w') as f:
                    f.write('#!/bin/bash\n' + secure_boot_nachbau_bash(self.iso_ordner, self.work_ordner))
                innen += f' && bash "{sb_skript}"'  # nur bei ERFOLGREICHEM refracta-Bau
            else:
                # Die signierten Bausteine fehlen -> die ISO wird NICHT Secure-Boot-faehig.
                # KEIN stiller Ausfall: einen Marker ins Log schreiben (immer, mit ';'), den
                # die App nach dem Bau als sichtbare Warnung + Behebungsbefehl zeigt.
                fehlend = []
                if not (os.path.exists(SHIM_SIGNED) or os.path.exists(SHIM_SIGNED_ALT)):
                    fehlend.append('shim-signed')
                if not os.path.exists(GRUB_SIGNED):
                    fehlend.append('grub-efi-amd64-signed')
                if not os.path.exists(ISOHDPFX):
                    fehlend.append('isolinux')
                if shutil.which('mformat') is None:
                    fehlend.append('mtools')
                innen += f' ; echo "!!!SECURE-BOOT-BAUSTEIN-FEHLT:{" ".join(fehlend)}!!!"'
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

    def _secure_boot_warnung(self, log_text):
        """Prueft das Bau-Protokoll auf die Secure-Boot-Marker und gibt (Titel, Text) fuer eine
        sichtbare Warnung zurueck -- oder None, wenn die ISO Secure-Boot-faehig ist. So erfaehrt der
        Nutzer SOFORT (nicht erst am fremden Rechner), wenn der Umbau nicht lief, und was zu tun ist."""
        de = SPRACHE == 'de'
        # 1) signierte Bausteine fehlen
        m = re.search(r'!!!SECURE-BOOT-BAUSTEIN-FEHLT:([^!]*)!!!', log_text)
        if m:
            pakete = m.group(1).strip() or 'shim-signed grub-efi-amd64-signed isolinux mtools'
            if de:
                return ("ISO ist NICHT Secure-Boot-fähig",
                        "Die ISO ist fertig, startet aber NICHT auf Rechnern mit eingeschaltetem "
                        "Secure Boot — es fehlen die signierten Bausteine.\n\n"
                        f"Fehlt: {pakete}\n\n"
                        "So behebst du es (einmalig), dann neu bauen:\n\n"
                        f"sudo apt install {pakete}")
            return ("ISO is NOT Secure-Boot-capable",
                    "The ISO is finished but will NOT start on machines with Secure Boot on — "
                    "the signed building blocks are missing.\n\n"
                    f"Missing: {pakete}\n\n"
                    "Fix it once, then build again:\n\n"
                    f"sudo apt install {pakete}")
        # 2) Platz war zu knapp fuer die zweite ISO
        m = re.search(r'!!!SECURE-BOOT-PLATZ:(\d+)!!!', log_text)
        if m:
            mb = m.group(1)
            if de:
                return ("ISO ist NICHT Secure-Boot-fähig (zu wenig Platz)",
                        "Die ISO ist fertig, aber der Secure-Boot-Umbau brauchte kurz Platz für eine "
                        f"zweite ISO — es fehlten etwa {mb} MB. Deshalb ist die ISO NICHT "
                        "Secure-Boot-fähig (startet nicht bei eingeschaltetem Secure Boot).\n\n"
                        "So bekommst du eine Secure-Boot-ISO:\n"
                        f"Mach mindestens {mb} MB frei (oder lege den Ablageort auf eine Platte mit "
                        "mehr Platz — Knopf „Ablageort ändern“) und baue dann neu.")
            return ("ISO is NOT Secure-Boot-capable (not enough space)",
                    "The ISO is finished, but making it Secure-Boot-capable briefly needed room for "
                    f"a second ISO — about {mb} MB were missing. So the ISO is NOT Secure-Boot-capable.\n\n"
                    f"To get one: free at least {mb} MB (or pick a destination with more room), then rebuild.")
        # 3) anderer xorriso-Fehler
        if '!!!SECURE-BOOT-FEHLGESCHLAGEN!!!' in log_text:
            if de:
                return ("ISO ist NICHT Secure-Boot-fähig",
                        "Die ISO ist fertig, aber der Secure-Boot-Umbau ist fehlgeschlagen — sie "
                        "startet nicht auf Rechnern mit eingeschaltetem Secure Boot.\n\n"
                        "Einzelheiten stehen unter „Technische Einzelheiten“. Versuche einen neuen Bau.")
            return ("ISO is NOT Secure-Boot-capable",
                    "The ISO is finished, but making it Secure-Boot-capable failed — it will not "
                    "start on machines with Secure Boot enabled.\n\nSee „Technical details“. Try again.")
        return None

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
                log_text = f.read()
        except FileNotFoundError:
            log_text = ''
        erfolg_im_log = 'All finished!' in log_text
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
            # Secure-Boot-Warnung: die ISO ist fertig, aber der Secure-Boot-Umbau lief NICHT
            # (Platz zu knapp / Bausteine fehlen / xorriso-Fehler). Kein stiller Ausfall mehr.
            sb_warn = self._secure_boot_warnung(log_text)
            if sb_warn:
                self.melde(Gtk.MessageType.WARNING, sb_warn[0], sb_warn[1])
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
        wo = self.work_ordner
        if wo and wo.startswith('/') and wo.rstrip('/').count('/') >= 1 and wo.rstrip('/') not in ('/home', '/tmp', '/var', '/usr'):
            teile.append(f'rm -rf {shlex.quote(wo)}')   # nur den app-eigenen work-Ordner, nie einen Systempfad
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
            if not os.path.exists(iso):
                de = SPRACHE == 'de'
                self.melde(Gtk.MessageType.ERROR, T['pruef_fehler'],
                           (f"Die gewählte ISO-Datei ist nicht mehr da:\n{iso}\n\n"
                            "Wurde sie gelöscht, verschoben oder auf einen anderen Datenträger\n"
                            "gelegt? Bitte baue den Schnappschuss neu oder wähle in der Liste\n"
                            "eine ISO, die noch vorhanden ist.") if de else
                           (f"The selected ISO file is gone:\n{iso}\n\n"
                            "Was it deleted or moved to another drive? Please rebuild the\n"
                            "snapshot, or pick an ISO from the list that still exists."))
                return
            groesse = os.path.getsize(iso)

            soll, werkzeug = None, 'sha256sum'
            for endung, wz in (('.sha256', 'sha256sum'), ('.md5', 'md5sum')):
                if os.path.exists(iso + endung):
                    with open(iso + endung) as f:
                        felder = f.read().split()
                    if felder:                       # Datei hat Inhalt -> erste Spalte = Soll-Summe
                        soll, werkzeug = felder[0], wz
                        break
                    # LEERE Pruefsummen-Datei: entsteht, wenn der ISO-Bau abbrach (z. B. Platte
                    # voll) — 'sha256sum ISO > ISO.sha256' legt die Datei an, BEVOR die Summe da
                    # ist. NICHT abstuerzen: unten die Summe direkt aus der ISO berechnen.
            if soll is None:
                erg = subprocess.run(['bash', '-c', f'{werkzeug} "{iso}"'],
                                     capture_output=True, text=True).stdout.split()
                if not erg:
                    de = SPRACHE == 'de'
                    self.melde(Gtk.MessageType.ERROR, T['pruef_fehler'],
                               ("Die Prüfsumme der ISO lässt sich nicht berechnen — ist die\n"
                                "ISO-Datei vollständig? (Ein abgebrochener Bau, etwa wegen zu wenig\n"
                                "Speicherplatz, hinterlässt eine unvollständige ISO.)") if de else
                               ("Cannot compute the ISO's checksum — is the ISO file complete?\n"
                                "(An aborted build, e.g. due to low disk space, leaves an\n"
                                "incomplete ISO.)"))
                    return
                soll = erg[0]

            roh = subprocess.run(
                self.root.split() + ['bash', '-c',
                                     f'head -c {groesse} {geraet_pfad} | {werkzeug}'],
                capture_output=True, text=True).stdout.split()
            if not roh:                              # Lesen vom Stick fehlgeschlagen (Rechte, Geraet weg)
                de = SPRACHE == 'de'
                self.melde(Gtk.MessageType.ERROR, T['pruef_fehler'],
                           ("Der Stick lässt sich nicht lesen. Steckt er noch? Wurde die\n"
                            "Passwort-Abfrage bestätigt?") if de else
                           ("Cannot read the stick. Is it still plugged in? Was the password\n"
                            "prompt confirmed?"))
                return
            ist = roh[0]

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

    # ================= Persistenz-Kiste auf dem Stick =================

    def persistenz_anlegen(self, _knopf):
        de = SPRACHE == 'de'
        try:
            lsblk = subprocess.run(['lsblk', '-nd', '-o', 'NAME,TRAN,TYPE,MODEL,SIZE'],
                                   capture_output=True, text=True).stdout
        except Exception as fehler:
            self.melde(Gtk.MessageType.ERROR, 'lsblk', str(fehler)); return
        sticks = [z.split(None, 4) for z in lsblk.splitlines()
                  if len(z.split()) >= 3 and z.split()[1] == 'usb' and z.split()[2] == 'disk']
        if not sticks:
            self.melde(Gtk.MessageType.ERROR, T['kein_stick_titel'], T['kein_stick_text']); return
        s = sticks[0]
        dev = f"/dev/{s[0]}"
        modell = s[3].strip() if len(s) > 3 else ''
        groesse = s[4].strip() if len(s) > 4 else ''
        # lsblk statt blkid: liest LIVE (blkid nutzt einen Cache, der direkt nach dem
        # ISO-Schreiben veraltet sein kann -> faelschlich "kein Schnappschuss").
        blk = subprocess.run(['lsblk', '-no', 'FSTYPE', f'{dev}1'],
                             capture_output=True, text=True).stdout.lower()
        if 'iso9660' not in blk:
            self.melde(Gtk.MessageType.WARNING,
                       'Erst die ISO schreiben' if de else 'Write the ISO first',
                       (f"Auf {dev} ({modell}) liegt noch kein Schnappschuss.\n"
                        "Bitte erst mit »🖊️ Auf USB-Stick schreiben« die ISO aufspielen,\n"
                        "dann hier die Persistenz einrichten.") if de else
                       (f"No snapshot ISO on {dev} ({modell}) yet.\n"
                        "Write the ISO with »🖊️ Write to USB stick« first, then set up persistence."))
            return
        d = Gtk.Dialog(title=T['knopf_persist'], transient_for=self, modal=True)
        d.add_button('Abbrechen' if de else 'Cancel', Gtk.ResponseType.CANCEL)
        d.add_button('Einrichten' if de else 'Set up', Gtk.ResponseType.OK)
        box = d.get_content_area(); box.set_spacing(8); box.set_border_width(12)
        box.add(Gtk.Label(label=f"USB-Stick: {dev}   {modell}   {groesse}", xalign=0))
        box.add(Gtk.Label(
            label=("Damit merkt sich dein Stick, was du änderst — sonst ist nach\n"
                   "jedem Ausschalten alles weg. Im freien Platz NACH der ISO wird\n"
                   "dafür ein Bereich angelegt; die ISO selbst bleibt unangetastet." if de else
                   "This lets your stick remember your changes — otherwise everything is\n"
                   "gone after each shutdown. A storage area is created in the free space\n"
                   "AFTER the ISO; the ISO itself stays untouched."), xalign=0))
        r_all = Gtk.RadioButton.new_with_label(
            None, "Alles merken — System, Programme und Daten (empfohlen)" if de
            else "Remember everything — system, programs and data (recommended)")
        r_home = Gtk.RadioButton.new_with_label_from_widget(
            r_all, "Nur meine persönlichen Daten merken" if de else "Remember only my personal data")
        box.add(r_all); box.add(r_home)
        d.show_all()
        antwort = d.run()
        modus = 'all' if r_all.get_active() else 'home'
        d.destroy()
        if antwort != Gtk.ResponseType.OK:
            return
        self.setze_phase('Persistenz wird eingerichtet ...' if de else 'Setting up persistence ...')
        self.lauf_aktiv = True
        GLib.timeout_add(200, self._puls)
        threading.Thread(target=self._persist_arbeit, args=(dev, modus, de), daemon=True).start()

    def _persist_arbeit(self, dev, modus, de):
        skript = os.path.join(DATEN, 'persistenz', 'persistenz-auf-stick.sh')
        try:
            r = subprocess.run(self.root.split() + ['bash', skript, dev, modus],
                               capture_output=True, text=True)
            if r.returncode == 0:
                self.melde(Gtk.MessageType.INFO,
                           'Persistenz ist eingerichtet' if de else 'Persistence is set up',
                           ((r.stdout.strip() or 'Fertig.') +
                            "\n\nBeim Starten vom Stick im Boot-Menü diesen Eintrag wählen\n"
                            "(das Boot-Menü ist immer englisch — es kann keine Umlaute):\n\n"
                            "»with persistence, keep changes (RECOMMENDED)«\n\n"
                            "Dein Klon merkt sich dann alles. Er arbeitet im Arbeitsspeicher\n"
                            "und speichert einmal beim Herunterfahren — ein bewährter Weg:\n"
                            "flott im Betrieb und schonend für den Stick.\n"
                            "Tipp: ein schneller USB-3-Stick speichert in Sekunden statt Minuten.\n\n"
                            "⚠️ WICHTIG: Immer ordentlich herunterfahren (Menü → Ausschalten)!\n"
                            "Bei hartem Ausschalten ist die Sitzung verloren.") if de else
                           ((r.stdout.strip() or 'Done.') +
                            "\n\nWhen booting the stick, pick this entry from the boot menu:\n\n"
                            "»with persistence, keep changes (RECOMMENDED)«\n\n"
                            "Your clone then remembers everything. It works in RAM and saves\n"
                            "once on shutdown — a proven approach: fast in use and gentle on\n"
                            "the stick. Tip: a fast USB-3 stick saves in seconds, not minutes.\n\n"
                            "⚠️ IMPORTANT: always shut down properly (menu → Shut down)!\n"
                            "Pulling the plug loses the session."))
            else:
                self.melde(Gtk.MessageType.ERROR, 'Fehler' if de else 'Error',
                           (r.stdout + '\n' + r.stderr).strip() or ('Fehlgeschlagen' if de else 'Failed'))
        except Exception as fehler:
            self.melde(Gtk.MessageType.ERROR, 'Fehler' if de else 'Error', str(fehler))
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
