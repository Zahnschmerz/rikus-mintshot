# Was sich geändert hat / Changelog

Alle Fassungen von Rikus Mintshot, neueste zuerst.
All releases of Rikus Mintshot, newest first.

---

## 6.9 — 20. Juli 2026

**🇩🇪 Zwei Fehler nach dem Wiederherstellen behoben — und eine fehlende Voraussetzung ergänzt.**

- **Behoben: GRUB-Eingabeaufforderung nach dem Wiederherstellen.** Wer einen Klon auf einem Rechner wiederherstellte, auf dem **schon ein Linux Mint installiert war**, blieb beim Start unter Umständen bei `grub` hängen. Ursache: Nach der Installation richtet das Programm die Startreihenfolge der Firmware, damit nicht weiter Windows startet. Dabei suchte es den Eintrag, der zur eigenen Startpartition gehört — und nahm blind **den ersten**, den es fand. Auf einem Rechner mit Vorgeschichte gibt es aber **zwei** Einträge mit derselben Kennung: den alten und den neuen. Erwischte es den alten, toten, schob es genau den nach vorn.
  Jetzt wird der richtige ausgewählt: bevorzugt der Eintrag, **mit dem der Rechner gerade gestartet ist** (besser lässt sich nicht beweisen, dass er funktioniert), sonst der, dessen **Startdatei wirklich vorhanden ist**. Bleibt es unklar, wird **nichts** verändert und alles ins Protokoll geschrieben. Gelöscht wird weiterhin kein Eintrag.
- **Behoben: Nach dem Wiederherstellen ließ sich kein Schnappschuss mehr erstellen.** Bei einem Klon im Modus **„Nur System"** bleibt alles unterhalb von `/home` draußen — also auch der Ordner, in dem gebaut wird. Die Prüfung „bin ich fertig eingerichtet?" sah nur in die Systemordner, meldete deshalb „alles bereit" und bot die Ersteinrichtung nie an. Nur die legt diesen Ordner aber an. Da `/home` dem Verwalter gehört, durfte ihn ein normaler Benutzer auch nicht selbst anlegen — der Knopf **tat einfach nichts**, ohne jede Meldung. Auch eine Neuinstallation half nicht, denn das Paket legt den Ordner ebenfalls nicht an.
  Jetzt gehört der Ordner zur Einrichtungs-Prüfung, und beim Bauen wird er notfalls **mit Verwalter-Rechten angelegt und dem Benutzer übergeben**. Geht auch das nicht, erscheint eine **verständliche Meldung** statt eines toten Knopfes.
- **Ergänzt: `wget` gehört jetzt zu den Voraussetzungen.** Die Ersteinrichtung lädt damit den Motor `refractasnapshot` herunter, aber keine der bisherigen Voraussetzungen brachte es mit. Auf Linux Mint ist es ab Werk vorhanden, weshalb es hier nie auffiel — auf einem schlanken Debian brach die Ersteinrichtung ab, bevor sie begann.

*Mit Dank an Hans-Josef Rausch, der Version 6.7 vollständig durchgetestet und beide Fehler gemeldet hat.*

**🇬🇧 Two bugs after restoring a clone fixed — and a missing requirement added.**

- **Fixed: GRUB prompt after restoring.** Restoring a clone onto a machine that **already had Linux Mint installed** could leave the computer sitting at a `grub` prompt. Cause: after installation the program puts its own firmware entry first, so the machine does not keep booting Windows. It looked for the entry belonging to its own boot partition — and blindly took **the first** one it found. On a machine with a history there are **two** entries with the same identifier, the old one and the new one. If it picked the old, dead one, that is what it moved to the front.
  It now picks the right one: preferably the entry **the machine just booted from** (there is no better proof that it works), otherwise the one whose **boot file actually exists**. If it stays ambiguous, **nothing** is changed and everything is written to the log. No entry is ever deleted.
- **Fixed: no new snapshot could be created after restoring.** A clone made in **"System (root) only"** mode leaves out everything below `/home` — including the folder the build works in. The "am I set up?" check only looked at system folders, reported "all good", and therefore never offered the first-time setup — which is the only thing that creates that folder. Since `/home` belongs to the administrator, a normal user could not create it either, so the button **simply did nothing**, without any message. Reinstalling did not help, because the package does not create that folder either.
  The folder is now part of the setup check, and during a build it is created **with administrator rights and handed to the user** if needed. If even that fails, a **clear message** appears instead of a dead button.
- **Added: `wget` is now a requirement.** The first-time setup uses it to download the `refractasnapshot` engine, but none of the previous requirements pulled it in. Linux Mint ships it by default, which is why it never showed up here — on a slim Debian the setup aborted before it started.

*With thanks to Hans-Josef Rausch, who tested version 6.7 in full and reported both bugs.*

---

## 6.8 — 18. Juli 2026

**🇩🇪 Die Platzprüfung sagt jetzt die Wahrheit, und virtuelle Maschinen lassen sich weglassen.**

