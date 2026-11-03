import asyncio
import unittest
from unittest.mock import patch

from scootscoot import PairingRequired

from gt3desk.backend import BluetoothService, friendly_error
from gt3desk.catalog import CATALOG


class FakeDevice:
    name = "03SDG0000A0001"
    address = "AA:BB:CC:DD:EE:FF"


class FakeSession:
    reads = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return False

    async def read_raw(self, board, index, length):
        self.reads.append((board, index, length))
        return bytes(length)


class FakeScooter:
    def __init__(self, *_args, **_kwargs):
        pass

    def session(self):
        return FakeSession()

    async def pair(self):
        raise AssertionError("A read operation must never pair")


class BackendTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.events = []
        self.service = BluetoothService(lambda event, value: self.events.append((event, value)))
        self.service.devices[FakeDevice.address] = FakeDevice()
        self.service.device_info[FakeDevice.address] = {"name": FakeDevice.name}
        FakeSession.reads = []

    async def test_live_read_is_bounded_catalogue_and_excludes_extra_battery(self):
        with patch("gt3desk.backend.Scooter", FakeScooter):
            result = await self.service.read(FakeDevice.address)
        expected = [s for s in CATALOG if s.live and s.board != "BMS2"]
        self.assertEqual(len(result), len(expected))
        self.assertEqual(FakeSession.reads, [(s.address, s.index, s.length) for s in expected])
        self.assertTrue(any(event == "access" for event, _ in self.events))

    async def test_all_only_reads_known_registers(self):
        with patch("gt3desk.backend.Scooter", FakeScooter):
            result = await self.service.read(FakeDevice.address, full=True, extra_battery=True)
        self.assertEqual(set(result), {s.key for s in CATALOG})
        self.assertEqual(len(FakeSession.reads), len(CATALOG))

    async def test_cancellation_propagates_and_does_not_fabricate_data(self):
        async def cancelled():
            raise asyncio.CancelledError()
        with self.assertRaises(asyncio.CancelledError):
            await self.service.guarded(cancelled())
        self.assertFalse(any(event == "reading" for event, _ in self.events))

    async def test_auth_required_is_handled_without_raw_error_contents(self):
        async def fail():
            raise PairingRequired("private-handshake-content")
        self.assertIsNone(await self.service.guarded(fail()))
        self.assertEqual(self.events[-1][0], "error")
        self.assertEqual(self.events[-1][1][0], "Schlüssel erforderlich")
        self.assertNotIn("private-handshake-content", str(self.events))

    async def test_owner_pairing_requires_explicit_confirmation(self):
        with self.assertRaises(ValueError):
            await self.service.pair_owner(FakeDevice.address)
        self.assertEqual(self.events, [])


if __name__ == "__main__":
    unittest.main()
