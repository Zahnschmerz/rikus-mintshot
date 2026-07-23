# Rikus Mintshot — Anleitung (Deutsch)

**Herausgeber: Gilbert Rikus · Lizenz: GPL-3 · kostenlos**
*(Version und Lizenztext stehen jederzeit im Programm unter „ℹ️ Über".)*

Dieses Programm erstellt mit einem Klick eine **startfähige Kopie deines
laufenden Linux-Mint-Systems** — etwas, wofür Linux Mint kein eigenes Werkzeug
mitbringt. Die ISO kannst du auf einen USB-Stick schreiben, davon jeden PC starten
und dein System mit einem Doppelklick fest installieren.

**Du entscheidest dabei selbst, wie viel mitkommt** — vom nackten System bis
zum vollständigen Klon mit all deinen Dateien. Nach der Installation
funktioniert alles wie gewohnt, ohne dass du etwas neu einrichten musst.

---

## 1. Was du brauchst

| | |
|---|---|
| Betriebssystem | Linux Mint 22.x (Cinnamon getestet) |
| Freier Platz | etwa **doppelt so viel wie dein System belegt** |
| USB-Stick | mindestens so groß wie die fertige ISO |
| Internet | nur für die einmalige Ersteinrichtung |

---

## 2. Programm installieren

**Am einfachsten — das fertige Paket:**

1. Lade `rikus-mintshot*.deb` von der
   [Releases-Seite](https://github.com/Zahnschmerz/rikus-mintshot/releases) herunter.
2. Doppelklick auf die Datei → deine Paketverwaltung öffnet sich → **„Installieren"**.
   *(Oder im Terminal: `sudo apt install ~/Downloads/rikus-mintshot*.deb`)*

   💡 **Tipp:** Liegt die Datei woanders? Dann im Download-Ordner **Rechtsklick →
   „Im Terminal öffnen"** — dort bist du automatisch am richtigen Ort.

   🔒 **Datei prüfen (freiwillig):** Im Download-Ordner **Rechtsklick → „Im Terminal
   öffnen"**, dann tippe `sha256sum rikus-mintshot*.deb`. Die lange Zahl, die erscheint,
   muss mit der auf der [Releases-Seite](https://github.com/Zahnschmerz/rikus-mintshot/releases)
   (und auf der Webseite) übereinstimmen — dann ist die Datei echt und unbeschädigt.
   Du brauchst dafür **nur diese eine Datei**.
3. Danach findest du **Rikus Mintshot** dauerhaft im **Startmenü**
   (mit eigenem Kamera-Symbol).

**Oder aus dem Quellcode:** Ordner entpacken und `python3 rikus-mintshot.py`
starten (oder doppelklicken → „Ausführen" wählen).

**Beim allerersten Start** prüft das Programm, ob alle Bausteine vorhanden sind.
Fehlt etwas, erscheint der Knopf **„🔧 Jetzt einrichten"**:

- Klick darauf → eine Liste zeigt, was installiert wird.
- Bestätige → dein **Passwort** wird einmal abgefragt (das ist normal:
  Systembausteine brauchen Verwaltungsrechte).
- Die Einrichtung dauert wenige Minuten. Danach erscheint
  **„✅ Einrichtung abgeschlossen"** — fertig, das war einmalig. Dabei wird
  das Programm auch fest ins System eingebaut, damit es in jedem Klon
  automatisch mit dabei ist.

---

## 3. Schnappschuss (ISO) erstellen

### Zuerst: Wie viel soll mitkommen?

Im Hauptfenster wählst du mit **einem Klick** aus drei Möglichkeiten:

| Auswahl im Programm | Was mitkommt | Wofür gedacht |
|---|---|---|
| **Nur System (root)**<br>*— ganz nackt, ohne persönliche Einstellungen* | nur das System selbst — **kein** persönlicher Ordner, keine Konten, keine Daten | eine saubere Grundlage, die du **gefahrlos weitergeben** kannst |
| ⭐ **System + meine Einstellungen**<br>*— schlank & brauchbar (empfohlen)* | System **plus deine Einstellungen**: Schreibtisch, Programme, Mails, Browser, gespeicherte Anmeldungen — **ohne** den großen Datenberg (Zwischenspeicher, Downloads, Bilder, Videos, Musik) | **die empfohlene Wahl:** klein, aber sofort brauchbar — alles ist eingerichtet wie gewohnt |
| **System + Home**<br>*— alles komplett (deine Dateien, Mails & Konto)* | **wirklich alles** — ein vollständiger 1:1-Klon inklusive all deiner Dateien | komplettes Backup oder Umzug auf einen neuen Rechner |

**Wenn du unsicher bist:** Nimm die mittlere Wahl (⭐ **System + meine Einstellungen**).
Sie ist voreingestellt und für die meisten die richtige.

> 🔒 **Wichtig bei den unteren beiden Wahlmöglichkeiten:** Sobald deine
> Einstellungen oder Dateien mitkommen, enthält die ISO **dein Konto und deine
> gespeicherten Zugänge**. Solche Sticks sicher verwahren und **nicht an Fremde
> weitergeben!** Nur **„Nur System (root)"** ist frei von persönlichen Daten.

### Virtuelle Maschinen

Hast du virtuelle Maschinen (VirtualBox, GNOME Boxes oder QEMU/virt-manager),
erscheint direkt unter der Auswahl eine **eigene Zeile**:

> ☑ **Virtuelle Maschinen mitnehmen** — sie sind oft sehr groß (schnell 60 GB und mehr)

**Der Haken ist gesetzt** — deine Maschinen kommen also mit, wie alles andere.
**Nimm den Haken weg**, wenn du sie draußen lassen willst. Das spart schnell
50 GB und mehr. Deine Wahl wird gemerkt; du musst sie nur einmal treffen.

> 💡 **Warum eine eigene Zeile?** Virtuelle Maschinen liegen je nach Programm
> **nicht** in deinem Persönlichen Ordner, sondern auf der Systemplatte
> (QEMU/virt-manager legt sie z. B. unter `/var/lib/libvirt/images` ab). Sie
> kommen deshalb bei **allen drei** Wahlmöglichkeiten mit — auch bei
> „Nur System". Ohne diese Zeile würdest du sie ungewollt mitschleppen.

> ⚠️ **Was NIE mitkommt — egal was du wählst:** Daten auf **anderen Platten**.
> Alles, was unter `/media` oder `/mnt` eingehängt ist (externe Festplatten,
> USB-Sticks, Netzlaufwerke, Cloud-Ordner), bleibt draußen. Das ist Absicht —
> sonst würde jede angesteckte Platte den Klon aufblähen.
> **Achtung, häufige Verwirrung:** Liegt deine virtuelle Maschine auf einer
> **zweiten Platte**, ist sie **nicht** im Klon — auch wenn der Haken gesetzt
> ist. Die Einstellungen des VM-Programms werden aber mitgeklont. Im Klon
> startet dein VM-Programm dann und **listet die Maschine auf, aber die
> Festplatten-Datei dazu fehlt.**

**Für Fortgeschrittene:** Unter **„⚙️ Für Fortgeschrittene: einzelne Ordner
weglassen"** kannst du zusätzlich genau bestimmen, was draußen bleibt
(Häkchen = bleibt draußen), zum Beispiel Steam-Spiele oder Flatpak-Programme.
Mit **„➕ Weiteren Ordner weglassen …"** kommt jeder beliebige Ordner dazu.

### Dann: Schnappschuss bauen

1. Klicke auf **„📸 Schnappschuss jetzt erstellen"**.
2. Das Programm arbeitet nun in **3 Schritten** (mit Fortschrittsbalken):
   - Schritt 1: System kopieren *(dauert am längsten)*
   - Schritt 2: Komprimieren *(mit Prozent-Anzeige)*
   - Schritt 3: Startfähige ISO bauen
   - **Gesamtdauer: etwa 15–25 Minuten** (je nach Wahl oben und Rechner).
     Du kannst nebenbei weiterarbeiten; selbst wenn du das Fenster schließt,
     läuft der Bau weiter.
3. Am Ende meldet das Programm **„✅ Schnappschuss fertig!"** — die ISO liegt
   in der Liste „Fertige Abbilder".

---

## 4. Auf den USB-Stick schreiben

1. Stecke den USB-Stick ein. **Alles auf dem Stick wird gelöscht!**
2. Wähle in der Liste deine ISO aus und klicke **„🖊️ Auf USB-Stick schreiben"**.
3. Es öffnet sich das Mint-eigene Schreibprogramm: Stick auswählen →
   **„Schreiben"** → warten (5–15 Minuten, je nach Stick).

## 5. Stick kontrollieren (sehr empfohlen!)

1. Stick eingesteckt lassen, in der Liste dieselbe ISO auswählen.
2. Klicke **„🔍 Stick kontrollieren (Prüfsumme)"**.
3. Das Programm vergleicht den Stick **Bit für Bit** mit der ISO
   (dauert einige Minuten). Am Ende steht entweder
   **„✅ Stick ist PERFEKT"** — oder eine klare Fehlermeldung
   (dann neu schreiben oder anderen Stick nehmen).

---

## 6. Vom Stick starten

1. Stick einstecken, Rechner **neu starten**.
2. Direkt beim Einschalten das **Boot-Menü** öffnen — meistens mit **F12**
   (je nach Hersteller auch **F2**, **F8**, **F10** oder **Esc**).
3. Den **USB-Stick** aus der Liste wählen.
4. Im Startmenü den **ersten Eintrag** („Linux Mint (Standard)") wählen. Das Menü
   hat bewusst nur **zwei Start-Einträge** — **Standard** und **mit Persistenz**
   (Punkt 7) — plus einen Eintrag **„Reboot into Firmware Setup (BIOS/UEFI)"**, der
   dich bequem ins BIOS bringt (praktisch bei Dualboot, siehe Punkt 8).
   *(Das Boot-Menü ist immer englisch — es kann keine Umlaute darstellen.)*
5. Nach etwa 1–2 Minuten erscheint der Schreibtisch. Hast du **deine
   Einstellungen** mitgenommen, startet das Live-System direkt in **deinem
   eigenen Benutzerkonto** — mit deinen Symbolen und Programmen, genau wie du
   es kennst. Nichts an deinem echten Rechner wird verändert, solange du nicht
   installierst.

> ✅ **Secure Boot:** Der Stick startet auch mit **eingeschaltetem Secure Boot** —
> du musst im BIOS nichts umstellen. Die ISO enthält eine von Microsoft und
> Canonical signierte Startkette, die moderne PCs (auch mit Windows daneben)
> akzeptieren. Er läuft mit Secure Boot an oder aus.

> 💡 **Auf einem anderen Rechner als dem Quell-PC gestartet?** Dein Klon bringt die
> Treiber deines eigenen Rechners mit. Auf **fremder Hardware** kann es sein, dass
> **Grafik oder WLAN** erst nach dem Nachinstallieren des passenden Treibers rund
> laufen. Das gespeicherte **WLAN-Passwort** wird dabei übernommen — auch wenn die
> Netzwerkkarte im anderen Rechner anders heißt.

---

## 7. Änderungen auf dem Stick behalten (Persistenz)

Ein Live-Stick vergisst normalerweise beim Ausschalten **alles** — beim nächsten
Start ist er wieder wie frisch. Mit **Persistenz** behält der Stick deine
Änderungen (neue Dateien, Programme, WLAN, Einstellungen) — **ganz ohne feste
Installation**.

**So richtest du sie ein:**

1. ISO ganz normal auf den Stick schreiben (Punkt 4) und kontrollieren (Punkt 5).
2. Im Programm auf **„💾 Persistenz einrichten"** klicken und den Stick wählen.
   Auf dem freien Platz **hinter** der ISO wird eine „Persistenz-Kiste" angelegt;
   die ISO selbst bleibt unangetastet. (Du kannst wählen, ob **alles** oder nur
   dein **persönlicher Ordner** gemerkt wird.)

**Beim Starten vom Stick** wählst du im Boot-Menü diesen Eintrag:

> **»with persistence, keep changes (RECOMMENDED)«**

*(Das Boot-Menü ist immer englisch — es kann keine Umlaute darstellen.)*

Dein Klon arbeitet dann im **Arbeitsspeicher** und schreibt **einmal beim
Herunterfahren** alles auf den Stick — ein bewährter Weg: flott im Betrieb und
schonend für den Stick.

> 💡 **Nimm einen schnellen USB-3-Stick!** Wie lange das Speichern beim
> Herunterfahren dauert, **hängt komplett vom Stick ab**. Ein langsamer (oft
> älterer, USB-2-)Stick kann dafür **1–2 Minuten** brauchen — bei einem schnellen
> **USB-3-Stick oder einer USB-SSD** sind es nur **Sekunden**. Für Persistenz lohnt
> sich ein guter Stick also wirklich.

> ⚠️ **Unbedingt richtig herunterfahren** (Menü → Ausschalten). Ziehst du einfach
> den Stecker oder hältst den Ausschaltknopf gedrückt, ist die **ganze Sitzung
> weg** — denn gespeichert wird erst beim ordentlichen Herunterfahren.

> 💡 **Nur für Fortgeschrittene:** Unter **„Advanced options"** liegt zusätzlich
> »persistence written directly to stick«. Der schreibt jede Änderung sofort mit —
> auf normalen USB-Sticks ist das aber **sehr langsam**: Der Start kann Minuten
> dauern, und Systemdienste können dabei scheitern. Sinnvoll nur mit einer
> schnellen **USB-SSD**.

---

## 8. System fest installieren

Auf dem Schreibtisch des Live-Systems liegt das Symbol **„System installieren"**:

1. **Doppelklick** darauf → das deutsche Installationsprogramm (Calamares) öffnet sich.
2. **Willkommen** → „Weiter".
3. **Partitionen**: Für Anfänger: **„Festplatte löschen"** wählen.
   ⚠️ Das löscht ALLES auf der gewählten Platte — vorher sichern!
   (Profis können „Manuelle Partitionierung" wählen.) → „Weiter".
4. **Zusammenfassung**: alles noch einmal lesen → **„Installieren"** →
   Sicherheitsfrage mit **„Jetzt installieren"** bestätigen.
   *(Es gibt bewusst KEINE separate Seite für Sprache/Zeitzone/Tastatur/Benutzer
   — das alles wird aus deinem Schnappschuss übernommen, du musst nichts eintippen.)*
5. Die Installation dauert **ca. 10 Minuten**. Danach: **„Alles erledigt."**
6. Rechner neu starten, **beim Neustart den Stick abziehen** —
   das frisch installierte Linux Mint startet von der Festplatte.
7. Anmelden: mit **deinem gewohnten Konto und Passwort** — es wird KEIN
   neues Konto angelegt (Installer-Symbol und Live-Reste sind automatisch entfernt).

> 🪟 **Windows daneben (Dualboot mit zwei Platten)?** Dann kann es sein, dass der
> Rechner nach der Installation **zuerst wieder Windows** startet. Das ist **normal**
> und liegt an der Firmware des Rechners (sie bevorzugt die Windows-Platte) — nicht
> an Linux Mint. **So lösst du es, einmalig:** Beim Einschalten ins **BIOS/UEFI**
> gehen und die **Linux-Platte** an die erste Stelle setzen. Am bequemsten geht das
> über den Menüpunkt **„Reboot into Firmware Setup (BIOS/UEFI)"** im Start-Menü des
> Sticks — dann musst du nicht die (bei jedem Hersteller andere) BIOS-Taste suchen.
> Danach startet Linux Mint von selbst, und Windows bleibt im Startmenü wählbar.

> ⚠️ **Platz auf der Zielplatte:** Die Festplatte, auf die du installierst, muss
> **mindestens so groß sein wie dein Schnappschuss entpackt** — bei „System + Home"
> kann das deutlich mehr sein, als die ISO-Datei vermuten lässt. Ist die Platte zu
> klein, bricht die Installation ab.

---

## 9. Häufige Fragen

### Der Hinweis „🔔 Version X ist verfügbar"

Ab Fassung 6.11 schaut das Programm beim Start einmal nach, ob es eine neuere Fassung
gibt. Wenn ja, erscheint unter dem Titel eine kleine grüne Zeile mit einem Link zur
Download-Seite. **Mehr passiert nicht** — es wird nichts heruntergeladen und nichts
installiert. Ohne Internet erscheint die Zeile einfach nicht; das Fenster geht wie
gewohnt sofort auf.

**Warum es das gibt:** Das Programm kommt als `.deb` von GitHub und ist damit *keine*
apt-Quelle. `apt update` erfährt also nie davon, dass es etwas Neueres gibt — man
bliebe ohne Hinweis auf einer alten Fassung sitzen, ohne es zu merken.

**Abschalten** — eine einzige Zeile im Terminal:

```
touch ~/.config/rikus-mintshot/kein-update-hinweis
```

Danach fragt das Programm gar nicht mehr nach. Wieder einschalten:

```
rm ~/.config/rikus-mintshot/kein-update-hinweis
```


**Welche Auswahl soll ich nehmen?**  Im Zweifel die mittlere:
**„System + meine Einstellungen"**. Sie ist voreingestellt, bleibt schlank und
ist trotzdem sofort brauchbar — alles ist eingerichtet wie gewohnt.

**Wie groß wird die ISO?**  Das hängt vor allem von deiner Wahl ab:
„Nur System" ist am kleinsten, „System + Home" am größten. Über die Häkchen
unter „Für Fortgeschrittene" lässt sich zusätzlich sparen.

**Ich habe einen Klon installiert — und jetzt will das Programm neu eingerichtet
werden?**  Das ist richtig so und dauert nur einen Klick. Bei einem Klon im Modus
**„Nur System (root)"** bleibt alles unterhalb von `/home` draußen — auch der
Ordner, in dem das Programm seine Abbilder ablegt. Er wird dann neu angelegt.
Einfach auf **„🔧 Jetzt einrichten"** klicken.

**Der Stick startet nicht?**  Boot-Menü-Taste falsch (F12/F2/F8/Esc probieren),
oder Stick neu schreiben und kontrollieren (Punkt 5). (Secure Boot muss NICHT
ausgeschaltet werden — die ISO ist signiert.)

**Kann ich das Fenster während des Baus schließen?**  Ja. Der Bau läuft im
Hintergrund weiter; beim nächsten Öffnen koppelt sich die Anzeige wieder an.

**Was ist mit meinen E-Mails und Passwörtern?**  Das entscheidest du mit der
Auswahl oben: Bei **„Nur System (root)"** bleibt alles Persönliche draußen.
Bei den beiden anderen sind Konto und gespeicherte Zugänge dabei — solche
Sticks sicher verwahren und nicht an Fremde weitergeben!

**Wo finde ich Version und Lizenz?**  Oben im Programmfenster auf
**„ℹ️ Über"** klicken — zeigt Version, Herausgeber und den vollständigen
GPL-3-Lizenztext.

**Woher kommt die Technik?**  Der Großteil ist eigene Technik — die
Secure-Boot-Kette, die Anpassung des Klons an fremde Hardware, die
Persistenz auf dem Stick, die ehrliche Platzvorschau und ein eigens
eingerichteter Installer auf *Calamares*-Basis. Den ersten Schritt —
das laufende System in eine Basis-ISO einsammeln — übernimmt ein
bewährtes Hilfsprogramm, das beim ersten Start automatisch mitkommt.
Dieses Programm macht alles per Klick und auf Deutsch bedienbar.
