import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from scootscoot.profiles.types import NORDIC_UART

from gt3desk.backend import BluetoothService
from gt3desk.catalog import BY_KEY, CATALOG
from gt3desk.data import decode_reading
from gt3desk.models import GT3_D, UnsupportedVehicle, recognize_model
from gt3desk.parameters import component_name, display_value, parameter_info


class DiscoveryTests(unittest.IsolatedAsyncioTestCase):
    async def test_generic_uart_and_brand_like_names_never_enter_device_list(self):
        def device(name, address):
            return (SimpleNamespace(name=name, address=address),
                    SimpleNamespace(local_name=name, service_uuids=[NORDIC_UART.service], rssi=-40))
        found = {1: device("03SDG0000A0001", "AA:BB:CC:DD:EE:FF"),
                 2: device("Segway-compatible UART", "00:00:00:00:00:01"),
                 3: device("ESP32", "00:00:00:00:00:02")}
        service = BluetoothService(lambda *_: None)
        with patch("gt3desk.backend.BleakScanner.discover", new=AsyncMock(return_value=found)):
            rows = await service.scan()
        self.assertEqual([row["name"] for row in rows], ["03SDG0000A0001"])
        self.assertEqual(set(service.devices), {"AA:BB:CC:DD:EE:FF"})

    async def test_unknown_device_is_rejected_before_any_gatt_connection(self):
        service = BluetoothService(lambda *_: None)
        device = SimpleNamespace(name="ESP32", address="AA:BB:CC:DD:EE:FF")
        with patch("gt3desk.backend.BleakScanner.find_device_by_address", new=AsyncMock(return_value=device)), \
             patch("gt3desk.backend.BleakClient") as client:
            with self.assertRaises(UnsupportedVehicle):
                await service.inspect(device.address)
        client.assert_not_called()


class BatteryDetectionTests(unittest.IsolatedAsyncioTestCase):
    async def detected(self, serial, voltage, primary="BATTERY0000001"):
        session = SimpleNamespace(read_raw=AsyncMock(side_effect=[serial, voltage]))
        row = decode_reading(BY_KEY["BMS1.rBatterySN"], primary.encode("ascii"))
        result = await BluetoothService(lambda *_: None)._detect_second_battery(session, {row.key: row})
        return result, session

    async def test_independent_serial_and_plausible_voltage_identify_second_bms(self):
        result, session = await self.detected(b"BATTERY0000002", (5226).to_bytes(2, "little"))
        self.assertTrue(result)
        self.assertEqual(session.read_raw.await_count, 2)

    async def test_primary_alias_is_not_reported_as_another_battery(self):
        result, session = await self.detected(b"BATTERY0000001", (5226).to_bytes(2, "little"))
        self.assertFalse(result)
        self.assertEqual(session.read_raw.await_count, 1)

    async def test_absent_or_invalid_secondary_is_not_enabled(self):
        for serial, voltage in ((None, None), (b"\x00" * 14, None),
                                (b"00000000000000", None), (b"BATTERY0000002", b"\xff\xff")):
            result, _ = await self.detected(serial, voltage)
            self.assertFalse(result)

    def test_module_health_uses_answers_not_just_plausible_values(self):
        temp_spec = BY_KEY["BMS1.rBmsTempFrequence"]
        temps = decode_reading(temp_spec, b"\xff\x00" * 8)
        tft = decode_reading(BY_KEY["TFT.rTftV"], None)
        health = BluetoothService._module_status({temps.key: temps, tft.key: tft})
        self.assertEqual(health["BMS1"]["state"], "online")
        self.assertEqual(health["BMS1"]["answers"], 1)
        self.assertEqual(health["BMS1"]["values"], 0)
        self.assertEqual(health["TFT"]["state"], "no_response")


class ParameterTests(unittest.TestCase):
    def test_every_readable_field_has_a_component_and_meaning(self):
        for spec in CATALOG:
            entry = parameter_info(spec)
            self.assertTrue(entry.label)
            self.assertGreater(len(entry.description), 35)
            self.assertNotEqual(entry.label, spec.name)
            self.assertNotEqual(component_name(spec.board), spec.board)

    def test_unknown_mode_codes_are_not_given_invented_mode_names(self):
        self.assertEqual(display_value(BY_KEY["VCU.rGearMode"], 4), "Code 4")
        self.assertEqual(display_value(BY_KEY["VCU.rErrorCode"], 0), "Kein Fehler")
        self.assertEqual(display_value(BY_KEY["VCU.rWarnCode"], 7), "Warncode 7")

    def test_model_identity_requires_more_than_uart_uuid(self):
        self.assertIs(recognize_model("03SDG0000A0001", [NORDIC_UART.service]), GT3_D)
        self.assertIsNone(recognize_model("Segway GT3 Pro", [NORDIC_UART.service]))
        self.assertIsNone(recognize_model("03SDG0000A0001", ["180f"]))


if __name__ == "__main__":
    unittest.main()