- **Behoben: Die Platzprüfung riet nur.** Vor dem Bau schätzte das Programm, wie viel Platz ein Klon braucht („ungefähr so viel, wie dein System belegt"). Diese Schätzung lag in **beide** Richtungen daneben: Auf knappen Systemen zu niedrig — der Bau lief mitten im Komprimieren voll und brach mit „0 Bytes übrig" ab. Auf gut gefüllten Systemen viel zu hoch, was vor **jedem** Bau eine unnötige Schreckwarnung bedeutet hätte.
  Jetzt wird der echte Wert bei `rsync` erfragt (Trockenlauf mit genau der Ausschlussliste des kommenden Baus, etwa 3 Sekunden) und **das Doppelte** verlangt — denn die Systemkopie und das komprimierte Abbild liegen **gleichzeitig** auf der Platte. Dünn belegte Dateien werden mit ihrer echten Größe gezählt; genau daran scheiterte das Schätzen.
  Die Warnung **nennt jetzt auch den Zielordner**. „Es sagt 411 GB, ich habe aber 1,8 TB" kann so nicht mehr passieren — gemeint war der Standard-Ordner, nicht die große Platte.
- **Neu: Virtuelle Maschinen lassen sich abwählen.** Je nach Programm liegen VMs nicht im Persönlichen Ordner, sondern auf der Systemplatte (QEMU/virt-manager nutzt `/var/lib/libvirt/images`). Sie kamen deshalb in **jedem** Modus mit — sogar bei „Nur System" — ohne jede Möglichkeit, sie abzuwählen. Auf dem Entwicklungsrechner waren das 60 GB von 96 GB. Das alte Häkchen suchte nur nach `~/VMs`, VirtualBox nutzt aber `~/VirtualBox VMs`.
  Jetzt gibt es direkt unter der Moduswahl eine eigene Zeile: **„Virtuelle Maschinen mitnehmen"**, standardmäßig angehakt, damit nichts stillschweigend verschwindet. Häkchen weg — und der Klon schrumpft, im Beispiel von 96 GB auf 36 GB. Gefunden werden libvirt, VirtualBox und GNOME Boxes; die Wahl wird gemerkt.
- **Anleitungen ergänzt:** Beide erklären jetzt die VM-Zeile und sagen klar, was schon manchen verwirrt hat: **Daten auf anderen Platten** (alles unter `/media` oder `/mnt`) sind **nie** Teil des Klons. Die *Einstellungen* deines VM-Programms werden mitgeklont — im Klon steht die Maschine also noch in der Liste, ihre Festplattendatei liegt aber auf der zweiten Platte und fehlt dort.

*Mit Dank an Peter Linu aus dem Linux-Mint-Forum, dessen Berichte zu beiden Korrekturen geführt haben.*

**🇬🇧 The space check now tells the truth, and virtual machines can be left out.**

- **Fixed: the space check was only guessing.** Before a build the program *estimated* how much room a clone needs. That guess was wrong in both directions: too small on tight systems — the build ran out of space halfway through compressing and died with "0 bytes remaining" — and far too large on well-filled systems, which would have meant a scary warning before every single build.
  It now asks `rsync` for the real figure (a dry run with the exact exclude list of the upcoming build, about 3 seconds) and requires **double** that, because the system copy and the compressed image sit on the disk at the same time. Sparse files are counted at their true written size, which is where guessing went wrong. The warning also **names the destination folder** now.
- **New: virtual machines can be deselected.** Depending on the program, VMs do not live in your home folder but on the system drive (QEMU/virt-manager uses `/var/lib/libvirt/images`). They therefore came along with *every* mode — even "System (root) only" — with no way to deselect them. The old checkbox only looked for `~/VMs`, while VirtualBox uses `~/VirtualBox VMs`.
  There is now a dedicated line right below the mode choice: **"Include virtual machines"**, ticked by default so nothing disappears silently. Untick it and the clone drops — 96 GB to 36 GB in the case above. It finds libvirt, VirtualBox and GNOME Boxes, and your choice is remembered.
- **Documentation:** both guides now explain the VM line, and spell out something that has confused people: data on other drives (anything under `/media` or `/mnt`) is **never** part of the clone.

*Thanks to Peter Linu in the Linux Mint forums, whose reports led to both fixes.*

---

## 6.7 — 17. Juli 2026

**🇩🇪 Die erste Fassung auf GitHub.** Ein großes Update gegenüber 5.5 — mit einer neuen Persistenz-Funktion, einem aufgeräumten Boot-Menü und mehreren Korrekturen für Probleme, die echte Nutzer gemeldet hatten.

**Neu:**
- **Persistenz** — deine Änderungen (Dateien, WLAN, Einstellungen) bleiben auf dem USB-Stick, ganz ohne feste Installation. Läuft im Arbeitsspeicher und speichert einmal beim Herunterfahren.
  💡 Nimm einen schnellen **USB-3-Stick** — wie flott gespeichert wird, hängt allein am Stick.
- **„Reboot into Firmware Setup (BIOS/UEFI)"** im Boot-Menü — kein Suchen mehr nach der (je nach Hersteller anderen) BIOS-Taste. Praktisch bei Dualboot.
- **Aufgeräumtes Boot-Menü:** nur noch zwei Einträge (starten / mit Persistenz starten), alles englisch.

**Behoben:**
- **Kernel-Panic auf manchen Rechnern** — der Live-Start wird jetzt korrekt in die Startdatei der ISO eingebaut.
- **„wouldn't verify" auf dem Stick** — die Prüfsummendatei wird zuverlässig geschrieben, und die eingebaute Prüfung stürzt bei leerer Prüfsumme nicht mehr ab.
- **WLAN auf fremder Hardware** — das gespeicherte WLAN verbindet sich jetzt auch, wenn die Netzwerkkarte auf dem anderen Rechner anders heißt.
- **Dualboot: „er startet einfach Windows"** — Mint wird als Standard gesetzt und das Boot-Menü angezeigt. Bei mehreren Platten kann einmalig noch das BIOS nötig sein (steht in der Anleitung — das ist normal und jetzt einen Klick entfernt, siehe Menüpunkt oben).
- **Fehlende `ping`-Rechte** im Klon — behoben (Dateimerkmale bleiben erhalten).
- **Aufgeblähter Klon** — ein zweites Betriebssystem und Swap-Dateien bleiben jetzt automatisch draußen.

**Hinweise:** Startet mit **Secure Boot an oder aus**. Oberfläche **deutsch oder englisch**, automatisch nach Systemsprache.

**🇬🇧 The first release on GitHub.** A big update over 5.5 — with a new **persistence** feature, a cleaner boot menu, and several fixes for problems real users reported.

**New:**
- **Persistence** — keep your changes (files, Wi-Fi, settings) on the USB stick without a permanent install. Works in RAM, saves once on shutdown. 💡 Use a fast **USB-3 stick**.
- **"Reboot into Firmware Setup (BIOS/UEFI)"** entry in the boot menu — no more hunting for the vendor-specific BIOS key.
- Cleaner boot menu: just two entries (start / start with persistence), all English.

**Fixed:**
- **Kernel panic on some machines** — the live boot component is now rebuilt into the ISO's start file.
- **"Wouldn't verify" on the stick** — the checksum file is written reliably, and the built-in check no longer crashes on an empty checksum.
- **Wi-Fi on foreign hardware** — the saved Wi-Fi now connects even when the network card is named differently on another PC.
- **Dual-boot: "it just booted Windows"** — Mint is now the default and the boot menu is shown; on multi-disk setups you may still need the BIOS once.
- **Missing `ping` permissions** in the clone — fixed (file attributes preserved).
- **Clone bloat** — a second OS and swap files are now left out automatically.

**Notes:** Boots with **Secure Boot on or off**. Interface in **German or English**, chosen automatically.

---

## Vor der Veröffentlichung auf GitHub / Before the GitHub release

**🇩🇪** Die Fassungen 5.0 bis 6.6 entstanden zwischen dem 8. und 17. Juli 2026 und wurden nicht als Release auf GitHub angeboten (die kurzzeitig veröffentlichte 5.5 wurde durch 6.7 ersetzt). Der Vollständigkeit halber der Weg dorthin:

**🇬🇧** Releases 5.0 to 6.6 were built between 8 and 17 July 2026 and were not offered as GitHub releases (5.5 was briefly published and then replaced by 6.7). For completeness, the path there:

| Fassung | Datum | Was dazukam / What changed |
|---|---|---|
| **6.0 – 6.6** | 16.–17.07. | Persistenz, dann die oben genannten Nutzer-Korrekturen · *persistence, then the user fixes listed above* |
| **5.5** | 14.07. | Umbenennung von „Linux Mint Snapshot" zu **Rikus Mintshot** · *renamed* |
| **5.4** | 14.07. | Drei Modi: **Nur System · System + meine Einstellungen · System + Persönlicher Ordner**; Feinauswahl im Bereich „Für Fortgeschrittene" · *three modes* |
| **5.3** | 13.07. | Freie Ordnerwahl, 13 Fehlerkorrekturen, rollbares Fenster · *free folder selection, 13 fixes, scrollable window* |
| **5.2** | 11.07. | Erster Persistenz-Versuch — **wieder zurückgenommen**, kam später als 6.0 · *first persistence attempt, reverted* |
| **5.1** | 10.07. | **Secure Boot** · *Secure Boot support* |
| **5.0** | 08.07. | Erste Fassung · *first release* |

---

**Alle Fassungen zum Herunterladen / All releases:** https://github.com/Zahnschmerz/rikus-mintshot/releases
**Webseite / Website:** https://snapshot.rikus.info
**Schwesterprogramm / Sister project:** [Rikus Zram](https://zram.rikus.info) — zram, swappiness und Swap-Dateien mit Schiebereglern statt Terminal.
