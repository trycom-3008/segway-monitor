"""German parameter descriptions. Unknown manufacturer encodings stay explicit.

Register names and lengths: NootNooot's GT3 reference (catalog.SOURCE).
No undocumented bit masks, mode names or physical units are invented here.
"""

from dataclasses import dataclass

from .catalog import CATALOG


COMPONENTS = {
    "VCU": "Fahrzeugsteuerung", "BMS1": "Hauptakku · BMS",
    "BMS2": "Zweiter Akku · BMS", "BLE": "Bluetooth-Modul",
    "MCU": "Motorsteuerung", "TFT": "Display",
}


@dataclass(frozen=True)
class ParameterInfo:
    label: str
    description: str
    presentation: str = "value"


def info(label, description, presentation="value"):
    return ParameterInfo(label, description, presentation)


PARAMETERS = {
    "rSN": info("Fahrzeug-Seriennummer", "Kennung des Scooters, die von der Fahrzeugsteuerung gemeldet wird."),
    "rCtrlV": info("Firmware der Fahrzeugsteuerung", "Ausgelesene Versionskennung der zentralen Fahrzeugsteuerung (VCU)."),
    "rMCUV": info("Firmware der Motorsteuerung", "Versionskennung der Motorsteuerung, die über die Fahrzeugsteuerung bereitgestellt wird."),
    "rBmsV": info("Firmware des Hauptakkus", "Versionskennung des Batteriemanagements, gemeldet über die Fahrzeugsteuerung."),
    "rBms2V": info("Firmware des zweiten Akkus", "Versionskennung eines zweiten Batteriemanagements. Dieser Eintrag gehört zu einem optionalen zweiten Akku."),
    "rCPUId": info("Kennung der Fahrzeug-Elektronik", "Hardwarekennung des Prozessors in der Fahrzeugsteuerung. Die Bytefolge ist eine Kennung, kein Messwert."),
    "rMCUCPUId": info("Kennung der Motor-Elektronik", "Hardwarekennung des Motorcontroller-Prozessors, bereitgestellt über die Fahrzeugsteuerung."),
    "rActDate": info("Aktivierungsdatum", "Im Fahrzeug gespeichertes Datum der Erstaktivierung."),
    "rBattery": info("Akkuladestand des Fahrzeugs", "Von der Fahrzeugsteuerung gemeldeter Ladezustand in Prozent. Der BMS-Ladestand steht zusätzlich in der Akku-Baugruppe."),
    "rSpeed": info("Aktuelle Geschwindigkeit", "Vom Fahrzeug gemeldete Geschwindigkeit in Kilometern pro Stunde."),
    "rErrorCode": info("Aktueller Fehlerstatus", "0 bedeutet, dass kein Fehlercode gemeldet wird. Andere Werte bleiben als Fehlercode sichtbar, bis ihre Bedeutung zugeordnet ist.", "error"),
    "rWarnCode": info("Aktueller Warnstatus", "0 bedeutet, dass kein Warncode gemeldet wird. Andere Werte bleiben als Hersteller-Warncode sichtbar.", "warning"),
    "rGearMode": info("Aktueller Fahrmodus", "Herstellercode des ausgewählten Fahrmodus. Die Zuordnung der einzelnen Moduscodes wird modellbezogen geführt.", "code"),
    "rLeftMileage": info("Geschätzte Restreichweite", "Vom Fahrzeug geschätzte noch fahrbare Strecke in Kilometern. Sie ist eine Fahrzeugprognose und kein fester Akku-Nennwert."),
    "rMileage": info("Gesamtkilometerstand", "Die im Fahrzeug gespeicherte gesamte Fahrstrecke in Kilometern."),
    "rRuntime": info("Gesamte Betriebszeit", "Aufsummierte Betriebszeit der Fahrzeugsteuerung. Der ausgelesene Zähler wird in Sekunden geführt."),
    "rRideTime": info("Gesamte Fahrzeit", "Aufsummierte Fahrzeit laut Fahrzeugsteuerung, in Sekunden."),
    "rBodyTemp": info("Temperatur der Fahrzeugsteuerung", "Gemeldete Temperatur der Steuerelektronik in Grad Celsius."),
    "rFlag": info("Betriebsstatus des Fahrzeugs", "Mehrere Statusangaben sind in einem Bitfeld zusammengefasst. Die Einzelbits sind für dieses Modell noch nicht vollständig zugeordnet.", "bits"),
    "rMCUFlag": info("Status der Motorsteuerung", "Über die Fahrzeugsteuerung gemeldetes Motor-Statusfeld. Die Bedeutung der einzelnen Bits ist noch nicht vollständig zugeordnet.", "bits"),
    "rBool": info("Fahrzeugstatus · Sammelfeld", "Gebündelte Zustandsangaben des Fahrzeugs. Der Wert ist ein Bitfeld und keine einzelne Ein-/Aus-Angabe.", "bits"),
    "rStartSpeed": info("Einstellung der Anfahrgeschwindigkeit", "Herstellerwert zur Anfahrfreigabe. Einheit und Kodierung dieses Einstellwerts sind noch nicht bestätigt.", "raw"),
    "rAutoOffTime": info("Einstellung der automatischen Abschaltung", "Herstellerwert zur automatischen Abschaltung. Die Zeiteinheit ist für dieses Feld noch nicht bestätigt.", "raw"),
    "rCustomKey": info("Belegung der Funktionstaste", "Konfigurationscode für eine zuweisbare Taste. Die einzelnen Belegungscodes sind noch nicht zugeordnet.", "code"),
    "rLedMode": info("Einstellung der Beleuchtung", "Herstellercode für den Beleuchtungsmodus. Die einzelnen Lichtmodi sind noch nicht vollständig zugeordnet.", "code"),
    "rProjectionLightMode": info("Einstellung des Projektionslichts", "Konfigurationscode einer Projektionsbeleuchtung. Ein lesbarer Wert belegt noch nicht, dass diese Ausstattung im Modell verbaut ist.", "code"),
    "rTailLightMode": info("Einstellung des Rücklichts", "Herstellercode zum Betriebsmodus des Rücklichts.", "code"),
    "rPreciseMileage": info("Zusätzlicher Streckenzähler", "Feiner aufgelöster interner Streckenwert. Seine Einheit ist noch nicht bestätigt; für Kilometer den Gesamtkilometerstand verwenden.", "raw"),
    "rSingleMileage": info("Streckenzähler der aktuellen Fahrt", "Interner Streckenwert einer einzelnen Fahrt. Die Skalierung dieses Registers ist noch nicht bestätigt.", "raw"),
    "rRunningTime": info("Betriebszähler seit dem Einschalten", "Interner Zähler der aktuellen Betriebsphase. Die Einheit ist für dieses Register noch nicht bestätigt.", "raw"),
    "rSingleRideTime": info("Zeitzähler der aktuellen Fahrt", "Interner Zeitwert einer einzelnen Fahrt. Seine Zeiteinheit ist noch nicht bestätigt.", "raw"),
    "readDecMode": info("Einstellung der Energierückgewinnung", "Herstellercode für den Rekuperationsmodus, also die Energierückgewinnung beim Verzögern. Einzelne Stufen sind noch nicht zugeordnet.", "code"),
    "rChargeStartTime": info("Einstellung des Ladebeginns", "Herstellerwert für den konfigurierten Ladebeginn. Zeitformat und Bezugszeit sind noch nicht zugeordnet.", "raw"),
    "rChargeEndTime": info("Einstellung des Ladeendes", "Herstellerwert für das konfigurierte Ladeende. Zeitformat und Bezugszeit sind noch nicht zugeordnet.", "raw"),
    "rSupportFoldShutdown": info("Faltabschaltung · Funktionsfeld", "Funktionsfeld zur Abschaltung beim Falten. Die Zuordnung der einzelnen Bits ist noch nicht bestätigt.", "bits"),
    "rEncryptionFlag": info("Kommunikationsstatus · Herstellerfeld", "Statusfeld der Fahrzeugkommunikation. Es enthält keinen auslesbaren BLE-Schlüssel; die einzelnen Bits sind noch nicht zugeordnet.", "bits"),
    "rAlarmLevel": info("Alarmstufe", "Vom Fahrzeug gemeldeter Alarmcode. Die einzelnen Stufen sind noch nicht zugeordnet.", "code"),
    "rBumpyRoad": info("Straßenzustand · Statuscode", "Herstellercode zum erkannten Straßenzustand. Die Bedeutung der einzelnen Werte ist noch nicht zugeordnet.", "code"),
    "rVoiceVolume": info("Einstellung der Signallautstärke", "Herstellerwert für die Lautstärke von Fahrzeugtönen. Die Skala dieses Werts ist noch nicht zugeordnet.", "raw"),
    "rInstumentKey": info("Display-Tastensignal", "Vom Hersteller als Display-Tastenwert geführter Code. Die Zuordnung einzelner Tasten ist noch nicht bestätigt.", "code"),
    "rSGear": info("Sportmodus · Konfigurationsfeld", "Interne Konfiguration des Sport-Fahrmodus. Die Einzelwerte des kodierten Felds sind noch nicht zugeordnet.", "raw"),
    "rDGear": info("Drive-Modus · Konfigurationsfeld", "Interne Konfiguration des Drive-Fahrmodus. Die Einzelwerte des kodierten Felds sind noch nicht zugeordnet.", "raw"),
    "rEGear": info("Eco-Modus · Konfigurationsfeld", "Interne Konfiguration des Eco-Fahrmodus. Die Einzelwerte des kodierten Felds sind noch nicht zugeordnet.", "raw"),
    "rMaintainCode": info("Wartungsstatus", "Vom Fahrzeug gemeldeter Wartungscode. Die einzelnen Wartungsmeldungen sind noch nicht zugeordnet.", "code"),
    "rBMSVolt": info("Akkuspannung", "Elektrische Gesamtspannung des Akkupakets in Volt. Die Spannungen der einzelnen Zellgruppen werden zusätzlich separat angezeigt."),
    "rBMSCur": info("Akkustrom", "Vom BMS gemeldeter Strom in Ampere. Das Vorzeichen bleibt erhalten; die Zuordnung von Laden und Entladen ist modellabhängig."),
    "rBmsSOC": info("Akkuladestand laut BMS", "Vom Batteriemanagement ermittelter Ladezustand in Prozent (State of Charge)."),
    "rBmsVer": info("Firmware des Batteriemanagements", "Ausgelesene Versionskennung der Elektronik, die den Akku überwacht."),
    "rBmsRB": info("Verbleibende Akkukapazität", "Vom BMS gemeldete verbleibende elektrische Ladungsmenge in Amperestunden. Sie ist etwas anderes als Energie in Wattstunden."),
    "rBatterySN": info("Akku-Seriennummer", "Kennung des Akkupakets. Sie dient auch dazu, einen zweiten Akku von einer wiederholten Antwort des Hauptakkus zu unterscheiden."),
    "rMaxPower": info("Leistungsgrenze des Akkus", "Interner BMS-Grenzwert zur Leistung. Die physikalische Einheit dieses Registers ist noch nicht bestätigt.", "raw"),
    "rBmsMoreInfoLT": info("Zusätzlicher Akku-Status", "Gebündelte BMS-Informationen. Die Bedeutung der einzelnen Bits ist noch nicht vollständig zugeordnet.", "bits"),
    "rBmsRemainCapacityLT": info("Weiterer Restkapazitätszähler", "Zusätzlicher interner Kapazitätswert des BMS. Seine Einheit ist noch nicht bestätigt; der Eintrag Verbleibende Akkukapazität hat eine eigene Umrechnung.", "raw"),
    "rBmsManufactureDateLT": info("Herstellungsdatum des Akkus", "Im BMS gespeichertes Produktionsdatum des Akkupakets."),
    "rBmsEnergyThroughputLT": info("Energiedurchsatz des Akkus", "Interner Langzeitzähler zur durchgesetzten Energie. Die Skalierung ist noch nicht bestätigt.", "raw"),
    "rBmsCapacityThroughputLT": info("Ladungsdurchsatz des Akkus", "Interner Langzeitzähler zur durchgesetzten elektrischen Ladung. Die Skalierung ist noch nicht bestätigt.", "raw"),
    "rBmsCycleCountLT": info("Ladezyklen des Akkus", "Vom Batteriemanagement gespeicherter Ladezyklenzähler. Ein Ladezyklus ist nicht zwingend ein einzelner Anschluss an das Ladegerät."),
    "rBmsDeepDischargeCountLT": info("Tiefentladungszähler", "Vom BMS gemeldete Anzahl erfasster Tiefentladungsereignisse. Die Auslöseschwelle legt die Akku-Firmware fest."),
    "rBmsExtremeUseTimeLT": info("Extrembetrieb des Akkus · Zähler", "Diagnosezähler für vom Hersteller als extrem eingestufte Nutzung. Auslöseschwellen und Zeiteinheit sind noch nicht zugeordnet.", "raw"),
    "rBmsExtremeChargeTimeLT": info("Extremladen des Akkus · Zähler", "Diagnosezähler für vom Hersteller als extrem eingestufte Ladevorgänge. Auslöseschwellen und Zeiteinheit sind noch nicht zugeordnet.", "raw"),
    "rBmsTmp3": info("Zusätzliches Temperaturfeld des Akkus", "Zusätzliche Temperaturdaten als Bytefolge. Aufbau und Umrechnung dieses Felds sind noch nicht zugeordnet.", "raw"),
    "rBmsCapacity": info("Nennkapazität des Akkus", "Vom BMS gemeldete Nenn-Ladungsmenge des Akkupakets in Amperestunden."),
    "rBmsCapacity2": info("Vollladekapazität des zweiten Akkus", "Vom zweiten BMS gemeldete Ladungsmenge bei voller Ladung, in Amperestunden."),
    "rTimeFull": info("Geschätzte verbleibende Ladezeit", "Vom BMS geschätzte Restzeit bis zur vollständigen Ladung, in Minuten. Der Betriebszustand des Ladegeräts ist bei der Einordnung zu beachten."),
    "rChargeStatus": info("Ladezustand · Diagnosefeld", "Mehrere Statusbytes zum Ladevorgang. Die Bedeutung der einzelnen Bytes ist noch nicht vollständig zugeordnet.", "raw"),
    "rBmsTempFrequence": info("Temperaturen der Akku-Sensoren", "Acht Temperaturkanäle in Grad Celsius. Ein Strich kennzeichnet einen Kanal ohne plausiblen Temperaturwert; die übrigen Kanäle bleiben sichtbar."),
    "rBmsCellVolFrequence": info("Spannungen der 13 Zellgruppen", "Spannungen der 13 in Reihe überwachten Zellgruppen in Volt. Angezeigt wird eine Spannung je Gruppe, nicht je einzelner parallel geschalteter Zelle."),
    "rBleV": info("Firmware des Bluetooth-Moduls", "Ausgelesene Versionskennung der Bluetooth-Elektronik."),
    "rFunSupBool": info("Bluetooth-Funktionsumfang", "Funktionsfeld des Bluetooth-Moduls. Die einzelnen Funktionsbits sind noch nicht vollständig zugeordnet.", "bits"),
    "rFindMyStatus": info("Find-My-Funktionsstatus", "Herstellercode zum Status der Find-My-Ortungsfunktion. Die einzelnen Zustände sind noch nicht vollständig zugeordnet.", "code"),
    "rFindMyEnable": info("Find-My-Konfiguration", "Konfigurationscode zur Find-My-Funktion. Der Wert wird nicht ohne bestätigte Kodierung als einfacher Ein-/Aus-Schalter interpretiert.", "code"),
    "rMCUPN": info("Teilenummer der Motorsteuerung", "Vom Motorcontroller gemeldete Hardware-Teilenummer."),
    "rTftV": info("Firmware des Displays", "Versionskennung des Display-Moduls. Eine ausbleibende Antwort betrifft dieses Display-Register und sagt nichts über die Erreichbarkeit des Akkus aus."),
}
for stem, title in (("rFunDisplayBool", "Anzeigefunktionen"), ("rFunBool", "Fahrzeugfunktionen")):
    for group in range(1, 6 if stem == "rFunDisplayBool" else 5):
        name = stem + (str(group) if group > 1 else "")
        PARAMETERS[name] = info(f"{title} · Gruppe {group}",
            f"Hersteller-Sammelfeld für {title.lower()}, Gruppe {group}. Einzelne Funktionen sind als Bits kodiert; ihre Zuordnung ist noch nicht vollständig bekannt.", "bits")
