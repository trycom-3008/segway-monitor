import json
import unittest

from scootscoot.crypto import NbCrypto
from scootscoot.framing import build_frame
from scootscoot.profiles.types import ENC2_GEN2

from tools.capture_wlbt_chrome import VehicleFrames, is_wlbt_page, is_wlbt_socket
from tools.local_devtools import LocalDevtoolsWebSocket
from tools.probe_wlbt_vehicle import describe
from tools.analyze_wlbt_trace import analyze


NAME = "TEST0000000001"
ENDPOINT = "wss://ws-nb.1dragon.de:443/"


def created(ident="test", url=ENDPOINT):
    return {"method": "Network.webSocketCreated", "params": {"requestId": ident, "url": url}}


def message(data, *, sent=True, ident="test"):
    return {"method": "Network.webSocketFrameSent" if sent else "Network.webSocketFrameReceived",
            "params": {"requestId": ident, "timestamp": 1,
                       "response": {"opcode": 1, "payloadData": data}}}


class WlbtCaptureTests(unittest.TestCase):
    def capture(self):
        capture = VehicleFrames(NAME)
        capture.accept(created())
        capture.accept(message(json.dumps({"type": "device_info", "name": NAME})))
        return capture

    def test_exact_origins_only(self):
        self.assertTrue(is_wlbt_page("https://wlbt.1dragon.de/"))
        self.assertTrue(is_wlbt_socket(ENDPOINT))
        for url in ("https://wlbt.1dragon.de.evil.test/", "http://wlbt.1dragon.de/",
                    "https://user@wlbt.1dragon.de/", "https://wlbt.1dragon.de:444/"):
            self.assertFalse(is_wlbt_page(url))
        for url in ("wss://ws-nb.1dragon.de.evil.test/", "ws://ws-nb.1dragon.de/",
                    "wss://ws-nb.1dragon.de/?key=secret", "wss://ws-nb.1dragon.de:444/"):
            self.assertFalse(is_wlbt_socket(url))

    def test_only_matching_vehicle_bound_to_same_socket(self):
        capture = self.capture()
        capture.accept(created("other"))
        capture.accept(message("90,165,0", ident="other", sent=False))
        capture.accept(created("foreign", "wss://private.example/"))
        capture.accept(message(json.dumps({"type": "device_info", "name": NAME}), ident="foreign"))
        capture.accept(message("90,165,0", ident="foreign", sent=False))
        capture.accept(message("90,165,0", sent=False))
        self.assertEqual(capture.public_summary()["vehicle_frame_count"], 1)
        self.assertEqual(capture.entries[0]["bytes_hex"], "5aa500")

    def test_wrong_vehicle_and_closed_socket_exclude_frames(self):
        capture = self.capture()
        capture.accept(message(json.dumps({"type": "device_info", "name": "OTHER000000001"})))
        capture.accept(message("90,165,0", sent=False))
        capture.accept(message(json.dumps({"type": "device_info", "name": NAME})))
        capture.accept({"method": "Network.webSocketClosed", "params": {"requestId": "test"}})
        capture.accept(message("90,165,0", sent=False))
        self.assertEqual(capture.entries, [])

    def test_unrelated_http_events_and_json_secrets_are_not_saved(self):
        capture = self.capture()
        capture.accept({"method": "Network.responseReceived", "params": {"secret": "cookie"}})
        capture.accept(message(json.dumps({"type": "device_summary", "license": "SECRET",
                                           "serial": "PRIVATE"}), sent=False))
        encoded = json.dumps(capture.entries)
        self.assertNotIn("SECRET", encoded)
        self.assertNotIn("PRIVATE", encoded)
        self.assertTrue(capture.summary_seen)

    def test_out_of_range_and_oversized_payloads_are_excluded(self):
        capture = self.capture()
        for payload in ("256,0", "-1,0", "0," * 512 + "0", "arbitrary text"):
            capture.accept(message(payload, sent=False))
        self.assertEqual(capture.entries, [])

    def test_transport_rejects_remote_and_nonpage_targets(self):
        for url in ("ws://example.com/devtools/page/123", "wss://localhost/devtools/page/1",
                    "ws://127.0.0.1:9222/devtools/browser/1"):
            with self.assertRaises(ValueError):
                LocalDevtoolsWebSocket(url)

    def test_probe_distinguishes_initial_and_challenge_key_contexts(self):
        auth = bytes(range(16))
        for material, label in ((ENC2_GEN2.initial_key2, "name+protocol-constant"),
                                (auth, "name+challenge")):
            crypto = NbCrypto(ecb_input=ENC2_GEN2.ecb_input)
            crypto.set_key(NAME.encode(), material)
            raw = crypto.encrypt(build_frame(4, 0x5c, 0, b"synthetic-key123"))
            result = describe(raw, NAME, auth)
            self.assertEqual(result["key_context"], label)
            self.assertEqual(result["command"], 0x5c)
            self.assertNotIn("synthetic", json.dumps(result))

    def test_offline_analysis_accepts_key_only_after_matching_auth_exchange(self):
        auth = bytes(range(16))
        password = b"synthetic-key123"
        context = NbCrypto(ecb_input=ENC2_GEN2.ecb_input)
        context.set_key(NAME.encode(), ENC2_GEN2.initial_key2)
        entries = []

        def append(plain, direction):
            entries.append({"direction": direction, "bytes_hex": context.encrypt(plain).hex()})

        append(build_frame(4, 0x5b, 0), "server-to-phone")
        append(bytes([0x5a, 0xa5, 30, 4, 0x3e, 0x5b, 1]) + auth + NAME.encode(), "phone-to-server")
        # A server can use the initial key for SET_PWD; don't assume challenge.
        append(build_frame(4, 0x5c, 0, password), "server-to-phone")
        trace = {"schema": "gt3desk.wlbt-chrome-trace.v1", "vehicle_name": NAME, "entries": entries}
        report, extracted = analyze(trace)
        self.assertIsNone(extracted)
        self.assertFalse(report["observed_authentication_success"])
        self.assertEqual(report["frames"][-1]["key_context"], "name+protocol-constant")
        context.set_key(password, auth)
        context.set_auth_param(auth)
        append(build_frame(4, 0x5d, 0, NAME.encode()), "server-to-phone")
        append(bytes([0x5a, 0xa5, 0, 4, 0x3e, 0x5d, 1]), "phone-to-server")
        report, extracted = analyze(trace)
        self.assertEqual(extracted, password)
        self.assertTrue(report["observed_authentication_success"])
        self.assertNotIn(password.hex(), json.dumps(report))
        self.assertNotIn(NAME, json.dumps(report))
        # Rejected AUTH must never authorize extraction.
        entries[-1]["bytes_hex"] = context.encrypt(bytes([0x5a, 0xa5, 0, 4, 0x3e, 0x5d, 0])).hex()
        self.assertIsNone(analyze(trace)[1])

    def test_mac_verified_pairing_ack_allows_pending_key_without_claiming_auth(self):
        auth = bytes(range(16))
        password = b"synthetic-key123"
        context = NbCrypto(ecb_input=ENC2_GEN2.ecb_input)
        context.set_key(NAME.encode(), ENC2_GEN2.initial_key2)
        reply = bytes([0x5a, 0xa5, 30, 4, 0x3e, 0x5b, 1]) + auth + NAME.encode()
        entries = [{"direction": "phone-to-server", "bytes_hex": context.encrypt(reply).hex()}]
        context.set_key(NAME.encode(), auth)
        entries.append({"direction": "server-to-phone",
                        "bytes_hex": context.encrypt(build_frame(4, 0x5c, 0, password)).hex()})
        context.set_key(password, auth)
        context.set_auth_param(auth)
        context.start_sn()
        accepted = context.encrypt(bytes([0x5a, 0xa5, 0, 4, 0x3e, 0x5c, 1]))
        entries.append({"direction": "phone-to-server", "bytes_hex": accepted.hex()})
        trace = {"schema": "gt3desk.wlbt-chrome-trace.v1", "vehicle_name": NAME, "entries": entries}
        report, key = analyze(trace)
        self.assertEqual(key, password)
        self.assertTrue(report["observed_pairing_acknowledgement"])
        self.assertFalse(report["observed_authentication_success"])
        corrupt = bytearray(accepted)
        corrupt[-4] ^= 0x80
        entries[-1]["bytes_hex"] = corrupt.hex()
        self.assertIsNone(analyze(trace)[1])


if __name__ == "__main__":
    unittest.main()
