import argparse
import asyncio
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Segway Monitor · lokale Fahrzeugdaten")
    parser.add_argument("--scan", action="store_true", help="Bluetooth-Geräte suchen")
    parser.add_argument("--diagnose", metavar="MAC", help="Dienste und Anmeldestatus eines eigenen Fahrzeugs prüfen")
    parser.add_argument("--key-file", type=Path, help="Eigene BLE-Session-Datei; wird nicht ausgegeben")
    parser.add_argument("--saved-key", action="store_true", help="Den letzten lokal verschlüsselt gesicherten Schlüssel verwenden")
    parser.add_argument("--all", action="store_true", help="Alle Profilwerte lesen")
    parser.add_argument("--extra-battery", action="store_true", default=None,
                        help="Zweites BMS gezielt abfragen; sonst automatische Erkennung")
    parser.add_argument("--output", type=Path, help="Lokalen JSON-Bericht schreiben")
    parser.add_argument("--self-check", action="store_true", help="GUI initialisieren und wieder schließen")
    parser.add_argument("--self-check-key", nargs=2, metavar=("MAC", "NAME"),
                        help="Automatisches Laden in der GUI ohne Bluetooth-Verbindung prüfen")
    parser.add_argument("--gui-diagnose", metavar="MAC", help="GUI-Suche, automatisches Laden und Vollabfrage prüfen")
    args = parser.parse_args()
    if args.key_file and args.saved_key:
        parser.error("--key-file und --saved-key können nicht gleichzeitig verwendet werden")
    if args.scan or args.diagnose:
        from .backend import BluetoothService
        from .data import import_credential, make_report, write_json
        from .key_store import latest_key, load_saved_key, remember_credential

        async def command():
            captured = {"gatt": [], "readings": {}, "access": "Noch nicht geprüft", "modules": {}, "authenticated": False}

            def emit(event, value):
                if event == "gatt":
                    captured["gatt"] = value
                elif event == "reading":
                    captured["readings"][value.key] = value
                elif event == "access":
                    captured["access"] = value
                    captured["authenticated"] = True
                elif event == "modules":
                    captured["modules"].update(value)
                elif event == "error":
                    captured["access"] = value[0]
                    print(f"{value[0]}: {value[1]}", flush=True)
                elif event == "status":
                    print(value, flush=True)

            service = BluetoothService(emit)
            if args.scan:
                rows = await service.guarded(service.scan())
                if rows is None:
                    return 1
                candidates = [row for row in rows if row["candidate"]]
                print(json.dumps(candidates, ensure_ascii=True, indent=2), flush=True)
                if args.output:
                    write_json(args.output, {"schema": "segway-monitor.scan.v1", "candidates": candidates})
                return 0
            if await service.guarded(service.inspect(args.diagnose)) is None:
                return 1
            device = service.device_info.get(args.diagnose, {"address": args.diagnose})
            credential = None
            if args.key_file:
                credential = (load_saved_key(args.key_file, expected_address=args.diagnose, expected_name=device.get("name"))
                              if args.key_file.suffix.lower() == ".gt3key" else import_credential(args.key_file))
            if args.saved_key:
                credential = latest_key(args.diagnose, device.get("name", ""))
            if credential and credential.device_name and credential.device_name != device.get("name"):
                print("Die Schlüsseldatei gehört zu einer anderen Fahrzeugkennung.", flush=True)
                return 1
            await service.guarded(service.read(args.diagnose,
                credential.password if credential else None,
                full=args.all, extra_battery=args.extra_battery))
            if captured["authenticated"] and credential:
                remember_credential(credential.password, device["name"], args.diagnose, confirmed=True)
            report = make_report(device, captured["gatt"], captured["readings"], captured["access"])
            report["modules"] = captured["modules"]
            if args.output:
                write_json(args.output, report)
            print(json.dumps({"access": report["access"], "readings": len(report["readings"]),
                              "gatt_services": len(report["gatt"])}, ensure_ascii=True), flush=True)
            return 0 if captured["readings"] else 2

        try:
            return asyncio.run(command())
        except (OSError, ValueError):
            print("Datei konnte nicht verarbeitet werden; Dateiformat und Speicherort prüfen.")
            return 1
        except KeyboardInterrupt:
            return 130
    from .app import launch
    checked = launch(self_check=args.self_check or bool(args.self_check_key) or bool(args.gui_diagnose),
                     self_check_key=args.self_check_key, gui_diagnose=args.gui_diagnose)
    if args.gui_diagnose:
        if args.output:
            from .data import write_json
            write_json(args.output, checked)
        print(json.dumps({"validation": checked["validation"], "readings": len(checked["readings"])}, ensure_ascii=True))
        return 0 if checked["validation"]["key_loaded"] and checked["readings"] else 2
    if args.self_check_key:
        if args.output:
            from .data import write_json
            write_json(args.output, checked)
        return 0 if checked["key_loaded"] and checked["vehicle_binding_matches"] else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
