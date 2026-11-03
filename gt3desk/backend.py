"""BLE discovery, inspection and reads, with separate opt-in owner pairing.

Read operations never pair. The explicit owner pairing operation can negotiate
a new BLE key; it requires caller confirmation and encrypted local persistence.
There is no vehicle register write or firmware endpoint.
"""

import asyncio
from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError
from scootscoot import (
    AuthenticationFailed, ConnectionFailed, Credentials, HandshakeFailed,
    PairingRequired, PairingTimeout, ProtocolError, Scooter, ServiceNotFound, VehicleBusy,
)
from .catalog import BY_KEY, CATALOG
from .data import decode_reading
from .key_store import KeyStorageError, mark_confirmed, save_pending
from .owner_pairing import OwnerPairingScooter
from .models import GT3_D, UnsupportedVehicle, recognize_model, require_model


PROFILE = GT3_D.profile


def friendly_error(error):
    if isinstance(error, UnsupportedVehicle):
        return ("Modell nicht unterstützt", "Dieses Gerät wird von Segway Monitor nicht angeboten.")
    if isinstance(error, PairingRequired):
        return ("Schlüssel erforderlich",
                "Bitte einmal eine Schlüsseldatei für das ausgewählte Fahrzeug importieren.")
    if isinstance(error, KeyStorageError):
        return ("Schlüsselsicherung fehlgeschlagen", "Die verschlüsselte Sicherung ist fehlgeschlagen. "
                "Es wurde kein neuer Kopplungsschlüssel an den Scooter gesendet.")
    if isinstance(error, PairingTimeout):
        return ("Kopplung nicht bestätigt", "Der Scooter hat die neue Kopplung nicht bestätigt. "
                "Ein vorab gesicherter Schlüssel bleibt lokal erhalten und kann geladen werden.")
    if isinstance(error, AuthenticationFailed):
        return ("Anmeldung abgelehnt", "Der BLE-Schlüssel passt nicht oder ist veraltet.")
    if isinstance(error, VehicleBusy):
        return ("Scooter belegt", "Die andere Verbindung zum Scooter beenden und erneut versuchen.")
    if isinstance(error, ServiceNotFound):
        return ("Schnittstelle unbekannt", "Dieses Fahrzeug bietet keinen unterstützten Datenkanal.")
    if isinstance(error, ProtocolError):
        return ("Protokoll nicht bestätigt", "Die Antwort passt nicht zum Encryption2-Profil. "
                "Für diese Firmware ist eine Anpassung erforderlich.")
    if isinstance(error, HandshakeFailed):
        return ("Anmeldung ohne Antwort", "Scooter einschalten, Segway-App schließen und erneut versuchen. "
                "Auch eine abweichende Firmware kann die Ursache sein.")
    if isinstance(error, TimeoutError):
        return ("Zeitüberschreitung", "Windows oder der Scooter hat nicht rechtzeitig geantwortet. "
                "Bluetooth, Entfernung und die Handy-Verbindung prüfen.")
    if isinstance(error, (BleakError, ConnectionFailed)):
        return ("Bluetooth-Verbindung fehlgeschlagen", "Windows-Bluetooth aktivieren, Scooter einschalten "
                "und die Segway-App schließen. Anschließend erneut suchen.")
    return ("Vorgang fehlgeschlagen", f"Fehlertyp: {type(error).__name__}. Vorgang erneut versuchen.")


