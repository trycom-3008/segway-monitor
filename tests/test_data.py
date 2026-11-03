import json
import tempfile
import unittest
from pathlib import Path

from gt3desk.catalog import BY_KEY, CATALOG
from gt3desk.data import (decode_reading, format_value, import_credential,
                          make_report, parse_password, write_csv, write_json)


class DataTests(unittest.TestCase):
    def test_gt3_d_requests_thirteen_cell_groups(self):
        spec = BY_KEY["BMS1.rBmsCellVolFrequence"]
        self.assertEqual(spec.length, 26)
        payload = b"".join(n.to_bytes(2, "little") for n in range(4000, 4013))
        row = decode_reading(spec, payload)
        self.assertEqual(len(row.value), 13)
        self.assertEqual(row.value[0], 4.0)
        self.assertEqual(row.value[-1], 4.012)
        self.assertEqual(row.raw_hex, payload.hex())

    def test_range_and_odometer_use_different_scales(self):
        remaining = decode_reading(BY_KEY["VCU.rLeftMileage"], (1234).to_bytes(2, "little"))
        odometer = decode_reading(BY_KEY["VCU.rMileage"], (1234).to_bytes(4, "little"))
        self.assertEqual(remaining.value, 12.34)
        self.assertEqual(odometer.value, 123.4)

    def test_signed_current(self):
        row = decode_reading(BY_KEY["BMS1.rBMSCur"], (-125).to_bytes(2, "little", signed=True))
        self.assertEqual(row.value, -1.25)

    def test_zero_is_a_real_reading(self):
        row = decode_reading(BY_KEY["VCU.rSpeed"], b"\x00\x00")
        self.assertEqual(row.value, 0.0)
        self.assertNotEqual(format_value(row.value), "—")

    def test_timeout_is_not_zero(self):
        row = decode_reading(BY_KEY["VCU.rSpeed"], None)
        self.assertIsNone(row.value)
        self.assertEqual(row.status, "Keine Antwort")

    def test_truncated_array_is_not_padded(self):
        row = decode_reading(BY_KEY["BMS1.rBmsCellVolFrequence"], b"\x00" * 24)
        self.assertIsNone(row.value)
        self.assertEqual(row.status, "Antwort zu kurz")

    def test_implausible_percent_is_not_displayed_as_measurement(self):
        row = decode_reading(BY_KEY["VCU.rBattery"], b"\xff\xff")
        self.assertIsNone(row.value)
        self.assertEqual(row.raw_hex, "ffff")
        self.assertEqual(row.status, "Außerhalb Profilbereich")

    def test_pro_voltage_is_rejected_by_d_profile(self):
        row = decode_reading(BY_KEY["BMS1.rBMSVolt"], (8000).to_bytes(2, "little"))
        self.assertIsNone(row.value)

    def test_invalid_date_is_marked(self):
        row = decode_reading(BY_KEY["VCU.rActDate"], b"\x00\x00")
        self.assertEqual(row.status, "Datum unklar")

    def test_invalid_temperature_channels_do_not_hide_plausible_channels(self):
        raw = bytes.fromhex("150015001600ff00150015001500ff00")
        row = decode_reading(BY_KEY["BMS1.rBmsTempFrequence"], raw)
        self.assertEqual(row.value, [21, 21, 22, None, 21, 21, 21, None])
        self.assertEqual(row.raw_hex, raw.hex())
        self.assertTrue(row.status.startswith("Teilweise gelesen"))
        self.assertNotIn("255", format_value(row.value))

    def test_all_implausible_array_channels_remain_invalid(self):
        row = decode_reading(BY_KEY["BMS1.rBmsTempFrequence"], b"\xff\x00" * 8)
        self.assertIsNone(row.value)
        self.assertEqual(row.status, "Außerhalb Profilbereich")

    def test_password_requires_exact_sixteen_bytes(self):
        self.assertEqual(parse_password("ab " * 16), bytes([0xAB] * 16))
        self.assertIsNone(parse_password(""))
        for invalid in ("ab" * 15, "ab" * 17, "gg" * 16, "account password"):
            with self.assertRaises(ValueError):
                parse_password(invalid)

    def test_import_and_report_do_not_leak_credentials(self):
        secret = "0123456789abcdef" * 2
        with tempfile.TemporaryDirectory() as tmp:
            keyfile = Path(tmp) / "owner.json"
            keyfile.write_text(json.dumps({"password": secret, "device_name": "owner-device"}), encoding="utf-8")
            credential = import_credential(keyfile)
            self.assertEqual(credential.device_name, "owner-device")
            self.assertNotIn(secret, repr(credential))
            report = make_report({"name": "owner-device", "password": secret, "token": secret}, [], {}, "Schlüssel erforderlich")
            output = Path(tmp) / "report.json"
            write_json(output, report)
            self.assertNotIn(secret, output.read_text(encoding="utf-8"))
            self.assertEqual(report["readings"], [])
            self.assertEqual(len(report["not_read"]), len(CATALOG))

    def test_bad_import_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            for obj in ([], {"password": [1] * 16}, {"password": ""}):
                path.write_text(json.dumps(obj), encoding="utf-8")
                with self.assertRaises(ValueError):
                    import_credential(path)

    def test_csv_formula_text_is_escaped_and_utf8(self):
        spec = BY_KEY["VCU.rSN"]
        row = decode_reading(spec, b"=1+1" + b"\x00" * 10)
        report = make_report({}, [], {row.key: row}, "test")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.csv"
            write_csv(path, report)
            payload = path.read_bytes()
            self.assertTrue(payload.startswith(b"\xef\xbb\xbf"))
            self.assertIn("'=1+1", payload.decode("utf-8-sig"))

    def test_catalog_has_unique_keys_and_documented_bounded_lengths(self):
        self.assertEqual(len(CATALOG), len(BY_KEY))
        for spec in CATALOG:
            self.assertLessEqual(spec.length, 26)
            self.assertGreater(spec.length, 0)
            self.assertFalse(spec.name.lower().startswith(("set", "write", "iap")))


if __name__ == "__main__":
    unittest.main()
