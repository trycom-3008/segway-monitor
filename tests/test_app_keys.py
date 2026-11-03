"""Exercise the real withdrawn Tk form and native encrypted files, without BLE."""

import sys
import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from gt3desk.app import App
from gt3desk.key_store import mark_confirmed, save_pending
from gt3desk.catalog import BY_KEY
from gt3desk.data import decode_reading


NAME = "03SDG0000A0001"
ADDRESS = "AA:BB:CC:DD:EE:FF"
PASSWORD = b"synthetic-key123"


class OfflineWorker:
    def __init__(self, emit):
        pass

    def shutdown(self):
        pass


@unittest.skipUnless(sys.platform == "win32", "Native Windows GUI and DPAPI are required")
class AppKeyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gt3desk-key-ui-")
        self.folder = Path(self.temp.name).resolve()
        self.assertEqual(self.folder.parent, Path(tempfile.gettempdir()).resolve())
        self.addCleanup(self.temp.cleanup)
        self.storage = patch("gt3desk.key_store.storage_root", return_value=self.folder / "monitor")
        self.storage.start()
        self.addCleanup(self.storage.stop)
        self.path = save_pending(PASSWORD, NAME, ADDRESS, directory=self.folder / "recovery")
        mark_confirmed(self.path)
        self.search = patch("gt3desk.key_store.key_search_directories",
                            return_value=[self.folder / "missing", self.path.parent])
        self.search.start()
        self.addCleanup(self.search.stop)
        self.worker = patch("gt3desk.app.AsyncWorker", OfflineWorker)
        self.worker.start()
        self.addCleanup(self.worker.stop)
        self.root = tk.Tk()
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.app = App(self.root)

    def select(self, address=ADDRESS, name=NAME):
        row = {"address": address, "name": name, "candidate": True}
        self.app.devices = [row]
        self.app._set_device(row)

    def test_selecting_scooter_auto_loads_confirmed_recovery_copy(self):
        self.select()
        self.assertEqual(self.app.password.get(), PASSWORD.hex())
        self.assertTrue(self.app.loaded_key_path.is_relative_to(self.folder / "monitor"))
        self.assertEqual(self.app.key_address, ADDRESS)
        self.assertEqual(self.app.key_device, NAME)
        self.assertTrue(self.app.key_entry.cget("show"))

    def test_other_vehicle_is_never_given_the_saved_secret(self):
        self.select(address="00:00:00:00:00:00")
        self.assertEqual(self.app.password.get(), "")
        self.assertIsNone(self.app.loaded_key_path)

    def test_direct_encrypted_import_when_automatic_search_cannot_find_file(self):
        with patch("gt3desk.key_store.key_search_directories", return_value=[self.folder / "missing"]):
            self.select()
            self.assertEqual(self.app.password.get(), "")
        with patch("gt3desk.app.filedialog.askopenfilename", return_value=str(self.path)):
            self.app.import_key()
        self.assertEqual(self.app.password.get(), PASSWORD.hex())
        self.assertEqual(self.app.key_device, NAME)
        self.assertEqual(self.app.key_address, ADDRESS)

    def test_direct_import_rejects_a_key_for_a_different_selected_scooter(self):
        self.select(address="00:00:00:00:00:00")
        with patch("gt3desk.app.filedialog.askopenfilename", return_value=str(self.path)), \
             patch("gt3desk.app.messagebox.showerror") as show_error:
            self.app.import_key()
        self.assertEqual(self.app.password.get(), "")
        self.assertTrue(show_error.called)

    def test_import_survives_relaunch_without_directory_search(self):
        with patch("gt3desk.key_store.key_search_directories", return_value=[]):
            self.select()
            self.assertFalse(self.app.password.get())
            with patch("gt3desk.app.filedialog.askopenfilename", return_value=str(self.path)):
                self.app.import_key()
            second_root = tk.Toplevel(self.root)
            second_root.withdraw()
            try:
                second = App(second_root)
                row = {"address": ADDRESS, "name": NAME, "candidate": True}
                second.devices = [row]
                second._set_device(row)
                self.assertEqual(second.password.get(), PASSWORD.hex())
                self.assertEqual(second.key_address, ADDRESS)
            finally:
                second_root.destroy()

    def test_only_supported_segways_can_be_selected(self):
        self.app.devices = [{"name": NAME, "address": ADDRESS, "candidate": True},
                            {"name": "ESP32", "address": "00:00:00:00:00:01", "candidate": True}]
        self.app._populate_devices()
        self.assertEqual(len(self.app.visible_devices), 1)
        self.assertEqual(self.app.address, ADDRESS)

    def test_parameter_hover_and_details_explain_battery_voltage(self):
        self.select()
        spec = BY_KEY["BMS1.rBMSVolt"]
        row = decode_reading(spec, (5226).to_bytes(2, "little"))
        self.app.readings[spec.key] = row
        self.app._update_rows()
        with patch.object(tk.Toplevel, "deiconify"):
            self.app.tooltip.show(spec.key, 10, 10)
        self.assertIn("Gesamtspannung", self.app.tooltip.label.cget("text"))
        self.assertIn("Hauptakku", self.app.tooltip.label.cget("text"))
        self.app.table.selection_set(spec.key)
        self.app.row_detail()
        self.assertIn("BMS1.rBMSVolt", self.app.detail_text.get("1.0", "end"))
        self.app.tooltip.hide()

    def test_search_uses_description_and_optional_bms_is_not_shown_before_detection(self):
        self.assertFalse(self.app.table.exists("BMS2.rBMSVolt"))
        self.app.search_var.set("Gesamtspannung")
        self.assertIn("BMS1.rBMSVolt", self.app.table.get_children())
        self.app.search_var.set("")
        self.app.events.put(("modules", {"BMS2": {"state": "online", "answers": 19, "values": 19, "detail": "19 Felder"}}))
        self.app._drain()
        self.assertTrue(self.app.table.exists("BMS2.rBMSVolt"))


if __name__ == "__main__":
    unittest.main()
