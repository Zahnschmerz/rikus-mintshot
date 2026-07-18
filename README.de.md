# 📸 Rikus Mintshot

**Ein bootfähiger Klon deines laufenden Linux-Mint-Systems — mit einem Klick.**
Verwandelt dein laufendes System in eine startfähige Live-ISO — etwas, wofür
Linux Mint kein eingebautes Werkzeug mitbringt.

Herausgeber: Gilbert Rikus · Kostenlos und quelloffen (GPL-3.0) · Keine Werbung, keine Konten.

*[English version: README.md](README.md)*

---

## Was es macht

Rikus Mintshot verwandelt dein laufendes Linux Mint in eine bootfähige Live-ISO —
mit einem Klick, in einfacher Sprache, ohne Terminal. Du wählst, **wie viel
hineinkommt** — vom nackten System bis zum Voll-Klon:

| Modus | Was drin ist | Wofür |
|---|---|---|
| **Nur System** | das nackte System, ohne dein Home | eine saubere Grundlage zum Weitergeben |
| ⭐ **System + meine Einstellungen** | System **plus deine Einstellungen** — Desktop, Programme, Mails, Backup-Profile — aber **ohne** den Datenberg (Zwischenspeicher, Downloads, Medien, große Modell-Dateien) | ein schlankes System, das sofort brauchbar ist — **die empfohlene Standard-Wahl** |
| **System + Home** | ein voller 1:1-Klon inklusive aller deiner Dateien | ein komplettes Backup / Umzug auf neue Hardware |

Fortgeschrittene können genau festlegen, welche Ordner weggelassen werden.

## Funktionen

- **Ein Klick** — Fortschritt in einfacher Sprache (Schritt 1/2/3 + Prozent), kein Terminal.
- **Auf USB-Stick schreiben** über Linux Mints eigenes Schreibprogramm, mit **eingebauter bit-genauer Kontrolle** — kein Rätselraten, ob der Stick in Ordnung ist.
- **Der Live-Stick startet direkt in dein eigenes Konto und deine Sprache** — kein anonymer Platzhalter-Benutzer.
- **Bootet auch mit eingeschaltetem Secure Boot** — die ISO trägt die Microsoft-signierte shim- + Canonical-signierte GRUB-Kette, so startet sie auf modernen PCs (z. B. mit Windows-Dualboot), *ohne* Secure Boot abzuschalten. Läuft mit an oder aus.
- **Symbol „System installieren" direkt auf dem Live-Schreibtisch** (über Calamares) übernimmt 1:1: keine Benutzer-Anlage, keine erneute Eingabe von Sprache/Zeitzone/Tastatur — alles schon deins.
- **Ehrliche Platz-Vorschau vor dem Bau** — das Programm rechnet aus, wie groß dein Klon *wirklich* wird (statt zu raten) und warnt nur, wenn es tatsächlich eng wird. So bricht kein Bau mehr mittendrin ab.
- **Virtuelle Maschinen mit einem Haken abwählbar** — direkt bei der Auswahl sichtbar. Sie liegen oft auf der Systemplatte und kämen sonst ungefragt mit; das sind schnell 60 GB.
- **Deutsche / englische Oberfläche**, automatisch nach deiner Systemsprache.

## Voraussetzungen

| | |
|---|---|
| System | Linux Mint 22.x (Cinnamon getestet), x86_64 |
| Speicherplatz | ~2× deine Systemgröße, frei |
| Internet | nur für die einmalige Ersteinrichtung |
| Secure Boot | **unterstützt** — bootet mit an *oder* aus, keine BIOS-Änderung nötig |

## Erste Schritte

**Am einfachsten — das .deb-Paket:** Lade `rikus-mintshot_*.deb` von der
[Releases](https://github.com/Zahnschmerz/rikus-mintshot/releases)-Seite herunter und
öffne es mit deiner Paketverwaltung (oder `sudo apt install ./rikus-mintshot_*.deb`).
Danach **Rikus Mintshot** aus dem Anwendungsmenü starten.

**Oder aus dem Quellcode:** `python3 rikus-mintshot.py` starten (oder doppelklicken und
„Ausführen" wählen). Beim ersten Start prüft die App, was fehlt (vor allem der
`refractasnapshot`-Motor, der nicht in Mints Standard-Quellen ist) und bietet an, es
zu installieren — eine Passwort-Abfrage, ein paar Minuten.

Ausführliche Schritt-für-Schritt-Anleitung: **[ANLEITUNG.md](ANLEITUNG.md)** (Deutsch) / **[GUIDE.md](GUIDE.md)** (English).

## Unter der Haube & Danksagung

Aufgebaut auf bewährten, bestehenden Werkzeugen — dieses Projekt verbindet sie mit einer freundlichen Oberfläche:

- **[Refracta](https://sourceforge.net/projects/refracta/)** (refractasnapshot / refractainstaller) — der eigentliche Motor zum Bauen der Schnappschuss-ISO.
- **Debian `live-boot` / `live-config`** — die Live-Boot-Technik.
- **[Calamares](https://calamares.io/)** — der grafische Installer, mit eigener Klon-Konfiguration (keine Benutzer-/Sprach-/Tastatur-Seiten — alles kommt aus deinem Klon).

## Lizenz

GPL-3.0 — frei zu nutzen, studieren, teilen und ändern, für immer. Siehe [LICENSE](LICENSE).
