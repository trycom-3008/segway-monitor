"""Bounded backend research with a fictional vehicle, never real BLE hardware.

Uses the public browser protocol found in the site's own JavaScript. Sends
only TEST0000000001 and synthetic PRE_COMM data. Stops at the next handshake
command; it neither acknowledges pairing nor requests tuning or a license.
"""

import argparse
import base64
import hashlib
import json
import os
import socket
import ssl
import struct
import sys
import time
from pathlib import Path

from scootscoot.crypto import CryptoStatus, NbCrypto
from scootscoot.profiles.types import ENC2_GEN2, ENC2_GEN3


class PublicWebSocket:
    def __enter__(self):
        self.socket = ssl.create_default_context().wrap_socket(
            socket.create_connection(("ws-nb.1dragon.de", 443), timeout=10),
            server_hostname="ws-nb.1dragon.de")
        self.socket.settimeout(5)
        self.reader = self.socket.makefile("rb")
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        headers = (
            "GET / HTTP/1.1\r\nHost: ws-nb.1dragon.de\r\nUpgrade: websocket\r\n"
            "Connection: Upgrade\r\nSec-WebSocket-Version: 13\r\n"
            "Origin: https://wlbt.1dragon.de\r\n"
            f"Sec-WebSocket-Key: {key}\r\n\r\n")
        self.socket.sendall(headers.encode("ascii"))
        status = self.reader.readline(4096).decode("ascii").strip()
        received = {}
        for _ in range(64):
            line = self.reader.readline(4096)
            if line == b"\r\n":
                break
            if not line:
                raise ValueError("Connection closed during HTTP upgrade")
            name, value = line.decode("latin-1").split(":", 1)
            received[name.lower()] = value.strip()
        expected = base64.b64encode(hashlib.sha1(
            (key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode("ascii")
        ).digest()).decode("ascii")
        if " 101 " not in status or received.get("sec-websocket-accept") != expected:
            raise ValueError(f"Public WebSocket upgrade refused: {status}")
        return self

    def send_frame(self, opcode, payload):
        if len(payload) > 65535:
            raise ValueError("Probe frame too large")
        prefix = bytes([0x80 | opcode])
        prefix += (bytes([0x80 | len(payload)]) if len(payload) < 126
                   else bytes([0xFE]) + struct.pack("!H", len(payload)))
        mask = os.urandom(4)
        self.socket.sendall(prefix + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(payload)))

    def send(self, text):
        self.send_frame(1, text.encode("utf-8"))

    def exact(self, length):
        data = self.reader.read(length)
        if len(data) != length:
            raise EOFError("WebSocket closed")
        return data

    def receive(self):
        for _ in range(8):
            first, second = self.exact(2)
            length = second & 0x7F
            if length == 126:
                length = struct.unpack("!H", self.exact(2))[0]
            elif length == 127:
                length = struct.unpack("!Q", self.exact(8))[0]
            if length > 262144:
                raise ValueError("Server frame exceeds probe limit")
            mask = self.exact(4) if second & 0x80 else None
            payload = self.exact(length)
            if mask:
                payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
            opcode = first & 0x0F
            if opcode == 8:
                raise EOFError("Server closed WebSocket")
            if opcode == 9:
                self.send_frame(10, payload)
                continue
            if opcode != 1 or not first & 0x80:
                raise ValueError("Unexpected server message type")
            return payload.decode("utf-8")
        raise ValueError("Too many WebSocket control messages")

    def __exit__(self, *_args):
        try:
            self.send_frame(8, b"\x03\xe8")
        except OSError:
            pass
        self.reader.close()
        self.socket.close()


def run(stored):
    name = "TEST0000000001"
    auth = hashlib.sha256(b"GT3 Desk synthetic research challenge").digest()[:16]
    report = {"synthetic_only": True, "real_bluetooth_used": False,
              "endpoint": "wss://ws-nb.1dragon.de:443/", "stored_password_flag": stored,
              "messages": []}
    context = None
    initial_suite = None
    phase = 0
    with PublicWebSocket() as ws:
        ws.send(json.dumps({"type": "device_info", "name": name}))
        deadline = time.monotonic() + 15
        for _ in range(8):
            if time.monotonic() > deadline:
                break
            try:
                message = ws.receive()
            except (TimeoutError, EOFError) as error:
                report["end"] = type(error).__name__
                break
            try:
                value = json.loads(message)
            except ValueError:
                try:
                    raw = bytes(int(value.strip()) for value in message.split(","))
                except (ValueError, OverflowError):
                    report["messages"].append({"kind": "unrecognized_text"})
                    break
                entry = {"kind": "ble_frame", "length": len(raw)}
                if phase == 0:
                    for suite in (ENC2_GEN2, ENC2_GEN3):
                        candidate = NbCrypto(ecb_input=suite.ecb_input)
                        candidate.set_key(name.encode("ascii"), suite.initial_key2)
                        plaintext, status = candidate.decrypt(raw)
                        if status == CryptoStatus.OK and len(plaintext) >= 7:
                            context = candidate
                            initial_suite = suite
                            entry.update({"suite": suite.label, "command": plaintext[5], "index": plaintext[6]})
                            break
                    if context is None or plaintext[5] != 0x5B:
                        report["messages"].append(entry)
                        break
                    # A fictional response only. No local scooter is contacted.
                    response = bytes([0x5A, raw[1], 30, 0x04, 0x3E, 0x5B, stored]) + auth + name.encode("ascii")
                    ws.send(",".join(str(byte) for byte in context.encrypt(response)))
                    context.set_auth_param(auth)
                    context.set_key(name.encode("ascii"), auth)
                    phase = 1
                else:
                    plaintext, status = context.decrypt(raw)
                    entry["valid_name_challenge_key"] = status == CryptoStatus.OK
                    if status != CryptoStatus.OK:
                        initial = NbCrypto(ecb_input=initial_suite.ecb_input)
                        initial.set_key(name.encode("ascii"), initial_suite.initial_key2)
                        plaintext, status = initial.decrypt(raw)
                        entry["valid_initial_key"] = status == CryptoStatus.OK
                    if status == CryptoStatus.OK and len(plaintext) >= 7:
                        entry.update({"command": plaintext[5], "index": plaintext[6],
                                      "payload_length": plaintext[2]})
                    report["messages"].append(entry)
                    report["end"] = "Stopped before pairing acknowledgement"
                    break
                report["messages"].append(entry)
            else:
                report["messages"].append({"kind": "json", "data": value})
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stored", type=int, choices=(0, 1), default=1)
    args = parser.parse_args()
    result = run(args.stored)
    output = Path(__file__).resolve().parents[1] / "research" / "wlbt" / f"synthetic-backend-{args.stored}.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=True, indent=2))
