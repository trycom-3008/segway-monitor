"""Offline WLBT trace analysis. Raw packets and BLE passwords never print.

Only reads a locally DPAPI-encrypted trace. An observed SET_PWD value may be
saved for GT3 Desk after a matching SET_PWD acknowledgement with a valid MAC,
or after the same flow's verified AUTH exchange. Pairing acknowledgement alone
does not prove authentication. This sends no traffic or vehicle commands.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from gt3desk.key_store import _dpapi, save_pending
from scootscoot.crypto import CryptoStatus, NbCrypto
from scootscoot.framing import FrameAssembler
from scootscoot.profiles.types import ENC2_GEN2, ENC2_GEN3


def decrypt(raw, name, direction, auth, password):
    matches = []
    for suite in (ENC2_GEN2, ENC2_GEN3):
        materials = [("name+protocol-constant", name.encode("ascii"), suite.initial_key2)]
        if auth is not None:
            materials.append(("name+challenge", name.encode("ascii"), auth))
            if password is not None:
                materials.append(("observed-password+challenge", password, auth))
        for label, key1, key2 in materials:
            context = NbCrypto(ecb_input=suite.ecb_input)
            context.set_key(key1, key2)
            if auth is not None:
                context.set_auth_param(auth)
            plain, status = context.decrypt(raw)
            if (status != CryptoStatus.OK or len(plain) != 7 + raw[2]
                    or plain[0] != 0x5a or plain[1] not in (0xa5, 0xb5)):
                continue
            if direction == "server-to-phone" and plain[3] != 0x3e:
                continue
            if direction == "phone-to-server" and plain[4] != 0x3e:
                continue
            matches.append((plain, suite.label, label))
    return matches


def analyze(trace):
    if trace.get("schema") != "gt3desk.wlbt-chrome-trace.v1":
        raise ValueError("Unexpected encrypted trace schema")
    name = trace["vehicle_name"]
    auth = password = serial = None
    auth_request_verified = False
    verified_password = None
    paired_password = None
    assemblers = {direction: FrameAssembler() for direction in ("server-to-phone", "phone-to-server")}
    report = {"schema": "gt3desk.wlbt-trace-analysis.v1", "vehicle_name_suffix": name[-4:],
              "frames": [], "message_types": [], "observed_authentication_success": False,
              "observed_pairing_acknowledgement": False,
              "decoded_read_responses": 0, "unrecognized_frame_count": 0}
    for entry in trace.get("entries", []):
        direction = entry.get("direction")
        if direction not in assemblers:
            continue
        if "message_type" in entry:
            report["message_types"].append({"direction": direction, "type": entry["message_type"]})
            continue
        raw_chunk = bytes.fromhex(entry["bytes_hex"])
        for raw in assemblers[direction].feed(raw_chunk):
            row = {"direction": direction, "wire_length": len(raw),
                   "counter": int.from_bytes(raw[-2:], "big"), "decoded": False}
            matches = decrypt(raw, name, direction, auth, password)
            if not matches:
                report["unrecognized_frame_count"] += 1
                report["frames"].append(row)
                continue
            plain, suite, label = matches[0]
            command, index = plain[5:7]
            row.update({"decoded": True, "command": command, "index": index,
                        "payload_length": plain[2], "suite": suite,
                        "key_context": label,
                        "verification": "checksum16" if not row["counter"] else "mac32"})
            if len(matches) > 1:
                row["matching_contexts"] = [f"{item[1]}:{item[2]}" for item in matches]
            if command == 0x5b and direction == "server-to-phone":
                auth = password = serial = None
                auth_request_verified = False
            elif command == 0x5b and direction == "phone-to-server" and plain[2] >= 30:
                auth, serial = plain[7:23], plain[23:37]
                report["stored_password_flag"] = index
            elif command == 0x5c and direction == "server-to-phone" and plain[2] == 16:
                password = plain[7:23]
                auth_request_verified = False
            elif (command == 0x5c and direction == "phone-to-server" and index == 1
                  and label == "observed-password+challenge" and row["counter"] > 0):
                paired_password = password
                report["observed_pairing_acknowledgement"] = True
            elif (command == 0x5d and direction == "server-to-phone"
                  and label == "observed-password+challenge" and serial is not None):
                auth_request_verified = plain[7:] == serial
                row["serial_matches_precomm"] = auth_request_verified
            elif (command == 0x5d and direction == "phone-to-server" and index == 1
                  and label == "observed-password+challenge" and auth_request_verified):
                verified_password = password
                report["observed_authentication_success"] = True
            if command == 0x04 and direction == "phone-to-server":
                report["decoded_read_responses"] += 1
            report["frames"].append(row)
    report["frame_count"] = len(report["frames"])
    return report, verified_password if verified_password is not None else paired_password


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--save-observed-key", action="store_true")
    parser.add_argument("--address")
    args = parser.parse_args()
    try:
        if args.trace.stat().st_size > 4 * 1024 * 1024:
            raise ValueError("Trace size limit")
        trace = json.loads(_dpapi(args.trace.read_bytes(), decrypt=True))
        report, password = analyze(trace)
        if args.save_observed_key:
            if password is None or not args.address:
                raise ValueError("No cryptographically acknowledged key or address")
            # Keep state pending until a fresh native read verifies reuse.
            path = save_pending(password, trace["vehicle_name"], args.address)
            report["encrypted_key_saved"] = True
            report["key_file_name"] = path.name
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        summary = {key: value for key, value in report.items() if key not in ("frames", "message_types")}
        print(json.dumps(summary, ensure_ascii=True), flush=True)
    except (OSError, ValueError, KeyError, TypeError):
        print(json.dumps({"status": "failed", "message": "Lokale Analyse nicht abgeschlossen; keine Rohdaten ausgegeben."}))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
