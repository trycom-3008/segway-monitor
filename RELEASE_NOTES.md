# Segway Monitor 1.0.0

Erstes Release vom 3. November 2026 nach den Entwicklungsversionen von GT3 Desk.

- Neuer Name **Segway Monitor** mit farbigem Modellzusatz **GT3 D**.
- Deutsche Bezeichnungen, Baugruppen, Einheiten und individuelle Erklärungen für
  sämtliche 106 Katalogeinträge; technische Namen bleiben zugänglich.
- Hover-Erklärungen und eine Detailansicht direkt unter der Parameterliste.
- Suche nach Bezeichnungen, technischen Namen, Baugruppen und Erklärungstexten.
- Akkuansicht mit 13 Zellgruppen, Spannungsdifferenz, Temperaturkanälen und
  tatsächlichem Antwortstatus der Baugruppen.
- Zweites BMS wird gezielt erkannt; seine Parameter erscheinen nach eigenständiger
  Akku-Kennung und plausibler Spannung.
- Dauerhafte Schlüsselübernahme nach Import mit fester Ablage im lokalen
  Windows-Benutzerprofil und direktem Dateiindex für den nächsten Programmstart.
- Windows-Ordnerabfrage statt Abhängigkeit vom geerbten `LOCALAPPDATA`-Wert.
- Übernahme vorhandener GT3-Desk-Sicherungen ohne neue Kopplung.
- Ausschließlich erkannte, unterstützte Segways in der Geräteauswahl.
- Normale Oberfläche ohne die bisherigen Entwicklungs- und Sicherheitsbanner.
- Deutsche Bezeichnungen und Funktionsbeschreibungen auch in JSON- und CSV-Exporten.
- Neue EXE, Windows-Versionsinformationen, Paketname und Desktop-Verknüpfung.

Dieses Release wurde für den GT3 D geprüft. Andere Modellfamilien benötigen
eigene getestete Profile. Einzelne Hersteller-Bitfelder sind noch nicht vollständig
zugeordnet; das jeweilige Feld benennt dies in seiner Erklärung.

Beim geprüften GT3 D antwortet das Haupt-BMS auf alle 22 vorgesehenen Felder.
Zwei Temperaturkanäle liefern unplausible Werte und bleiben einzeln leer.
Das Display-Firmware-Register antwortet bei der bisherigen Abfrage nicht.
