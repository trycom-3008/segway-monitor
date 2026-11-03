# Segway Monitor · Release 1.0.0

Native Windows-Anwendung zum Abrufen der Fahrzeugdaten unterstützter
Segway/Ninebot-Modelle. Dieses Release unterstützt den **Segway GT3 D**.

[Windows-Download · Version 1.0.0](https://github.com/trycom-3008/segway-monitor/releases/tag/v1.0.0)
· [Quellcode](https://github.com/trycom-3008/segway-monitor)

Benötigt werden ein Windows-PC mit 64 Bit und Bluetooth, ein eingeschalteter
unterstützter Scooter und dessen eigener BLE-Schlüssel. Der Schlüsselimport
erfolgt einmalig; danach wird der gespeicherte Zugang automatisch geladen.

## Starten

`Segway-Monitor-Windows-v1.0.0.zip` vollständig entpacken und
`Segway-Monitor.exe` starten. Python muss dafür nicht installiert sein.

1. Scooter einschalten und **Segway suchen** wählen.
2. Das Fahrzeug auswählen. Ein gespeicherter Zugang wird automatisch geladen.
3. Beim ersten Mal **Schlüssel importieren** verwenden: eigene `.gt3key`-Sicherung
   oder JSON-Datei im Format von `credential-format.example.txt` auswählen.
4. **Werte lesen**, **Live-Abfrage starten** oder **Alle Profilwerte lesen** wählen.

Der Import lädt und speichert den Zugang; die Fahrzeugabfrage startet mit einem
der Lesebefehle. Ein eigener BLE-Schlüssel gehört zum jeweiligen Fahrzeug und
wird im allgemeinen Programmpaket nicht mitgeliefert.

## Parameter und Baugruppen

Die Parameterliste zeigt eine deutsche Bezeichnung, die Baugruppe, Wert,
Einheit, Antwortstatus und den technischen Namen. Die Suche berücksichtigt auch
Erklärungen und Baugruppennamen. Beim Verweilen des Mauszeigers über einer Zeile
erscheint ihre Funktionsbeschreibung. Ein Klick öffnet die ausführlichen Details
unter der Tabelle, einschließlich Register, Zeitstempel und Rohbytes.

Herstellerfelder mit nicht vollständig zugeordneten Einzelcodes erscheinen als
**Code**, **Bitfeld** oder **Rohwert**. Die Erklärung beschreibt den bekannten
Funktionsbereich und die verbleibende Unklarheit. Eine Zuordnung aller
Hersteller-Bits oder unbestätigter physikalischer Einheiten wird nicht vorgetäuscht.

Die vollständige Referenz mit allen 106 Katalogeinträgen steht in `PARAMETER.md`.

## Live-Werte und vollständige Abfrage

Die Live-Abfrage aktualisiert die laufenden Betriebswerte. Nach jeder
abgeschlossenen Runde wartet sie fünf Sekunden bis zur nächsten Abfrage.
**Alle Profilwerte lesen** ergänzt unter anderem Seriennummern, Firmware,
Ladezyklen, Temperaturkanäle und Zellgruppenspannungen.

Das GT3-D-Hauptprofil enthält 87 Felder. 19 weitere gehören zum optionalen
zweiten Batteriemanagement. Diese zusätzlichen Felder werden angezeigt, wenn
eine eigene Akku-Seriennummer und eine plausible Spannung des zweiten BMS
empfangen wurden. Eine Antwort mit derselben Akku-Kennung wie BMS1 zählt nicht
als eigenständiger zweiter Akku.

Die Seite **Akku & Baugruppen** zeigt:

- alle 13 Zellgruppenspannungen mit Minimum, Maximum und Spannungsdifferenz;
- acht Temperaturkanäle, wobei unplausible Kanäle als Strich erscheinen;
- den Antwortstatus von Fahrzeugsteuerung, Haupt-BMS, Bluetooth, Motorsteuerung,
  Display und optionalem zweitem BMS.

**Nicht erkannt** bedeutet, dass die Abfrage kein eindeutig getrenntes zweites
BMS nachgewiesen hat. **Keine Antwort** betrifft die konkret angefragte
Baugruppe; **Noch nicht abgefragt** beschreibt den Stand vor ihrer Abfrage.

## Dauerhaft gespeicherter Zugang

Der feste Speicherort ist `%LOCALAPPDATA%\SegwayMonitor` und hängt weder vom
EXE-Ordner noch von der Programmversion ab. Der BLE-Schlüssel liegt in einer
mit Windows-DPAPI geschützten Datei. `key-index.json` speichert ausschließlich
Fahrzeugzuordnung und Dateiname, keinen Schlüsselwert.
Der Benutzerordner wird direkt über Windows ermittelt; ein abweichender
`LOCALAPPDATA`-Wert eines Startprozesses ändert diese Ablage nicht.

Nach einem Import wird die genaue Sicherungsdatei registriert. Ein Neustart
verwendet diese direkte Zuordnung, ohne von einer Dateinamen-Suche abhängig zu
sein. Nach erfolgreicher Fahrzeuganmeldung wird der Zugang als bestätigt geführt.
**Eingabe leeren** leert das aktuelle Feld; die gespeicherte Zuordnung bleibt bestehen.

Ältere GT3-Desk-Sicherungen werden lokal übernommen. Die alten Dateien bleiben
erhalten. Für die bestehende Installation ist keine neue Fahrzeugkopplung nötig.
Die Schlüsselspeicherung ist an den Windows-Benutzer gebunden. Ein Kopieren des
Programmpakets auf einen anderen PC überträgt keinen Fahrzeugzugang.

## Geräteauswahl und unterstützte Modelle

Die Suche bietet ausschließlich erkannte Geräte mit einem unterstützten
Modellprofil an. Ein allgemeiner Nordic-UART-Dienst oder ein Markenwort im
Bluetooth-Namen allein reicht dafür nicht. Ohne passendes Gerät erscheint
**Kein unterstützter Segway gefunden**.

| Modell | Release 1.0.0 |
| --- | --- |
| Segway GT3 D | Anmeldung, Live-Werte und Vollabfrage am realen Fahrzeug geprüft |
| Weitere Segway/Ninebot-Modelle | Können als eigene geprüfte Modellprofile ergänzt werden |

Die Fahrzeugtests erfolgten am GT3 D mit dem vorhandenen modifizierten
Firmwarestand des Testfahrzeugs. Ein Abgleich sämtlicher Serienfirmwarestände
gehört nicht zu dieser Modellprüfung.

Die Modellprofile enthalten ihre eigene Protokollkonfiguration, Registerliste,
Baugruppen und Anzahl der Zellgruppen. Dieses Release verspricht keine
automatische Kompatibilität mit sämtlichen Segway-Modellen.

## Export

**Exportieren** speichert JSON oder eine Excel-kompatible UTF-8-CSV-Datei mit
Semikolon-Trennung. Enthalten sind Messwerte, deutsche Bezeichnungen,
Erklärungen, Baugruppen, technische Namen, Status, Zeitstempel und Rohdaten.
Schlüssel und Anmeldepakete sind nicht Bestandteil der Exporte.

## Entwicklung

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m gt3desk
.\build.ps1 -OutputDirectory dist-v1.0.0
.\.venv\Scripts\python.exe tools/package_release.py
```

Diagnosebefehle der EXE oder des internen Python-Pakets:

```powershell
Segway-Monitor.exe --self-check
Segway-Monitor.exe --scan --output suche.json
Segway-Monitor.exe --diagnose AA:BB:CC:DD:EE:FF --saved-key --all --output fahrzeug.json
Segway-Monitor.exe --self-check-key AA:BB:CC:DD:EE:FF FAHRZEUGNAME --output zugangspruefung.json
Segway-Monitor.exe --gui-diagnose AA:BB:CC:DD:EE:FF --output gui-pruefung.json
```

`--self-check-key` prüft das Laden im GUI-Ablauf ohne Funkverbindung.
`--gui-diagnose` prüft die tatsächliche Suche, Auswahl, Zugangsladung und
Vollabfrage über die native Oberfläche. Die Diagnoseberichte enthalten keinen Schlüssel.

## Quellen und Lizenzen

- [GT3-Registerreferenz von NootNooot](https://nootnooot.codeberg.page/segway-ninebot-ble/devices/segway-superscooter-gt3/)
- [scootscoot: Encryption2-Bibliothek und Protokollherkunft](https://github.com/andyshinn/scootscoot)
- [Bleak: Windows-Bluetooth](https://bleak.readthedocs.io/en/latest/backends/windows.html)

Der eigene Anwendungscode von Segway Monitor steht unter der [MIT-Lizenz](LICENSE).
Drittanbieter-Komponenten und daraus übernommenes Material behalten ihre
jeweiligen Lizenzen. Originale Lizenztexte und Herkunftshinweise stehen unter
`licenses` und in [NOTICE](NOTICE).

Segway Monitor ist eine unabhängige, inoffizielle Anwendung ohne Verbindung
zu Segway oder Ninebot. Die Markennamen benennen die unterstützte Hardware.
