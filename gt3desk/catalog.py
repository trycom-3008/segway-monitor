"""Read-only GT3 family register catalogue; GT3 D calibration is pending.

Addresses/lengths: NootNooot's GT3 device command reference (2026-11-02).
VCU routing and selected scales: scootscoot's GT3 Pro profile. The regional
GT3 D is deliberately identified as experimental rather than as a GT3 Pro.
Unknown lengths and non-read commands are excluded instead of guessed.
"""

from dataclasses import dataclass


SOURCE = "https://nootnooot.codeberg.page/segway-ninebot-ble/devices/segway-superscooter-gt3/"
CALIBRATION_SOURCE = "https://github.com/andyshinn/scootscoot"


@dataclass(frozen=True)
class ReadSpec:
    name: str
    label: str
    board: str
    address: int
    index: int
    length: int
    kind: str = "u16"
    scale: float = 1.0
    unit: str = ""
    minimum: float | None = None
    maximum: float | None = None
    live: bool = False

    @property
    def key(self) -> str:
        return f"{self.board}.{self.name}"


def _spec(board, name, label, index, length=2, kind="u16", scale=1.0,
          unit="", minimum=None, maximum=None, live=False):
    addresses = {"BLE": 0x04, "VCU": 0x16, "BMS1": 0x07,
                 "BMS2": 0x06, "MCU": 0x02, "TFT": 0x23}
    return ReadSpec(name, label, board, addresses[board], index, length,
                    kind, scale, unit, minimum, maximum, live)


_s = _spec
_vcu = [
    _s("VCU", "rSN", "Seriennummer", 0x10, 14, "ascii"),
    _s("VCU", "rCtrlV", "VCU-Firmware", 0x17, kind="version"),
    _s("VCU", "rMCUV", "Motor-Firmware", 0x18, kind="version"),
    _s("VCU", "rBmsV", "Akku-Firmware", 0x19, kind="version"),
    _s("VCU", "rBms2V", "Zusatzakku-Firmware", 0x1A, kind="version"),
    _s("VCU", "rCPUId", "VCU-Kennung", 0xDA, 12, "hex"),
    _s("VCU", "rMCUCPUId", "Motorcontroller-Kennung", 0xC0, 12, "hex"),
    _s("VCU", "rActDate", "Aktivierungsdatum", 0x40, kind="date"),
    _s("VCU", "rBattery", "Akkustand (Fahrzeug)", 0x55,
       unit="%", minimum=0, maximum=100, live=True),
    _s("VCU", "rSpeed", "Geschwindigkeit", 0x57, scale=0.1,
       unit="km/h", minimum=0, maximum=120, live=True),
    _s("VCU", "rErrorCode", "Fehlercode", 0x58, live=True),
    _s("VCU", "rWarnCode", "Warncode", 0x59, live=True),
    _s("VCU", "rGearMode", "Fahrmodus (Code)", 0x5A, live=True),
    _s("VCU", "rLeftMileage", "Restreichweite", 0x5F,
       scale=0.01, unit="km", minimum=0, maximum=500, live=True),
    _s("VCU", "rMileage", "Kilometerstand", 0x62, 4,
       "u32", 0.1, "km", minimum=0, maximum=1000000, live=True),
    _s("VCU", "rRuntime", "Gesamtbetriebszeit", 0x64, 4, "u32", unit="s"),
    _s("VCU", "rRideTime", "Gesamtfahrzeit", 0x66, 4, "u32", unit="s"),
    _s("VCU", "rBodyTemp", "Controllertemperatur", 0x6B,
       scale=0.1, unit="°C", minimum=-40, maximum=150, live=True),
]
for _name, _label, _index in [
    ("rFlag", "Fahrzeugstatus (Bits)", 0xE7),
    ("rMCUFlag", "Motorstatus (Bits)", 0xC6),
    ("rFunDisplayBool", "Anzeigefunktionen 1 (Bits)", 0x1B),
    ("rFunDisplayBool2", "Anzeigefunktionen 2 (Bits)", 0x30),
    ("rFunDisplayBool3", "Anzeigefunktionen 3 (Bits)", 0x31),
    ("rFunDisplayBool4", "Anzeigefunktionen 4 (Bits)", 0x32),
    ("rFunDisplayBool5", "Anzeigefunktionen 5 (Bits)", 0x33),
    ("rBool", "Fahrzeugflags (Bits)", 0x1C),
    ("rFunBool", "Funktionen 1 (Bits)", 0x1D),
    ("rFunBool2", "Funktionen 2 (Bits)", 0x1E),
    ("rFunBool3", "Funktionen 3 (Bits)", 0x1F),
    ("rFunBool4", "Funktionen 4 (Bits)", 0x2F),
    ("rStartSpeed", "Anfahrgeschwindigkeit (Rohwert)", 0x42),
    ("rAutoOffTime", "Abschaltzeit (Rohwert)", 0x49),
    ("rCustomKey", "Tastenbelegung (Code)", 0x4A),
    ("rLedMode", "Lichtmodus (Code)", 0x5B),
    ("rProjectionLightMode", "Projektionslicht (Code)", 0x5C),
    ("rTailLightMode", "Rücklicht (Code)", 0x5D),
    ("rPreciseMileage", "Strecke präzise (Rohwert)", 0x5E),
    ("rSingleMileage", "Einzelfahrt Strecke (Rohwert)", 0x68),
    ("rRunningTime", "Aktuelle Betriebszeit (Rohwert)", 0x69),
    ("rSingleRideTime", "Einzelfahrt Zeit (Rohwert)", 0x6A),
    ("readDecMode", "Rekuperationsmodus (Code)", 0x70),
    ("rChargeStartTime", "Ladebeginn (Rohwert)", 0x4B),
    ("rChargeEndTime", "Ladeende (Rohwert)", 0x4C),
    ("rGearED", "ED-Konfiguration (Rohwert)", 0x47),
    ("rGearEDMin", "ED-Untergrenze (Rohwert)", 0x43),
    ("rGearEDMax", "ED-Obergrenze (Rohwert)", 0x45),
    ("rGearSR", "SR-Konfiguration (Rohwert)", 0x48),
    ("rGearSRMin", "SR-Untergrenze (Rohwert)", 0x44),
    ("rGearSRMax", "SR-Obergrenze (Rohwert)", 0x46),
    ("rSupportFoldShutdown", "Faltabschaltung unterstützt (Bits)", 0x31),
    ("rEncryptionFlag", "Verschlüsselungsstatus (Bits)", 0xE8),
    ("rAlarmLevel", "Alarmstufe (Code)", 0x74),
    ("rBumpyRoad", "Straßenzustand (Code)", 0x75),
    ("rVoiceVolume", "Lautstärke (Rohwert)", 0x76),
    ("rInstumentKey", "Displaytasten (Rohwert)", 0x2E),
    ("rSGear", "Sport-Konfiguration (Rohwert)", 0x6E),
    ("rMaintainCode", "Wartungscode", 0x78),
    ("rDGear", "Drive-Konfiguration (Rohwert)", 0x7A),
    ("rEGear", "Eco-Konfiguration (Rohwert)", 0x79),
]:
    _vcu.append(_s("VCU", _name, _label, _index))


