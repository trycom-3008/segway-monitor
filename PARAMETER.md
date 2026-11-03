# Segway Monitor 1.0.0 · Parameterreferenz

Modell: GT3 D. Das Hauptprofil umfasst 87 Felder; 19 weitere gehören zu einem zweiten BMS.

Die Anwendung zeigt die zusätzlichen BMS2-Felder nach eindeutiger Erkennung an.

| Technischer Name | Anzeige | Baugruppe | Einheit / Format | Erklärung |
| --- | --- | --- | --- | --- |
| VCU.rSN | Fahrzeug-Seriennummer | Fahrzeugsteuerung |  | Kennung des Scooters, die von der Fahrzeugsteuerung gemeldet wird. |
| VCU.rCtrlV | Firmware der Fahrzeugsteuerung | Fahrzeugsteuerung |  | Ausgelesene Versionskennung der zentralen Fahrzeugsteuerung (VCU). |
| VCU.rMCUV | Firmware der Motorsteuerung | Fahrzeugsteuerung |  | Versionskennung der Motorsteuerung, die über die Fahrzeugsteuerung bereitgestellt wird. |
| VCU.rBmsV | Firmware des Hauptakkus | Fahrzeugsteuerung |  | Versionskennung des Batteriemanagements, gemeldet über die Fahrzeugsteuerung. |
| VCU.rBms2V | Firmware des zweiten Akkus | Fahrzeugsteuerung |  | Versionskennung eines zweiten Batteriemanagements. Dieser Eintrag gehört zu einem optionalen zweiten Akku. |
| VCU.rCPUId | Kennung der Fahrzeug-Elektronik | Fahrzeugsteuerung |  | Hardwarekennung des Prozessors in der Fahrzeugsteuerung. Die Bytefolge ist eine Kennung, kein Messwert. |
| VCU.rMCUCPUId | Kennung der Motor-Elektronik | Fahrzeugsteuerung |  | Hardwarekennung des Motorcontroller-Prozessors, bereitgestellt über die Fahrzeugsteuerung. |
| VCU.rActDate | Aktivierungsdatum | Fahrzeugsteuerung |  | Im Fahrzeug gespeichertes Datum der Erstaktivierung. |
| VCU.rBattery | Akkuladestand des Fahrzeugs | Fahrzeugsteuerung | % | Von der Fahrzeugsteuerung gemeldeter Ladezustand in Prozent. Der BMS-Ladestand steht zusätzlich in der Akku-Baugruppe. |
| VCU.rSpeed | Aktuelle Geschwindigkeit | Fahrzeugsteuerung | km/h | Vom Fahrzeug gemeldete Geschwindigkeit in Kilometern pro Stunde. |
| VCU.rErrorCode | Aktueller Fehlerstatus | Fahrzeugsteuerung |  | 0 bedeutet, dass kein Fehlercode gemeldet wird. Andere Werte bleiben als Fehlercode sichtbar, bis ihre Bedeutung zugeordnet ist. |
| VCU.rWarnCode | Aktueller Warnstatus | Fahrzeugsteuerung |  | 0 bedeutet, dass kein Warncode gemeldet wird. Andere Werte bleiben als Hersteller-Warncode sichtbar. |
| VCU.rGearMode | Aktueller Fahrmodus | Fahrzeugsteuerung | Code | Herstellercode des ausgewählten Fahrmodus. Die Zuordnung der einzelnen Moduscodes wird modellbezogen geführt. |
| VCU.rLeftMileage | Geschätzte Restreichweite | Fahrzeugsteuerung | km | Vom Fahrzeug geschätzte noch fahrbare Strecke in Kilometern. Sie ist eine Fahrzeugprognose und kein fester Akku-Nennwert. |
| VCU.rMileage | Gesamtkilometerstand | Fahrzeugsteuerung | km | Die im Fahrzeug gespeicherte gesamte Fahrstrecke in Kilometern. |
| VCU.rRuntime | Gesamte Betriebszeit | Fahrzeugsteuerung | s | Aufsummierte Betriebszeit der Fahrzeugsteuerung. Der ausgelesene Zähler wird in Sekunden geführt. |
| VCU.rRideTime | Gesamte Fahrzeit | Fahrzeugsteuerung | s | Aufsummierte Fahrzeit laut Fahrzeugsteuerung, in Sekunden. |
| VCU.rBodyTemp | Temperatur der Fahrzeugsteuerung | Fahrzeugsteuerung | °C | Gemeldete Temperatur der Steuerelektronik in Grad Celsius. |
| VCU.rFlag | Betriebsstatus des Fahrzeugs | Fahrzeugsteuerung | Bitfeld | Mehrere Statusangaben sind in einem Bitfeld zusammengefasst. Die Einzelbits sind für dieses Modell noch nicht vollständig zugeordnet. |
| VCU.rMCUFlag | Status der Motorsteuerung | Fahrzeugsteuerung | Bitfeld | Über die Fahrzeugsteuerung gemeldetes Motor-Statusfeld. Die Bedeutung der einzelnen Bits ist noch nicht vollständig zugeordnet. |
| VCU.rFunDisplayBool | Anzeigefunktionen · Gruppe 1 | Fahrzeugsteuerung | Bitfeld | Hersteller-Sammelfeld für anzeigefunktionen, Gruppe 1. Einzelne Funktionen sind als Bits kodiert; ihre Zuordnung ist noch nicht vollständig bekannt. |
| VCU.rFunDisplayBool2 | Anzeigefunktionen · Gruppe 2 | Fahrzeugsteuerung | Bitfeld | Hersteller-Sammelfeld für anzeigefunktionen, Gruppe 2. Einzelne Funktionen sind als Bits kodiert; ihre Zuordnung ist noch nicht vollständig bekannt. |
| VCU.rFunDisplayBool3 | Anzeigefunktionen · Gruppe 3 | Fahrzeugsteuerung | Bitfeld | Hersteller-Sammelfeld für anzeigefunktionen, Gruppe 3. Einzelne Funktionen sind als Bits kodiert; ihre Zuordnung ist noch nicht vollständig bekannt. |
| VCU.rFunDisplayBool4 | Anzeigefunktionen · Gruppe 4 | Fahrzeugsteuerung | Bitfeld | Hersteller-Sammelfeld für anzeigefunktionen, Gruppe 4. Einzelne Funktionen sind als Bits kodiert; ihre Zuordnung ist noch nicht vollständig bekannt. |
| VCU.rFunDisplayBool5 | Anzeigefunktionen · Gruppe 5 | Fahrzeugsteuerung | Bitfeld | Hersteller-Sammelfeld für anzeigefunktionen, Gruppe 5. Einzelne Funktionen sind als Bits kodiert; ihre Zuordnung ist noch nicht vollständig bekannt. |
| VCU.rBool | Fahrzeugstatus · Sammelfeld | Fahrzeugsteuerung | Bitfeld | Gebündelte Zustandsangaben des Fahrzeugs. Der Wert ist ein Bitfeld und keine einzelne Ein-/Aus-Angabe. |
| VCU.rFunBool | Fahrzeugfunktionen · Gruppe 1 | Fahrzeugsteuerung | Bitfeld | Hersteller-Sammelfeld für fahrzeugfunktionen, Gruppe 1. Einzelne Funktionen sind als Bits kodiert; ihre Zuordnung ist noch nicht vollständig bekannt. |
| VCU.rFunBool2 | Fahrzeugfunktionen · Gruppe 2 | Fahrzeugsteuerung | Bitfeld | Hersteller-Sammelfeld für fahrzeugfunktionen, Gruppe 2. Einzelne Funktionen sind als Bits kodiert; ihre Zuordnung ist noch nicht vollständig bekannt. |
| VCU.rFunBool3 | Fahrzeugfunktionen · Gruppe 3 | Fahrzeugsteuerung | Bitfeld | Hersteller-Sammelfeld für fahrzeugfunktionen, Gruppe 3. Einzelne Funktionen sind als Bits kodiert; ihre Zuordnung ist noch nicht vollständig bekannt. |
| VCU.rFunBool4 | Fahrzeugfunktionen · Gruppe 4 | Fahrzeugsteuerung | Bitfeld | Hersteller-Sammelfeld für fahrzeugfunktionen, Gruppe 4. Einzelne Funktionen sind als Bits kodiert; ihre Zuordnung ist noch nicht vollständig bekannt. |
| VCU.rStartSpeed | Einstellung der Anfahrgeschwindigkeit | Fahrzeugsteuerung | Rohwert | Herstellerwert zur Anfahrfreigabe. Einheit und Kodierung dieses Einstellwerts sind noch nicht bestätigt. |
| VCU.rAutoOffTime | Einstellung der automatischen Abschaltung | Fahrzeugsteuerung | Rohwert | Herstellerwert zur automatischen Abschaltung. Die Zeiteinheit ist für dieses Feld noch nicht bestätigt. |
| VCU.rCustomKey | Belegung der Funktionstaste | Fahrzeugsteuerung | Code | Konfigurationscode für eine zuweisbare Taste. Die einzelnen Belegungscodes sind noch nicht zugeordnet. |
| VCU.rLedMode | Einstellung der Beleuchtung | Fahrzeugsteuerung | Code | Herstellercode für den Beleuchtungsmodus. Die einzelnen Lichtmodi sind noch nicht vollständig zugeordnet. |
| VCU.rProjectionLightMode | Einstellung des Projektionslichts | Fahrzeugsteuerung | Code | Konfigurationscode einer Projektionsbeleuchtung. Ein lesbarer Wert belegt noch nicht, dass diese Ausstattung im Modell verbaut ist. |
| VCU.rTailLightMode | Einstellung des Rücklichts | Fahrzeugsteuerung | Code | Herstellercode zum Betriebsmodus des Rücklichts. |
| VCU.rPreciseMileage | Zusätzlicher Streckenzähler | Fahrzeugsteuerung | Rohwert | Feiner aufgelöster interner Streckenwert. Seine Einheit ist noch nicht bestätigt; für Kilometer den Gesamtkilometerstand verwenden. |
| VCU.rSingleMileage | Streckenzähler der aktuellen Fahrt | Fahrzeugsteuerung | Rohwert | Interner Streckenwert einer einzelnen Fahrt. Die Skalierung dieses Registers ist noch nicht bestätigt. |
| VCU.rRunningTime | Betriebszähler seit dem Einschalten | Fahrzeugsteuerung | Rohwert | Interner Zähler der aktuellen Betriebsphase. Die Einheit ist für dieses Register noch nicht bestätigt. |
| VCU.rSingleRideTime | Zeitzähler der aktuellen Fahrt | Fahrzeugsteuerung | Rohwert | Interner Zeitwert einer einzelnen Fahrt. Seine Zeiteinheit ist noch nicht bestätigt. |
| VCU.readDecMode | Einstellung der Energierückgewinnung | Fahrzeugsteuerung | Code | Herstellercode für den Rekuperationsmodus, also die Energierückgewinnung beim Verzögern. Einzelne Stufen sind noch nicht zugeordnet. |
| VCU.rChargeStartTime | Einstellung des Ladebeginns | Fahrzeugsteuerung | Rohwert | Herstellerwert für den konfigurierten Ladebeginn. Zeitformat und Bezugszeit sind noch nicht zugeordnet. |
| VCU.rChargeEndTime | Einstellung des Ladeendes | Fahrzeugsteuerung | Rohwert | Herstellerwert für das konfigurierte Ladeende. Zeitformat und Bezugszeit sind noch nicht zugeordnet. |
| VCU.rGearED | Fahrmodusgruppe ED · Konfiguration | Fahrzeugsteuerung | Rohwert | Interner Konfigurationswert der Fahrmodusgruppe ED. Die Kodierung der Einzelwerte und ihre Einheiten sind noch nicht bestätigt. |
| VCU.rGearEDMin | Fahrmodusgruppe ED · Untergrenzen | Fahrzeugsteuerung | Rohwert | Interner Konfigurationswert der Fahrmodusgruppe ED. Die Kodierung der Einzelwerte und ihre Einheiten sind noch nicht bestätigt. |
| VCU.rGearEDMax | Fahrmodusgruppe ED · Obergrenzen | Fahrzeugsteuerung | Rohwert | Interner Konfigurationswert der Fahrmodusgruppe ED. Die Kodierung der Einzelwerte und ihre Einheiten sind noch nicht bestätigt. |
| VCU.rGearSR | Fahrmodusgruppe SR · Konfiguration | Fahrzeugsteuerung | Rohwert | Interner Konfigurationswert der Fahrmodusgruppe SR. Die Kodierung der Einzelwerte und ihre Einheiten sind noch nicht bestätigt. |
| VCU.rGearSRMin | Fahrmodusgruppe SR · Untergrenzen | Fahrzeugsteuerung | Rohwert | Interner Konfigurationswert der Fahrmodusgruppe SR. Die Kodierung der Einzelwerte und ihre Einheiten sind noch nicht bestätigt. |
| VCU.rGearSRMax | Fahrmodusgruppe SR · Obergrenzen | Fahrzeugsteuerung | Rohwert | Interner Konfigurationswert der Fahrmodusgruppe SR. Die Kodierung der Einzelwerte und ihre Einheiten sind noch nicht bestätigt. |
| VCU.rSupportFoldShutdown | Faltabschaltung · Funktionsfeld | Fahrzeugsteuerung | Bitfeld | Funktionsfeld zur Abschaltung beim Falten. Die Zuordnung der einzelnen Bits ist noch nicht bestätigt. |
| VCU.rEncryptionFlag | Kommunikationsstatus · Herstellerfeld | Fahrzeugsteuerung | Bitfeld | Statusfeld der Fahrzeugkommunikation. Es enthält keinen auslesbaren BLE-Schlüssel; die einzelnen Bits sind noch nicht zugeordnet. |
| VCU.rAlarmLevel | Alarmstufe | Fahrzeugsteuerung | Code | Vom Fahrzeug gemeldeter Alarmcode. Die einzelnen Stufen sind noch nicht zugeordnet. |
| VCU.rBumpyRoad | Straßenzustand · Statuscode | Fahrzeugsteuerung | Code | Herstellercode zum erkannten Straßenzustand. Die Bedeutung der einzelnen Werte ist noch nicht zugeordnet. |
| VCU.rVoiceVolume | Einstellung der Signallautstärke | Fahrzeugsteuerung | Rohwert | Herstellerwert für die Lautstärke von Fahrzeugtönen. Die Skala dieses Werts ist noch nicht zugeordnet. |
| VCU.rInstumentKey | Display-Tastensignal | Fahrzeugsteuerung | Code | Vom Hersteller als Display-Tastenwert geführter Code. Die Zuordnung einzelner Tasten ist noch nicht bestätigt. |
| VCU.rSGear | Sportmodus · Konfigurationsfeld | Fahrzeugsteuerung | Rohwert | Interne Konfiguration des Sport-Fahrmodus. Die Einzelwerte des kodierten Felds sind noch nicht zugeordnet. |
| VCU.rMaintainCode | Wartungsstatus | Fahrzeugsteuerung | Code | Vom Fahrzeug gemeldeter Wartungscode. Die einzelnen Wartungsmeldungen sind noch nicht zugeordnet. |
| VCU.rDGear | Drive-Modus · Konfigurationsfeld | Fahrzeugsteuerung | Rohwert | Interne Konfiguration des Drive-Fahrmodus. Die Einzelwerte des kodierten Felds sind noch nicht zugeordnet. |
| VCU.rEGear | Eco-Modus · Konfigurationsfeld | Fahrzeugsteuerung | Rohwert | Interne Konfiguration des Eco-Fahrmodus. Die Einzelwerte des kodierten Felds sind noch nicht zugeordnet. |
| BMS1.rBMSVolt | Akkuspannung | Hauptakku · BMS | V | Elektrische Gesamtspannung des Akkupakets in Volt. Die Spannungen der einzelnen Zellgruppen werden zusätzlich separat angezeigt. |
| BMS1.rBMSCur | Akkustrom | Hauptakku · BMS | A | Vom BMS gemeldeter Strom in Ampere. Das Vorzeichen bleibt erhalten; die Zuordnung von Laden und Entladen ist modellabhängig. |
| BMS1.rBmsSOC | Akkuladestand laut BMS | Hauptakku · BMS | % | Vom Batteriemanagement ermittelter Ladezustand in Prozent (State of Charge). |
| BMS1.rBmsVer | Firmware des Batteriemanagements | Hauptakku · BMS |  | Ausgelesene Versionskennung der Elektronik, die den Akku überwacht. |
| BMS1.rBmsRB | Verbleibende Akkukapazität | Hauptakku · BMS | Ah | Vom BMS gemeldete verbleibende elektrische Ladungsmenge in Amperestunden. Sie ist etwas anderes als Energie in Wattstunden. |
| BMS1.rBatterySN | Akku-Seriennummer | Hauptakku · BMS |  | Kennung des Akkupakets. Sie dient auch dazu, einen zweiten Akku von einer wiederholten Antwort des Hauptakkus zu unterscheiden. |
| BMS1.rMaxPower | Leistungsgrenze des Akkus | Hauptakku · BMS | Rohwert | Interner BMS-Grenzwert zur Leistung. Die physikalische Einheit dieses Registers ist noch nicht bestätigt. |
| BMS1.rBmsMoreInfoLT | Zusätzlicher Akku-Status | Hauptakku · BMS | Bitfeld | Gebündelte BMS-Informationen. Die Bedeutung der einzelnen Bits ist noch nicht vollständig zugeordnet. |
| BMS1.rBmsRemainCapacityLT | Weiterer Restkapazitätszähler | Hauptakku · BMS | Rohwert | Zusätzlicher interner Kapazitätswert des BMS. Seine Einheit ist noch nicht bestätigt; der Eintrag Verbleibende Akkukapazität hat eine eigene Umrechnung. |
| BMS1.rBmsManufactureDateLT | Herstellungsdatum des Akkus | Hauptakku · BMS |  | Im BMS gespeichertes Produktionsdatum des Akkupakets. |
| BMS1.rBmsEnergyThroughputLT | Energiedurchsatz des Akkus | Hauptakku · BMS | Rohwert | Interner Langzeitzähler zur durchgesetzten Energie. Die Skalierung ist noch nicht bestätigt. |
| BMS1.rBmsCapacityThroughputLT | Ladungsdurchsatz des Akkus | Hauptakku · BMS | Rohwert | Interner Langzeitzähler zur durchgesetzten elektrischen Ladung. Die Skalierung ist noch nicht bestätigt. |
| BMS1.rBmsCycleCountLT | Ladezyklen des Akkus | Hauptakku · BMS |  | Vom Batteriemanagement gespeicherter Ladezyklenzähler. Ein Ladezyklus ist nicht zwingend ein einzelner Anschluss an das Ladegerät. |
| BMS1.rBmsDeepDischargeCountLT | Tiefentladungszähler | Hauptakku · BMS |  | Vom BMS gemeldete Anzahl erfasster Tiefentladungsereignisse. Die Auslöseschwelle legt die Akku-Firmware fest. |
| BMS1.rBmsExtremeUseTimeLT | Extrembetrieb des Akkus · Zähler | Hauptakku · BMS | Rohwert | Diagnosezähler für vom Hersteller als extrem eingestufte Nutzung. Auslöseschwellen und Zeiteinheit sind noch nicht zugeordnet. |
| BMS1.rBmsExtremeChargeTimeLT | Extremladen des Akkus · Zähler | Hauptakku · BMS | Rohwert | Diagnosezähler für vom Hersteller als extrem eingestufte Ladevorgänge. Auslöseschwellen und Zeiteinheit sind noch nicht zugeordnet. |
| BMS1.rBmsTmp3 | Zusätzliches Temperaturfeld des Akkus | Hauptakku · BMS | Rohwert | Zusätzliche Temperaturdaten als Bytefolge. Aufbau und Umrechnung dieses Felds sind noch nicht zugeordnet. |
| BMS1.rBmsCapacity | Nennkapazität des Akkus | Hauptakku · BMS | Ah | Vom BMS gemeldete Nenn-Ladungsmenge des Akkupakets in Amperestunden. |
| BMS1.rTimeFull | Geschätzte verbleibende Ladezeit | Hauptakku · BMS | min | Vom BMS geschätzte Restzeit bis zur vollständigen Ladung, in Minuten. Der Betriebszustand des Ladegeräts ist bei der Einordnung zu beachten. |
| BMS1.rChargeStatus | Ladezustand · Diagnosefeld | Hauptakku · BMS | Rohwert | Mehrere Statusbytes zum Ladevorgang. Die Bedeutung der einzelnen Bytes ist noch nicht vollständig zugeordnet. |
| BMS1.rBmsTempFrequence | Temperaturen der Akku-Sensoren | Hauptakku · BMS | °C | Acht Temperaturkanäle in Grad Celsius. Ein Strich kennzeichnet einen Kanal ohne plausiblen Temperaturwert; die übrigen Kanäle bleiben sichtbar. |
| BMS1.rBmsCellVolFrequence | Spannungen der 13 Zellgruppen | Hauptakku · BMS | V | Spannungen der 13 in Reihe überwachten Zellgruppen in Volt. Angezeigt wird eine Spannung je Gruppe, nicht je einzelner parallel geschalteter Zelle. |
| BMS2.rBMSVolt | Akkuspannung | Zweiter Akku · BMS | V | Elektrische Gesamtspannung des Akkupakets in Volt. Die Spannungen der einzelnen Zellgruppen werden zusätzlich separat angezeigt. |
| BMS2.rBMSCur | Akkustrom | Zweiter Akku · BMS | A | Vom BMS gemeldeter Strom in Ampere. Das Vorzeichen bleibt erhalten; die Zuordnung von Laden und Entladen ist modellabhängig. |
| BMS2.rBmsSOC | Akkuladestand laut BMS | Zweiter Akku · BMS | % | Vom Batteriemanagement ermittelter Ladezustand in Prozent (State of Charge). |
| BMS2.rBmsVer | Firmware des Batteriemanagements | Zweiter Akku · BMS |  | Ausgelesene Versionskennung der Elektronik, die den Akku überwacht. |
| BMS2.rBmsRB | Verbleibende Akkukapazität | Zweiter Akku · BMS | Ah | Vom BMS gemeldete verbleibende elektrische Ladungsmenge in Amperestunden. Sie ist etwas anderes als Energie in Wattstunden. |
| BMS2.rBatterySN | Akku-Seriennummer | Zweiter Akku · BMS |  | Kennung des Akkupakets. Sie dient auch dazu, einen zweiten Akku von einer wiederholten Antwort des Hauptakkus zu unterscheiden. |
| BMS2.rMaxPower | Leistungsgrenze des Akkus | Zweiter Akku · BMS | Rohwert | Interner BMS-Grenzwert zur Leistung. Die physikalische Einheit dieses Registers ist noch nicht bestätigt. |
| BMS2.rBmsMoreInfoLT | Zusätzlicher Akku-Status | Zweiter Akku · BMS | Bitfeld | Gebündelte BMS-Informationen. Die Bedeutung der einzelnen Bits ist noch nicht vollständig zugeordnet. |
| BMS2.rBmsRemainCapacityLT | Weiterer Restkapazitätszähler | Zweiter Akku · BMS | Rohwert | Zusätzlicher interner Kapazitätswert des BMS. Seine Einheit ist noch nicht bestätigt; der Eintrag Verbleibende Akkukapazität hat eine eigene Umrechnung. |
| BMS2.rBmsManufactureDateLT | Herstellungsdatum des Akkus | Zweiter Akku · BMS |  | Im BMS gespeichertes Produktionsdatum des Akkupakets. |
| BMS2.rBmsEnergyThroughputLT | Energiedurchsatz des Akkus | Zweiter Akku · BMS | Rohwert | Interner Langzeitzähler zur durchgesetzten Energie. Die Skalierung ist noch nicht bestätigt. |
| BMS2.rBmsCapacityThroughputLT | Ladungsdurchsatz des Akkus | Zweiter Akku · BMS | Rohwert | Interner Langzeitzähler zur durchgesetzten elektrischen Ladung. Die Skalierung ist noch nicht bestätigt. |
| BMS2.rBmsCycleCountLT | Ladezyklen des Akkus | Zweiter Akku · BMS |  | Vom Batteriemanagement gespeicherter Ladezyklenzähler. Ein Ladezyklus ist nicht zwingend ein einzelner Anschluss an das Ladegerät. |
| BMS2.rBmsDeepDischargeCountLT | Tiefentladungszähler | Zweiter Akku · BMS |  | Vom BMS gemeldete Anzahl erfasster Tiefentladungsereignisse. Die Auslöseschwelle legt die Akku-Firmware fest. |
| BMS2.rBmsExtremeUseTimeLT | Extrembetrieb des Akkus · Zähler | Zweiter Akku · BMS | Rohwert | Diagnosezähler für vom Hersteller als extrem eingestufte Nutzung. Auslöseschwellen und Zeiteinheit sind noch nicht zugeordnet. |
| BMS2.rBmsExtremeChargeTimeLT | Extremladen des Akkus · Zähler | Zweiter Akku · BMS | Rohwert | Diagnosezähler für vom Hersteller als extrem eingestufte Ladevorgänge. Auslöseschwellen und Zeiteinheit sind noch nicht zugeordnet. |
| BMS2.rBmsTmp3 | Zusätzliches Temperaturfeld des Akkus | Zweiter Akku · BMS | Rohwert | Zusätzliche Temperaturdaten als Bytefolge. Aufbau und Umrechnung dieses Felds sind noch nicht zugeordnet. |
| BMS2.rBmsCapacity | Nennkapazität des Akkus | Zweiter Akku · BMS | Ah | Vom BMS gemeldete Nenn-Ladungsmenge des Akkupakets in Amperestunden. |
| BMS2.rBmsCapacity2 | Vollladekapazität des zweiten Akkus | Zweiter Akku · BMS | Ah | Vom zweiten BMS gemeldete Ladungsmenge bei voller Ladung, in Amperestunden. |
| BLE.rBleV | Firmware des Bluetooth-Moduls | Bluetooth-Modul |  | Ausgelesene Versionskennung der Bluetooth-Elektronik. |
| BLE.rFunSupBool | Bluetooth-Funktionsumfang | Bluetooth-Modul | Bitfeld | Funktionsfeld des Bluetooth-Moduls. Die einzelnen Funktionsbits sind noch nicht vollständig zugeordnet. |
| BLE.rFindMyStatus | Find-My-Funktionsstatus | Bluetooth-Modul | Code | Herstellercode zum Status der Find-My-Ortungsfunktion. Die einzelnen Zustände sind noch nicht vollständig zugeordnet. |
| BLE.rFindMyEnable | Find-My-Konfiguration | Bluetooth-Modul | Code | Konfigurationscode zur Find-My-Funktion. Der Wert wird nicht ohne bestätigte Kodierung als einfacher Ein-/Aus-Schalter interpretiert. |
| MCU.rMCUPN | Teilenummer der Motorsteuerung | Motorsteuerung |  | Vom Motorcontroller gemeldete Hardware-Teilenummer. |
| TFT.rTftV | Firmware des Displays | Display |  | Versionskennung des Display-Moduls. Eine ausbleibende Antwort betrifft dieses Display-Register und sagt nichts über die Erreichbarkeit des Akkus aus. |

Registergrundlage: [GT3-Protokollreferenz](https://nootnooot.codeberg.page/segway-ninebot-ble/devices/segway-superscooter-gt3/).

Einzelne Herstellerkodierungen sind noch nicht vollständig zugeordnet. Die Beschreibungen benennen dies beim betreffenden Feld; die Rohdaten bleiben in Details und Export verfügbar.