for group in ("ED", "SR"):
    for suffix, title in (("", "Konfiguration"), ("Min", "Untergrenzen"), ("Max", "Obergrenzen")):
        PARAMETERS[f"rGear{group}{suffix}"] = info(f"Fahrmodusgruppe {group} · {title}",
            f"Interner Konfigurationswert der Fahrmodusgruppe {group}. Die Kodierung der Einzelwerte und ihre Einheiten sind noch nicht bestätigt.", "raw")


def parameter_info(spec):
    if spec.name == "rBmsCellVolFrequence":
        count = spec.length // 2
        return info(f"Spannungen der {count} Zellgruppen",
                    f"Spannungen der {count} in Reihe überwachten Zellgruppen in Volt. Angezeigt wird eine Spannung je Gruppe, nicht je einzelner parallel geschalteter Zelle.")
    return PARAMETERS[spec.name]


def component_name(board):
    return COMPONENTS.get(board, board)


def parameter_unit(spec):
    presentation = parameter_info(spec).presentation
    return spec.unit or {"bits": "Bitfeld", "raw": "Rohwert", "code": "Code"}.get(presentation, "")


def display_value(spec, value):
    from .data import format_value
    if value is None:
        return "—"
    presentation = parameter_info(spec).presentation
    if presentation == "error":
        return "Kein Fehler" if value == 0 else f"Fehlercode {value}"
    if presentation == "warning":
        return "Keine Warnung" if value == 0 else f"Warncode {value}"
    if presentation == "bits" and isinstance(value, int):
        return f"0x{value:04X}"
    if presentation == "code":
        return f"Code {value}"
    if isinstance(value, list) and len(value) > 8:
        valid = [item for item in value if item is not None]
        if valid:
            return f"{len(valid)} Gruppen · {format_value(min(valid))}–{format_value(max(valid))}"
    return format_value(value)


def parameter_text(spec, row=None):
    from .data import format_value
    entry = parameter_info(spec)
    text = f"{entry.label}\n{component_name(spec.board)}\n\n{entry.description}"
    if row:
        text += f"\n\nWert: {format_value(row.value)} {parameter_unit(spec)}\nStatus: {row.status}"
    text += f"\n\nTechnischer Name: {spec.key}\nDatenquelle: {spec.board} · Adresse 0x{spec.address:02X}"
    text += f"\nRegister: 0x{spec.index:02X} · Antwortlänge: {spec.length} Bytes"
    if row:
        text += f"\nZeit UTC: {row.time}\nRohbytes: {row.raw_hex or '—'}"
    return text


assert all(spec.name in PARAMETERS for spec in CATALOG), "Every register needs a description"
