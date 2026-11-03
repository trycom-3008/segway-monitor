"""One explicitly approved PRE_COMM relay, then STOP before other BLE commands.

Discloses the real BLE name and the scooter's PRE_COMM response to the public
WLBT backend. Execute only after the owner approves that specific disclosure.
The only accepted backend-to-vehicle command is a validated PRE_COMM (0x5B).
SET_PWD, AUTH, register writes, register reads and unknown frames are never sent.
No frame payloads or proposed passwords are written to the report.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from bleak import BleakClient, BleakScanner
from scootscoot.crypto import CryptoStatus, NbCrypto
from scootscoot.framing import FrameAssembler
from scootscoot.profiles.types import ENC2_GEN2, ENC2_GEN3, NORDIC_UART

try:
    from .probe_wlbt_backend import PublicWebSocket
except ImportError:
    from probe_wlbt_backend import PublicWebSocket


def decrypt_candidates(raw, name, auth=None):
    for suite in (ENC2_GEN2, ENC2_GEN3):
        context = NbCrypto(ecb_input=suite.ecb_input)
        context.set_key(name.encode("ascii"), auth if auth is not None else suite.initial_key2)
        if auth is not None:
            context.set_auth_param(auth)
        plaintext, status = context.decrypt(raw)
        if status == CryptoStatus.OK and len(plaintext) >= 7:
            return plaintext, suite
    return None, None


def describe(raw, name, auth=None):
    plaintext, suite = decrypt_candidates(raw, name, auth)
    key_context = "name+challenge" if auth is not None else "name+protocol-constant"
    if plaintext is None and auth is not None:
        plaintext, suite = decrypt_candidates(raw, name)
        key_context = "name+protocol-constant"
    result = {"length": len(raw), "decrypted": plaintext is not None,
              "sync2": raw[1] if len(raw) > 1 else None,
              "counter": int.from_bytes(raw[-2:], "big") if len(raw) >= 6 else None}
    if plaintext is not None:
        result.update({"suite": suite.label, "command": plaintext[5],
                       "index": plaintext[6], "payload_length": plaintext[2],
                       "key_context": key_context})
    return result


def parse_csv(message):
    values = [int(value) for value in message.strip().split(",")]
    if not values or len(values) > 512 or any(not 0 <= value <= 255 for value in values):
        raise ValueError("Invalid backend frame")
    return bytes(values)


async def run(address):
    report = {"schema": "gt3desk.wlbt-precomm-probe.v1", "vehicle_identifier_sent": False,
              "precomm_response_sent": False, "backend_ble_commands_forwarded": [],
              "stopped_before_pairing_or_authentication": True, "events": []}
    device = await asyncio.wait_for(BleakScanner.find_device_by_address(address, timeout=10), 15)
    if device is None or not device.name:
        raise ValueError("Scooter or exact BLE name not found")
    name = device.name
    report["vehicle_name_suffix"] = name[-4:]
    responses = asyncio.Queue()
    assembler = FrameAssembler()

    def receive(_characteristic, raw):
        for frame in assembler.feed(bytes(raw)):
            responses.put_nowait(frame)

    with PublicWebSocket() as ws:
        async with BleakClient(device, timeout=15) as client:
            await client.start_notify(NORDIC_UART.notify, receive)
            try:
                ws.send(json.dumps({"type": "device_info", "name": name}))
                report["vehicle_identifier_sent"] = True
                auth = None
                forwarded = False
                for _ in range(10):
                    message = await asyncio.to_thread(ws.receive)
                    try:
                        value = json.loads(message)
                    except ValueError:
                        raw = parse_csv(message)
                        descriptor = describe(raw, name, auth)
                        report["events"].append({"from": "backend", "frame": descriptor})
                        if forwarded:
                            report["stop_reason"] = "Next backend frame recorded, never forwarded to scooter"
                            break
                        plaintext, _suite = decrypt_candidates(raw, name)
                        if (plaintext is None or len(plaintext) != 7 or plaintext[0] != 0x5A
                                or plaintext[2] != 0 or plaintext[3:7] != bytes([0x3E, 0x04, 0x5B, 0x00])):
                            report["stop_reason"] = "Backend frame is not the allowlisted PRE_COMM"
                            break
                        await client.write_gatt_char(NORDIC_UART.write, raw, response=False)
                        report["backend_ble_commands_forwarded"].append("PRE_COMM 0x5B")
                        response = await asyncio.wait_for(responses.get(), 4)
                        reply, _suite = decrypt_candidates(response, name)
                        if (reply is None or len(reply) < 37 or reply[3:6] != bytes([0x04, 0x3E, 0x5B])
                                or reply[2] < 30):
                            report["stop_reason"] = "Unexpected scooter PRE_COMM response; not uploaded"
                            break
                        auth = reply[7:23]
                        report["stored_password_flag"] = reply[6]
                        ws.send(",".join(str(byte) for byte in response))
                        report["precomm_response_sent"] = True
                        forwarded = True
                    else:
                        # Record only message type/code. No server-provided
                        # serials, passwords or opaque data enter the report.
                        entry = {"from": "backend", "message_type": value.get("type")}
                        if "code" in value:
                            entry["code"] = value["code"]
                        report["events"].append(entry)
                        if value.get("type") == "error":
                            report["stop_reason"] = "Backend reported an error"
                            break
            finally:
                await client.stop_notify(NORDIC_UART.notify)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("address")
    parser.add_argument("--owner-approved-disclosure", action="store_true", required=True)
    args = parser.parse_args()

    async def bounded():
        async with asyncio.timeout(45):
            return await run(args.address)

    result = asyncio.run(bounded())
    output = Path(__file__).resolve().parents[1] / "research" / "wlbt" / "vehicle-precomm-probe.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=True, indent=2))