def _battery(board):
    result = [
        _s(board, "rBMSVolt", "Akkuspannung", 0x8C, scale=0.01,
           unit="V", minimum=20, maximum=60, live=True),
        _s(board, "rBMSCur", "Akkustrom", 0x8D, kind="i16", scale=0.01,
           unit="A", minimum=-150, maximum=150, live=True),
        _s(board, "rBmsSOC", "Akkustand (BMS)", 0x8F,
           unit="%", minimum=0, maximum=100, live=True),
        _s(board, "rBmsVer", "BMS-Firmware", 0x0E, kind="version"),
        _s(board, "rBmsRB", "Restkapazität", 0x5B, scale=0.01, unit="Ah"),
        _s(board, "rBatterySN", "Akku-Seriennummer", 0x02, 14, "ascii"),
        _s(board, "rMaxPower", "Leistungsgrenze (Rohwert)", 0x82),
        _s(board, "rBmsMoreInfoLT", "Akkuinformationen (Bits)", 0xEA),
        _s(board, "rBmsRemainCapacityLT", "Restkapazität (Rohwert)", 0x8A),
        _s(board, "rBmsManufactureDateLT", "Herstellungsdatum", 0x0A, kind="date"),
        _s(board, "rBmsEnergyThroughputLT", "Energiedurchsatz (Rohwert)", 0xE3, 4, "u32"),
        _s(board, "rBmsCapacityThroughputLT", "Kapazitätsdurchsatz (Rohwert)", 0xE1, 4, "u32"),
        _s(board, "rBmsCycleCountLT", "Ladezyklen", 0x59),
        _s(board, "rBmsDeepDischargeCountLT", "Tiefentladungen", 0x89),
        _s(board, "rBmsExtremeUseTimeLT", "Extremnutzung Zeit (Rohwert)", 0xF5, 4, "u32"),
        _s(board, "rBmsExtremeChargeTimeLT", "Extremladen Zeit (Rohwert)", 0xF7, 4, "u32"),
        _s(board, "rBmsTmp3", "Weitere Temperaturen (Rohbytes)", 0xF9, 4, "hex"),
        _s(board, "rBmsCapacity", "Nennkapazität", 0x13, scale=0.01, unit="Ah"),
    ]
    if board == "BMS1":
        result.extend([
            _s(board, "rTimeFull", "Restladezeit", 0x94, unit="min"),
            _s(board, "rChargeStatus", "Ladestatus (Rohbytes)", 0x92, 4, "hex"),
            _s(board, "rBmsTempFrequence", "Akkutemperaturen", 0x96, 16,
               "u16_array", unit="°C", minimum=-40, maximum=150),
            _s(board, "rBmsCellVolFrequence", "Zellgruppenspannungen (13)", 0xA0, 26,
               "u16_array", 0.001, "V", minimum=1.5, maximum=4.5),
        ])
    else:
        result.append(_s(board, "rBmsCapacity2", "Vollladekapazität", 0x5A,
                         scale=0.01, unit="Ah"))
    return result


CATALOG = tuple(_vcu + _battery("BMS1") + _battery("BMS2") + [
    _s("BLE", "rBleV", "Bluetooth-Firmware", 0x01, kind="version"),
    _s("BLE", "rFunSupBool", "Bluetooth-Funktionen (Bits)", 0x50),
    _s("BLE", "rFindMyStatus", "Find-My-Status (Code)", 0x1D),
    _s("BLE", "rFindMyEnable", "Find My aktiviert (Code)", 0x20),
    _s("MCU", "rMCUPN", "Motorcontroller-Teilenummer", 0x10, 16, "ascii"),
    _s("TFT", "rTftV", "Display-Firmware", 0x01, kind="version"),
])
BY_KEY = {spec.key: spec for spec in CATALOG}
PROFILE_NOTE = (
    "GT3 D · experimentelles Leseprofil. Register und Umrechnungen müssen "
    "am Fahrzeug mit der Segway-App abgeglichen werden. Rohbytes bleiben erhalten."
)
