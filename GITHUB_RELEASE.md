# Segway Monitor 1.0.0

Erstes öffentliches Release der nativen Windows-Anwendung für den **Segway GT3 D**.

## Download und Start

Unter **Assets** die Datei **Segway-Monitor-Windows-v1.0.0.zip** herunterladen,
vollständig entpacken und **Segway-Monitor.exe** starten. Python ist nicht nötig.
Windows mit 64 Bit, Bluetooth und der eigene BLE-Schlüssel des unterstützten
Fahrzeugs werden vorausgesetzt. Der Schlüssel wird einmal importiert und danach
automatisch aus dem lokalen Windows-Benutzerprofil geladen.

Der Quellcode steht separat als **Segway-Monitor-Source-v1.0.0.zip** und im
Repository bereit. **SHA256SUMS.txt** enthält die Prüfsummen der beiden Pakete.

## Funktionen

- Live-Abfrage und vollständige Profilabfrage mit 87 Feldern des GT3 D.
- Deutsche Bezeichnungen, Baugruppen und individuelle Hover-Erklärungen.
- Technische Details mit Register, Rohwert und Zeitstempel.
- Akkuansicht mit 13 Zellgruppen, Temperaturkanälen und Baugruppenstatus.
- Automatische Erkennung eines optionalen zweiten BMS mit weiteren 19 Feldern.
- Lokale, mit Windows-DPAPI verschlüsselte Schlüsselspeicherung.
- JSON- und CSV-Export mit verständlichen Bezeichnungen und Erklärungen.
- Geräteauswahl ausschließlich für erkannte, unterstützte Modellprofile.

## Geprüfter Umfang

Die vollständige Abfrage und Anmeldung wurden am realen GT3 D mit dem vorhandenen
modifizierten Firmwarestand geprüft. Der Besitzer hat den Betrieb der fertigen
Version bestätigt. 66 automatisierte Tests bestanden. Das Haupt-BMS beantwortet
alle 22 vorgesehenen Abfragen.

Von 87 Profilfeldern werden im Fahrzeugtest 85 vollständig und eines teilweise
gelesen; das Display-Firmware-Register antwortet nicht. Zwei Temperaturkanäle
liefern unplausible Werte und bleiben einzeln leer. Nicht vollständig zugeordnete
Hersteller-Codes sind entsprechend erklärt. Andere Segway-Modelle und sämtliche
Serienfirmwarestände sind mit diesem Release noch nicht validiert.

Die Windows-EXE ist derzeit nicht digital signiert.

## Lizenz und Herkunft

Der eigene Anwendungscode steht unter der **MIT-Lizenz**. Drittanbieter-Komponenten
behalten ihre Lizenzen; Originaltexte und Hinweise liegen beiden Paketen bei.
Segway Monitor ist eine unabhängige, inoffizielle Anwendung ohne Verbindung zu
Segway oder Ninebot. Die Pakete enthalten keine Fahrzeugschlüssel, persönlichen
Fahrzeugkennungen oder privaten Messberichte.
