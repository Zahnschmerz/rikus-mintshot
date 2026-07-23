# Was sich geändert hat / Changelog

Alle Fassungen von Rikus Mintshot, neueste zuerst.
All releases of Rikus Mintshot, newest first.

---

## 7.2 — 23. Juli 2026

**🇩🇪 Wenn die ISO nicht Secure-Boot-fähig wird, sagt das Programm es jetzt — statt still eine normale ISO zu liefern.**

- **Behoben: stiller Ausfall beim Secure-Boot-Umbau.** Damit die ISO auch mit eingeschaltetem Secure Boot startet, baut das Programm sie am Ende mit einer signierten Startkette neu zusammen. Schlug dieser Schritt fehl, lieferte das Programm **stillschweigend** eine normale ISO — man merkte es erst, wenn ein fremder Rechner mit Secure Boot den Stick abwies. Jetzt erscheint eine **klare Warnung** mit dem Grund (fehlende Bausteine, zu wenig Platz oder ein anderer Fehler) und was zu tun ist.
- **Behoben: der Umbau scheiterte bei großen ISOs am Platz.** Beim Neu-Zusammenbauen liegen kurz die **alte und die neue** ISO gleichzeitig auf der Platte — bei einer großen ISO (etwa „System + Home") wird der Platz dann leicht knapp. Bisher brach der Schritt mitten im Packen ab. Jetzt prüft das Programm den Platz **vorher** und meldet klar, wie viel fehlt, damit man Platz freimachen (oder einen anderen Ablageort wählen) und neu bauen kann. Die fertige normale ISO bleibt dabei unversehrt.

**🇬🇧 If the ISO can't be made Secure-Boot-capable, the program now says so — instead of silently handing you a normal ISO.**

- **Fixed: silent failure of the Secure-Boot step.** To make the ISO start with Secure Boot enabled, the program rebuilds it at the end with a signed boot chain. If that step failed, the program **silently** produced a normal ISO — you only found out when a machine with Secure Boot rejected the stick. Now a **clear warning** appears with the reason (missing building blocks, too little space, or another error) and what to do.
- **Fixed: the step ran out of space on large ISOs.** Rebuilding briefly keeps the **old and the new** ISO on disk at the same time — on a large ISO (e.g. "System + Home") space can run short. It used to abort mid-pack; now the program checks space **beforehand** and reports exactly how much is missing, so you can free space (or pick another destination) and rebuild. The finished normal ISO is left intact.

---

## 7.1 — 23. Juli 2026

**🇩🇪 Persistenz ließ sich auf vielen Sticks nicht einrichten („Invalid partition data!").**

- **Behoben: „💾 Persistenz einrichten" brach mit „Invalid partition data!" ab.** Zum Anlegen der Persistenz-Kiste benutzte das Programm ein Werkzeug (`sgdisk`), das nur mit **einer** Sorte Partitionstabelle umgehen kann („GPT"). Sticks, die mit Linux Mints eigenem USB-Stick-Ersteller beschrieben wurden, haben aber die **andere** Sorte („MBR") — dort verweigerte das Werkzeug die Arbeit, und es entstand keine Persistenz. Ob der Fehler auftrat, hing davon ab, **womit** der Stick beschrieben wurde, was ihn schwer greifbar machte.
  Jetzt erkennt das Programm, welche Sorte der Stick hat, und nimmt für jede das passende Werkzeug. **Beide Fälle sind an nachgebauten Sticks geprüft:** Die Persistenz-Partition entsteht im freien Platz hinter der ISO, die ISO selbst bleibt unangetastet.
- **Eine Abhängigkeit kam dazu: `fdisk`** — daraus stammt das Werkzeug (`sfdisk`), das die Kiste auf MBR-Sticks anlegt. Auf Linux Mint ist es ohnehin vorhanden; auf einem abgespeckten System wird es jetzt sauber mitinstalliert, statt dass die Persistenz-Einrichtung dort still nichts täte.

**🇬🇧 Persistence could not be set up on many sticks ("Invalid partition data!").**

- **Fixed: "💾 Set up persistence" aborted with "Invalid partition data!".** To create the persistence box, the program used a tool (`sgdisk`) that only handles **one** kind of partition table ("GPT"). Sticks written with Linux Mint's own USB stick writer have the **other** kind ("MBR"), where the tool refused to work and no persistence was created. Whether the error appeared depended on **how** the stick was written, which made it hard to pin down.
  The program now detects which kind the stick has and uses the matching tool for each. **Both cases are verified on rebuilt sticks:** the persistence partition is created in the free space behind the ISO, leaving the ISO itself untouched.
- **One dependency was added: `fdisk`** — it provides the tool (`sfdisk`) that creates the box on MBR sticks. Always present on Linux Mint anyway; on a slim system it is now pulled in properly instead of persistence setup silently doing nothing.

---

## 7.0 — 21. Juli 2026

**🇩🇪 Nach dem Wiederherstellen war der Fernzugang (SSH) still tot.**

- **Behoben: Im wiederhergestellten Klon fehlten die SSH-Rechnerschlüssel** — dadurch startete der SSH-Dienst gar nicht erst (`sshd: no hostkeys available -- exiting`). Man merkt davon **nichts**: Am Rechner selbst läuft alles normal, und erst wenn man sich von außen verbinden will, ist der Zugang tot — also ausgerechnet im Notfall.
- **Warum das passierte:** Der Schnappschuss lässt die Schlüssel **absichtlich** weg. Das ist auch richtig so — sonst hätten alle Klone dieselben Schlüssel und könnten sich füreinander ausgeben. In der Ausschlussliste steht dazu „New ones will be generated upon live boot". Das stimmt aber **nur für den Live-Start vom Stick**. Nach einer **festen Installation** erzeugt sie niemand nach.
- **Der Fix:** Ein kleiner Dienst prüft bei jedem Start, ob Schlüssel vorhanden sind, erzeugt sie sonst frisch und startet den SSH-Dienst nach. Auf einem System, das seine Schlüssel hat, tut er **nichts**. Es werden immer **neue** Schlüssel erzeugt, nie welche kopiert — die Trennung zwischen Quelle und Klon bleibt gewahrt.
- **Die Ersteinrichtung meldet es jetzt**, wenn dieser Schutz fehlt.
- **Eine Abhängigkeit kam dazu: `openssh-client`** — daraus stammt das Werkzeug, das die Schlüssel erzeugt. Auf Linux Mint ist es ohnehin immer vorhanden; auf einem abgespeckten System wird es jetzt sauber mitinstalliert, statt dass der Schutz still nichts täte.
- Gefunden am ersten echten Dauersystem, das aus einem Klon entstanden ist: Ein mit 6.11 gebauter Klon läuft seit dem 21.07. als Alltagssystem auf einem anderen Laptop. Dort fiel auf, dass zwei von drei Fernzugangswegen tot waren — die Ursache war dieselbe.

**🇬🇧 After restoring, remote access (SSH) was silently dead.**

- **Fixed: the restored clone had no SSH host keys** — so the SSH service never started (`sshd: no hostkeys available -- exiting`). You notice nothing locally; only a connection attempt from outside reveals it — exactly when you need it most.
- **Why:** The snapshot deliberately excludes host keys (otherwise every clone would share the same ones and could impersonate each other). The exclude list says „New ones will be generated upon live boot" — true for a **live** boot, but nobody regenerates them after a **permanent install**.
- **The fix:** A small service checks at every boot whether host keys exist, generates fresh ones if not, and restarts SSH. On a system that has its keys it does **nothing**. Keys are always generated, never copied — source and clone stay separate.
- **First-run setup now reports** when this safeguard is missing.
- **One dependency was added: `openssh-client`** — it provides the tool that generates the keys. Always present on Linux Mint anyway; on a slim system it is now pulled in properly instead of the safeguard silently doing nothing.

---

## 6.11 — 21. Juli 2026

**🇩🇪 Das Programm sagt jetzt Bescheid, wenn es eine neuere Fassung gibt.**

- **Neu: Update-Hinweis.** Beim Start schaut das Programm einmal nach, ob auf GitHub eine neuere Fassung liegt. Wenn ja, erscheint unter dem Titel eine kleine grüne Zeile: „🔔 Version X ist verfügbar — ansehen", mit Link zur Download-Seite. **Es wird nichts heruntergeladen und nichts installiert** — nur der Hinweis.
- **Warum das nötig war:** Das Programm kommt als `.deb` über GitHub und ist damit *keine* apt-Quelle. `apt update` erfährt also nie von einer neuen Fassung. Wie sehr das fehlt, zeigte ein Tester, der Fehler zu Fassung 6.7 meldete, als 6.8 längst veröffentlicht war.
- **Was der Hinweis NICHT tut:** Er hält das Fenster nicht auf (eigener Hintergrund-Vorgang mit 4-Sekunden-Grenze — gemessen: das Fenster stand nach 450 ms, während die Abfrage noch ins Leere lief). Er stürzt nicht ab (schlägt etwas fehl, bleibt die Zeile einfach weg). Er braucht **kein zusätzliches Paket**. Und ohne Internet erscheint er gar nicht — das ist der Normalfall, kein Fehler.
- **Abschaltbar:** `touch ~/.config/rikus-mintshot/kein-update-hinweis` — dann fragt das Programm gar nicht mehr nach. Steht in beiden Anleitungen.

**🇬🇧 The program now tells you when a newer version is out.**

- **New: update hint.** At startup the program checks once whether a newer release exists on GitHub. If so, a small green line appears below the title: „🔔 Version X is available — view", linking to the download page. **Nothing is downloaded and nothing is installed.**
- **Why:** The program ships as a `.deb` via GitHub and is therefore *not* an apt source, so `apt update` never learns about newer versions. A tester reported bugs against 6.7 while 6.8 had long been released.
- **What it does not do:** It never blocks the window (background check with a 4-second limit — measured: window up after 450 ms while the request was still running into nothing), it never crashes (on any failure the line simply stays hidden), and it needs **no extra package**. Without internet it does not appear at all.
- **Can be switched off:** `touch ~/.config/rikus-mintshot/kein-update-hinweis`. Documented in both guides.

---

## 6.10 — 21. Juli 2026

**🇩🇪 Bei Ordnernamen mit `&` blieb die Ablage-Zeile leer.**

- **Behoben: Die Zeile „Ablageort: … · Freier Platz: …"** unten im Fenster war **vollständig leer**, wenn im Pfad ein kaufmännisches Und stand (z. B. `Musik & Filme`) — ohne Fehlermeldung. Dasselbe passierte bei spitzen Klammern (`Foto<2026>`). Ursache: Die Zeile darf Formatierung enthalten, und dort haben diese Zeichen eine Sonderbedeutung; ein einzelnes `&` lässt die ganze Zeile verwerfen. **Vier andere Stellen im Programm waren dagegen abgesichert, nur diese eine nicht.** Es ging dabei nichts kaputt — die ISO wurde weiterhin korrekt gebaut, man sah nur nicht mehr, wohin.
- **Das Paket wird jetzt sauberer gebaut** (neues `bauen.sh` im Projekt):
  - **`Installed-Size` wird eingetragen** — vorher meldete apt beim Installieren „0 B zusätzlich belegt".
  - **Prüfsummen der Dateien (`md5sums`)** liegen bei, damit `dpkg -V`/`debsums` das Paket überprüfen können.
  - **Das Änderungsprotokoll** liegt jetzt auch als `changelog.gz` bei, wo apt es findet.
  - **Mit `xz` gepackt statt `zstd`** — zstd-Pakete können ältere Systeme nicht öffnen.
  - Die Prüfsummen-Datei enthält nur noch den bloßen Dateinamen, damit `sha256sum -c` bei jedem funktioniert.

**🇬🇧 With folder names containing `&`, the location line stayed empty.**

- **Fixed: the line "Location: … · Free space: …"** at the bottom of the window was **completely empty** when the path contained an ampersand (e.g. `Musik & Filme`) — with no error message. The same happened with angle brackets (`Foto<2026>`). Cause: the line may contain formatting, where those characters have a special meaning; a single `&` makes the whole line be discarded. **Four other places in the program were guarded, this one was not.** Nothing was damaged — the ISO was still built correctly, you just could not see where it went.
- **The package is now built more cleanly** (new `bauen.sh` in the project): `Installed-Size` is set (apt used to report "0 B"), `md5sums` are included, the changelog ships as `changelog.gz`, it is packed with **xz instead of zstd** (older systems cannot open zstd), and the checksum file contains only the bare filename.

---

## 6.9 — 20. Juli 2026

**🇩🇪 Zwei Fehler nach dem Wiederherstellen behoben — und eine fehlende Voraussetzung ergänzt.**

- **Behoben: GRUB-Eingabeaufforderung nach dem Wiederherstellen.** Wer einen Klon auf einem Rechner wiederherstellte, auf dem **schon ein Linux Mint installiert war**, blieb beim Start unter Umständen bei `grub` hängen. Ursache: Nach der Installation richtet das Programm die Startreihenfolge der Firmware, damit nicht weiter Windows startet. Dabei suchte es den Eintrag, der zur eigenen Startpartition gehört — und nahm blind **den ersten**, den es fand. Auf einem Rechner mit Vorgeschichte gibt es aber **zwei** Einträge mit derselben Kennung: den alten und den neuen. Erwischte es den alten, toten, schob es genau den nach vorn.
  Jetzt wird der richtige ausgewählt: bevorzugt der Eintrag, **mit dem der Rechner gerade gestartet ist** (besser lässt sich nicht beweisen, dass er funktioniert), sonst der, dessen **Startdatei wirklich vorhanden ist**. Bleibt es unklar, wird **nichts** verändert und alles ins Protokoll geschrieben. Gelöscht wird weiterhin kein Eintrag.
- **Behoben: Nach dem Wiederherstellen ließ sich kein Schnappschuss mehr erstellen.** Bei einem Klon im Modus **„Nur System"** bleibt alles unterhalb von `/home` draußen — also auch der Ordner, in dem gebaut wird. Die Prüfung „bin ich fertig eingerichtet?" sah nur in die Systemordner, meldete deshalb „alles bereit" und bot die Ersteinrichtung nie an. Nur die legt diesen Ordner aber an. Da `/home` dem Verwalter gehört, durfte ihn ein normaler Benutzer auch nicht selbst anlegen — der Knopf **tat einfach nichts**, ohne jede Meldung. Auch eine Neuinstallation half nicht, denn das Paket legt den Ordner ebenfalls nicht an.
  Jetzt gehört der Ordner zur Einrichtungs-Prüfung, und beim Bauen wird er notfalls **mit Verwalter-Rechten angelegt und dem Benutzer übergeben**. Geht auch das nicht, erscheint eine **verständliche Meldung** statt eines toten Knopfes.
- **Ergänzt: `wget` gehört jetzt zu den Voraussetzungen.** Die Ersteinrichtung lädt damit den Motor `refractasnapshot` herunter, aber keine der bisherigen Voraussetzungen brachte es mit. Auf Linux Mint ist es ab Werk vorhanden, weshalb es hier nie auffiel — auf einem schlanken Debian brach die Ersteinrichtung ab, bevor sie begann.
- **Neu: Ein zweiter Weg für dein gespeichertes WLAN.** Bisher lagen die WLAN-Zugangsdaten im Klon nur an **einer einzigen Stelle**. Aus dieser Datei baut das System beim Start die eigentliche Verbindung. Geht dabei irgendetwas schief, ist das WLAN weg — und zwar auf besonders tückische Weise: Die Karte läuft, alle Netze werden gefunden, **nur das eigene Netz fehlt**, ohne Fehlermeldung.
  Jetzt legt der Bau zusätzlich eine **Sicherheitskopie** deiner WLAN- und Kabel-Verbindungen in den Klon. Beim Start prüft der Klon, ob das System sie kennt — und stellt **nur die fehlenden** wieder her, samt Passwort und gelöst von der Netzwerkkarte des Ursprungsrechners. Ist alles vorhanden, geschieht **nichts**: keine doppelten Einträge, kein Neustart des Netzes.
- **Behoben: Die Platzprüfung meldete viel zu viel.** Seit 6.8 misst das Programm den Platzbedarf, statt zu raten — es benutzte dabei aber nur die Ausschlussliste. Der Bau lässt jedoch **drei weitere Ordner** aus, die dort gar nicht stehen: den Arbeitsordner, den Ordner mit den fertigen Abbildern und den Ordner für die Startdateien. Wer schon Abbilder gesammelt hatte, bekam sie mitgezählt — auf dem Entwicklungsrechner meldete die Warnung **102,7 GB für einen Klon, der am Ende 15,6 GB groß war**.
  Die Messung liest diese drei Ordner jetzt aus **derselben Konfigurationsdatei, die der Bau gleich darauf benutzt**. Damit können Messung und Bau nicht mehr auseinanderlaufen, auch wenn der Ablageort gewechselt wird.

*Mit Dank an Hans-Josef Rausch, der Version 6.7 vollständig durchgetestet und beide Fehler gemeldet hat.*

**🇬🇧 Two bugs after restoring a clone fixed — and a missing requirement added.**

- **Fixed: GRUB prompt after restoring.** Restoring a clone onto a machine that **already had Linux Mint installed** could leave the computer sitting at a `grub` prompt. Cause: after installation the program puts its own firmware entry first, so the machine does not keep booting Windows. It looked for the entry belonging to its own boot partition — and blindly took **the first** one it found. On a machine with a history there are **two** entries with the same identifier, the old one and the new one. If it picked the old, dead one, that is what it moved to the front.
  It now picks the right one: preferably the entry **the machine just booted from** (there is no better proof that it works), otherwise the one whose **boot file actually exists**. If it stays ambiguous, **nothing** is changed and everything is written to the log. No entry is ever deleted.
- **Fixed: no new snapshot could be created after restoring.** A clone made in **"System (root) only"** mode leaves out everything below `/home` — including the folder the build works in. The "am I set up?" check only looked at system folders, reported "all good", and therefore never offered the first-time setup — which is the only thing that creates that folder. Since `/home` belongs to the administrator, a normal user could not create it either, so the button **simply did nothing**, without any message. Reinstalling did not help, because the package does not create that folder either.
  The folder is now part of the setup check, and during a build it is created **with administrator rights and handed to the user** if needed. If even that fails, a **clear message** appears instead of a dead button.
- **Added: `wget` is now a requirement.** The first-time setup uses it to download the `refractasnapshot` engine, but none of the previous requirements pulled it in. Linux Mint ships it by default, which is why it never showed up here — on a slim Debian the setup aborted before it started.
- **New: a second route for your saved Wi-Fi.** Until now the Wi-Fi credentials lived in the clone in **one single place**. From that file the system builds the actual connection at boot. If anything goes wrong there, the Wi-Fi is gone — in a particularly deceptive way: the card works, every network shows up, **only your own network is missing**, with no error message.
  The build now also puts a **backup copy** of your Wi-Fi and wired connections into the clone. At boot the clone checks whether the system knows them and restores **only the missing ones**, password included and detached from the source machine's network card. If everything is there, **nothing happens**: no duplicate entries, no network restart.
- **Fixed: the space check reported far too much.** Since 6.8 the program measures the space a clone needs instead of guessing — but it only used the exclude list. The build, however, leaves out **three further folders** that are not in that list: the work folder, the folder holding finished images, and the folder for the boot files. Anyone who had collected images got them counted in — on the development machine the warning announced **102.7 GB for a clone that ended up 15.6 GB**.
  The measurement now reads those three folders from **the same configuration file the build uses moments later**, so measurement and build can no longer drift apart, even if the destination folder changes.

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
