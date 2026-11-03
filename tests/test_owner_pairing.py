import unittest

from scootscoot import PairingRequired, ProtocolError
from scootscoot.crypto import CryptoStatus, NbCrypto
from scootscoot.framing import CMD_AUTH, CMD_PRE_COMM, CMD_SET_PWD
from scootscoot.handshake import AwaitConfirmation, Established, Handshake, Send
from scootscoot.profiles.types import ENC2_GEN2

from gt3desk.owner_pairing import OwnerHandshake


NAME = "TEST0000000001"
AUTH = bytes(range(16))


def precomm(stored=1, cmd=CMD_PRE_COMM):
    context = NbCrypto(ecb_input=ENC2_GEN2.ecb_input)
    context.set_key(NAME.encode(), ENC2_GEN2.initial_key2)
    reply = bytes([0x5A, 0xA5, 30, 0x04, 0x3E, cmd, stored]) + AUTH + NAME.encode()
    return context.encrypt(reply)


class OwnerPairingTests(unittest.TestCase):
    def handshake(self, persist):
        return OwnerHandshake(device_name=NAME, suite=ENC2_GEN2, ble_address=4, persist_password=persist)

    def test_normal_policy_still_refuses_replacing_stored_password(self):
        ordinary = Handshake(device_name=NAME, suite=ENC2_GEN2, ble_address=4, allow_pairing=True)
        ordinary.start()
        with self.assertRaises(PairingRequired):
            ordinary.feed(precomm())

    def test_explicit_owner_flow_saves_before_returning_set_password(self):
        persisted = []
        handshake = self.handshake(persisted.append)
        handshake.start()
        step = handshake.feed(precomm())
        self.assertIsInstance(step, Send)
        self.assertEqual(len(persisted), 1)
        self.assertEqual(len(persisted[0]), 16)
        self.assertGreaterEqual(step.timeout, 60)
        receiver = NbCrypto(ecb_input=ENC2_GEN2.ecb_input)
        receiver.set_key(NAME.encode(), AUTH)
        receiver.set_auth_param(AUTH)
        plaintext, status = receiver.decrypt(step.payload)
        self.assertEqual(status, CryptoStatus.OK)
        self.assertEqual(plaintext[5], CMD_SET_PWD)
        self.assertEqual(plaintext[7:], persisted[0])
        self.assertEqual(step.payload[-2:], b"\x00\x00")

    def test_failed_save_returns_no_outgoing_set_password(self):
        def fail(_password):
            raise OSError("Test storage failure")
        handshake = self.handshake(fail)
        handshake.start()
        with self.assertRaises(OSError):
            handshake.feed(precomm())
        self.assertEqual(handshake._crypto.counter, 1)

    def test_bad_mac_cannot_trigger_pairing(self):
        persisted = []
        handshake = self.handshake(persisted.append)
        handshake.start()
        raw = bytearray(precomm())
        raw[10] ^= 0x80
        with self.assertRaises(ProtocolError):
            handshake.feed(bytes(raw))
        self.assertEqual(persisted, [])

    def test_wrong_command_cannot_trigger_pairing(self):
        persisted = []
        handshake = self.handshake(persisted.append)
        handshake.start()
        with self.assertRaises(ProtocolError):
            handshake.feed(precomm(cmd=1))
        self.assertEqual(persisted, [])

    def test_unpaired_flow_also_saves_before_send(self):
        persisted = []
        handshake = self.handshake(persisted.append)
        handshake.start()
        self.assertIsInstance(handshake.feed(precomm(stored=0)), Send)
        self.assertEqual(len(persisted), 1)

    def test_pending_button_confirmation_does_not_send_auth(self):
        persisted = []
        handshake = self.handshake(persisted.append)
        handshake.start()
        handshake.feed(precomm())
        vehicle = NbCrypto(ecb_input=ENC2_GEN2.ecb_input)
        vehicle.set_key(NAME.encode(), AUTH)
        vehicle.set_auth_param(AUTH)
        pending = vehicle.encrypt(bytes([0x5A, 0xA5, 0, 4, 0x3E, CMD_SET_PWD, 0]))
        self.assertIsInstance(handshake.feed(pending), AwaitConfirmation)
        self.assertEqual(len(persisted), 1)

    def test_full_documented_handshake_uses_the_previously_saved_key(self):
        persisted = []
        handshake = self.handshake(persisted.append)
        handshake.start()
        handshake.feed(precomm())
        vehicle = NbCrypto(ecb_input=ENC2_GEN2.ecb_input)
        vehicle.set_key(NAME.encode(), AUTH)
        vehicle.set_auth_param(AUTH)
        accepted = vehicle.encrypt(bytes([0x5A, 0xA5, 0, 4, 0x3E, CMD_SET_PWD, 1]))
        auth_step = handshake.feed(accepted)
        self.assertIsInstance(auth_step, Send)
        vehicle.set_key(persisted[0], AUTH)
        plaintext, status = vehicle.decrypt(auth_step.payload)
        self.assertEqual(status, CryptoStatus.OK)
        self.assertEqual(plaintext[5], CMD_AUTH)
        self.assertEqual(auth_step.payload[-2:], b"\x00\x00")
        self.assertEqual(plaintext[7:], NAME.encode())
        response = vehicle.encrypt(bytes([0x5A, 0xA5, 0, 4, 0x3E, CMD_AUTH, 1]))
        established = handshake.feed(response)
        self.assertIsInstance(established, Established)
        self.assertEqual(established.password, persisted[0])
        self.assertTrue(established.paired)
        self.assertEqual(established.crypto.counter, 1)


if __name__ == "__main__":
    unittest.main()
