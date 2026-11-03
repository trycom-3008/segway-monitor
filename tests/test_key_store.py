import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gt3desk.key_store import latest_key, load_saved_key, mark_confirmed, remember_credential, save_pending
from gt3desk.windows_paths import local_app_data


@unittest.skipUnless(sys.platform == "win32", "Windows DPAPI is required")
class KeyStoreTests(unittest.TestCase):
    def test_windows_user_folder_does_not_follow_changed_environment(self):
        actual = local_app_data()
        with patch.dict(os.environ, {"LOCALAPPDATA": str(actual / "Packages" / "redirected-test" / "AC")}):
            self.assertEqual(local_app_data(), actual)

    def test_native_encrypted_roundtrip_and_no_plaintext_key(self):
        password = bytes.fromhex("a179c931904b861bc42559ff20c035ed")
        with tempfile.TemporaryDirectory() as folder:
            path = save_pending(password, "TEST0000000001", "AA:BB:CC:DD:EE:FF", directory=folder)
            self.assertNotIn(password.hex(), path.read_text(encoding="utf-8"))
            self.assertNotIn("TEST0000000001", path.read_text(encoding="utf-8"))
            saved = load_saved_key(path, expected_address="AA:BB:CC:DD:EE:FF", expected_name="TEST0000000001")
            self.assertEqual(saved.password, password)
            self.assertEqual(saved.state, "pending")
            self.assertNotIn(password.hex(), repr(saved))
            mark_confirmed(path)
            self.assertEqual(load_saved_key(path).state, "confirmed")

    def test_each_attempt_preserves_previous_key(self):
        with tempfile.TemporaryDirectory() as folder:
            first = save_pending(b"a" * 16, "TEST0000000001", "AA:BB:CC:DD:EE:FF", directory=folder)
            second = save_pending(b"b" * 16, "TEST0000000001", "AA:BB:CC:DD:EE:FF", directory=folder)
            self.assertNotEqual(first, second)
            self.assertEqual(load_saved_key(first).password, b"a" * 16)
            self.assertEqual(latest_key("AA:BB:CC:DD:EE:FF", "TEST0000000001", directory=folder).password, b"b" * 16)

    def test_wrong_vehicle_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = save_pending(b"a" * 16, "TEST0000000001", "AA:BB:CC:DD:EE:FF", directory=folder)
            with self.assertRaises(ValueError):
                load_saved_key(path, expected_address="00:00:00:00:00:00")
            with self.assertRaises(ValueError):
                load_saved_key(path, expected_name="TEST0000000002")

    def test_invalid_envelope_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "invalid.gt3key"
            path.write_text(json.dumps({"schema": "different", "protected": "abc"}), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_saved_key(path)

    def test_confirmed_key_survives_a_newer_unconfirmed_attempt(self):
        with tempfile.TemporaryDirectory() as folder:
            confirmed = save_pending(b"a" * 16, "TEST0000000001", "AA:BB:CC:DD:EE:FF", directory=folder)
            mark_confirmed(confirmed)
            save_pending(b"b" * 16, "TEST0000000001", "AA:BB:CC:DD:EE:FF", directory=folder)
            loaded = latest_key("aa-bb-cc-dd-ee-ff", "TEST0000000001", directory=folder)
            self.assertEqual(loaded.password, b"a" * 16)
            self.assertEqual(loaded.state, "confirmed")

    def test_confirmed_only_never_automatically_loads_pending_key(self):
        with tempfile.TemporaryDirectory() as folder:
            save_pending(b"a" * 16, "TEST0000000001", "AA:BB:CC:DD:EE:FF", directory=folder)
            with self.assertRaises(FileNotFoundError):
                latest_key("AA:BB:CC:DD:EE:FF", "TEST0000000001", directory=folder, confirmed_only=True)

    def test_unreadable_directory_is_not_reported_as_no_key(self):
        with patch.object(Path, "iterdir", side_effect=PermissionError("Read denied")):
            with self.assertRaises(PermissionError):
                latest_key("AA:BB:CC:DD:EE:FF", "TEST0000000001", directory="unreadable")

    def test_renamed_backup_is_found_by_protected_vehicle_identity(self):
        with tempfile.TemporaryDirectory() as folder:
            key = save_pending(b"a" * 16, "TEST0000000001", "AA:BB:CC:DD:EE:FF", directory=folder)
            mark_confirmed(key)
            renamed = key.with_name("meine-sicherung.gt3key")
            key.rename(renamed)
            loaded = latest_key("AA:BB:CC:DD:EE:FF", "TEST0000000001", directory=folder)
            self.assertEqual(loaded.path, renamed)

    def test_direct_index_loads_even_when_folder_listing_fails(self):
        with tempfile.TemporaryDirectory() as folder, \
             patch("gt3desk.key_store.storage_root", return_value=Path(folder)):
            saved = remember_credential(b"a" * 16, "TEST0000000001", "AA:BB:CC:DD:EE:FF")
            with patch.object(Path, "iterdir", side_effect=PermissionError("No enumeration")):
                loaded = latest_key("AA:BB:CC:DD:EE:FF", "TEST0000000001", confirmed_only=True)
            self.assertEqual(loaded.password, saved.password)
            self.assertNotIn((b"a" * 16).hex(), (Path(folder) / "key-index.json").read_text())

    def test_index_cannot_reassign_a_key_to_another_vehicle(self):
        with tempfile.TemporaryDirectory() as folder, \
             patch("gt3desk.key_store.storage_root", return_value=Path(folder)):
            remember_credential(b"a" * 16, "TEST0000000001", "AA:BB:CC:DD:EE:FF", confirmed=True)
            path = Path(folder) / "key-index.json"
            index = json.loads(path.read_text())
            index["vehicles"]["00:00:00:00:00:00"] = index["vehicles"]["AA:BB:CC:DD:EE:FF"]
            path.write_text(json.dumps(index))
            with patch("gt3desk.key_store.key_search_directories", return_value=[]):
                with self.assertRaises(FileNotFoundError):
                    latest_key("00:00:00:00:00:00", "TEST0000000001")


if __name__ == "__main__":
    unittest.main()