class BluetoothService:
    def __init__(self, emit):
        self.emit = emit
        self.devices = {}
        self.device_info = {}
        self.optional_boards = {}

    async def scan(self):
        self.emit("status", "Suche nach unterstützten Segway-Scootern …")
        # Bound startup as well as scan duration. Windows WinRT initialization
        # can itself stall when the process cannot access the physical radio.
        async with asyncio.timeout(24):
            found = await BleakScanner.discover(timeout=9, return_adv=True)
        self.devices.clear()
        self.device_info.clear()
        rows = []
        for device, adv in found.values():
            name = adv.local_name or device.name or "Unbenanntes BLE-Gerät"
            model = recognize_model(name, adv.service_uuids)
            if model is None:
                continue
            row = {"name": name, "address": device.address, "rssi": adv.rssi,
                   "services": list(adv.service_uuids), "candidate": True,
                   "model": model.key, "model_name": model.name}
            self.devices[device.address] = device
            self.device_info[device.address] = row
            rows.append(row)
        rows.sort(key=lambda row: (not row["candidate"], -row["rssi"]))
        self.emit("devices", rows)
        count = sum(row["candidate"] for row in rows)
        self.emit("status", f"{count} unterstützte Segway-Scooter gefunden" if count else
                  "Kein unterstützter Segway gefunden · Scooter einschalten und erneut suchen")
        return rows

    async def resolve(self, address):
        if address in self.devices:
            name = self.device_info.get(address, {}).get("name") or self.devices[address].name
            model = require_model(name, self.device_info.get(address, {}).get("services", ()))
            self.device_info.setdefault(address, {"name": name, "address": address})["model"] = model.key
            return self.devices[address]
        async with asyncio.timeout(18):
            device = await BleakScanner.find_device_by_address(address, timeout=10)
        if device is None:
            raise ConnectionFailed("device was not found")
        model = require_model(device.name)
        self.devices[address] = device
        self.device_info[address] = {"name": device.name or "", "address": address,
                                     "services": [], "model": model.key, "model_name": model.name}
        return device

    async def inspect(self, address):
        self.emit("status", "Bluetooth-Schnittstellen werden gelesen …")
        async with asyncio.timeout(35):
            device = await self.resolve(address)
            async with BleakClient(device, timeout=15) as client:
                services = [{"uuid": s.uuid, "description": s.description,
                             "characteristics": [
                                 {"uuid": c.uuid, "properties": list(c.properties)}
                                 for c in s.characteristics]}
                            for s in client.services]
                self.emit("gatt", services)
        self.emit("status", "Bluetooth-Dienste gelesen · Fahrzeuganmeldung separat prüfen")
        return services

    async def read(self, address, password=None, *, full=False, extra_battery=None):
        self.emit("status", "Verbindung und Fahrzeuganmeldung …")
        async with asyncio.timeout(200 if full else 65):
            device = await self.resolve(address)
            model = require_model(self.device_info[address].get("name") or device.name)
            scooter = Scooter(device, model.profile, Credentials(password=password),
                              device_name=self.device_info[address].get("name") or device.name,
                              connect_timeout=15, read_timeout=1.2)
            async with scooter.session() as session:
                self.emit("model", model.key)
                self.emit("access", "Anmeldung bestätigt · " + model.name)
                has_second = extra_battery is True or self.optional_boards.get(address, False)
                selected = [s for s in model.registers if (full or s.live) and s.board in model.boards]
                if has_second and extra_battery is not False:
                    selected += [s for s in model.registers if s.board == "BMS2" and (full or s.live)]
                result = {}
                for n, spec in enumerate(selected, start=1):
                    # read_raw builds only CMD_READ (0x01). No arbitrary
                    # command, register write or opaque frame is accepted.
                    raw = await session.read_raw(spec.address, spec.index, spec.length)
                    if raw is None:
                        raw = await session.read_raw(spec.address, spec.index, spec.length)
                    reading = decode_reading(spec, raw)
                    result[spec.key] = reading
                    self.emit("reading", reading)
                    self.emit("progress", (n, len(selected)))
                if full and extra_battery is None and not has_second:
                    has_second = await self._detect_second_battery(session, result, model=model)
                    self.optional_boards[address] = has_second
                    if has_second:
                        for spec in model.registers:
                            if spec.board == "BMS2":
                                raw = await session.read_raw(spec.address, spec.index, spec.length)
                                row = decode_reading(spec, raw)
                                result[spec.key] = row
                                self.emit("reading", row)
                modules = self._module_status(result)
                if full:
                    modules["BMS2"] = modules.get("BMS2", {
                        "state": "not_detected" if extra_battery is not False else "not_queried",
                        "answers": 0, "values": 0,
                        "detail": "Kein eindeutig getrenntes zweites BMS erkannt" if extra_battery is not False else
                                  "Zweiter Akku wurde nicht abgefragt",
                    })
                self.emit("modules", modules)
        okay = sum(row.value is not None for row in result.values())
        self.emit("status", f"Abfrage abgeschlossen · {okay}/{len(result)} Werte empfangen · Verbindung freigegeben")
        return result

    async def _detect_second_battery(self, session, result, *, model=GT3_D):
        serial_spec = model.by_key.get("BMS2.rBatterySN")
        voltage_spec = model.by_key.get("BMS2.rBMSVolt")
        if serial_spec is None or voltage_spec is None:
            return False
        raw_serial = await session.read_raw(serial_spec.address, serial_spec.index, serial_spec.length)
        if raw_serial is None or len(raw_serial) < serial_spec.length:
            return False
        serial = raw_serial[:serial_spec.length].rstrip(b"\x00 ")
        if (not serial or not serial.strip(b"0") or not all(32 <= byte < 127 for byte in serial)
                or not any(48 <= byte <= 57 for byte in serial)):
            return False
        primary = result.get("BMS1.rBatterySN")
        if primary is not None and primary.value and serial.decode("ascii") == primary.value:
            return False
        voltage = await session.read_raw(voltage_spec.address, voltage_spec.index, voltage_spec.length)
        return decode_reading(voltage_spec, voltage).value is not None

    @staticmethod
    def _module_status(result):
        modules = {}
        for board in {row.board for row in result.values()}:
            rows = [row for row in result.values() if row.board == board]
            answers = sum(bool(row.raw_hex) for row in rows)
            values = sum(row.value is not None for row in rows)
            modules[board] = {"state": "online" if answers else "no_response",
                              "answers": answers, "values": values,
                              "detail": f"{answers} von {len(rows)} Feldern beantwortet"}
        return modules

    async def pair_owner(self, address, *, owner_confirmed=False, key_directory=None):
        if not owner_confirmed:
            raise ValueError("Die neue Kopplung muss ausdrücklich bestätigt werden.")
        self.emit("status", "Neue lokale Kopplung wird vorbereitet …")
        saved = []
        async with asyncio.timeout(120):
            device = await self.resolve(address)
            name = self.device_info[address].get("name") or device.name
            if not name:
                raise ValueError("Die genaue Bluetooth-Fahrzeugkennung fehlt.")

            def persist(password):
                try:
                    path = save_pending(password, name, address, directory=key_directory)
                except (OSError, ValueError) as error:
                    raise KeyStorageError("Vorherige Schlüsselsicherung fehlgeschlagen.") from error
                saved.append(path)
                self.emit("status", "Neuer Schlüssel vorab verschlüsselt gesichert · Kopplung wird angefordert")

            scooter = OwnerPairingScooter(
                device, PROFILE, Credentials(), device_name=name,
                connect_timeout=15, read_timeout=1.2, persist_password=persist,
                emit_status=lambda message: self.emit("status", message))
            password = await scooter.pair()
        try:
            mark_confirmed(saved[-1])
        except (OSError, ValueError):
            # The previously verified pending file still contains the key.
            self.emit("status", "Kopplung erfolgreich; Schlüssel ist in der vorab erstellten Sicherung verfügbar")
        self.emit("credential_ready", {"password": password, "device_name": name})
        self.emit("access", "Neu gekoppelt und angemeldet · Leseprofil noch unbestätigt")
        self.emit("status", "Neue Kopplung erfolgreich · jetzt Fahrzeugwerte lesen")
        return True

    async def guarded(self, operation):
        try:
            return await operation
        except asyncio.CancelledError:
            self.emit("status", "Vorgang gestoppt · Bluetooth-Verbindung wird freigegeben")
            raise
        except Exception as error:
            title, message = friendly_error(error)
            self.emit("error", (title, message))
            return None
