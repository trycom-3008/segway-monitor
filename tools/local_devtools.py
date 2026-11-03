"""Small bounded WebSocket transport, exclusively for loopback DevTools.

No browser UI commands, page JavaScript, proxy, cookies or external hosts.
"""

import base64
import hashlib
import os
import select
import socket
import struct
import time
from urllib.parse import urlsplit


class LocalDevtoolsWebSocket:
    LIMIT = 2 * 1024 * 1024

    def __init__(self, url):
        parsed = urlsplit(url)
        if (parsed.scheme != "ws" or parsed.hostname not in ("localhost", "127.0.0.1")
                or not parsed.port or parsed.username or parsed.password or parsed.query
                or parsed.fragment or not parsed.path.startswith("/devtools/page/")
                or any(char in parsed.path for char in "\r\n ")):
            raise ValueError("Only a local page-specific DevTools socket is allowed")
        self.port = parsed.port
        self.path = parsed.path
        self.socket = None
        self.buffer = bytearray()
        self.fragments = bytearray()
        self.fragmenting = False

    def __enter__(self):
        self.socket = socket.create_connection(("127.0.0.1", self.port), timeout=5)
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        self.socket.sendall((f"GET {self.path} HTTP/1.1\r\n"
                             f"Host: localhost:{self.port}\r\n"
                             "Upgrade: websocket\r\nConnection: Upgrade\r\n"
                             "Sec-WebSocket-Version: 13\r\n"
                             f"Sec-WebSocket-Key: {key}\r\n\r\n").encode("ascii"))
        try:
            while b"\r\n\r\n" not in self.buffer:
                chunk = self.socket.recv(4096)
                if not chunk or len(self.buffer) + len(chunk) > 65536:
                    raise OSError("Invalid local DevTools upgrade")
                self.buffer.extend(chunk)
            head, rest = bytes(self.buffer).split(b"\r\n\r\n", 1)
            self.buffer[:] = rest
            lines = head.decode("latin-1").split("\r\n")
            headers = {name.lower(): value.strip() for name, value in
                       (line.split(":", 1) for line in lines[1:])}
            expected = base64.b64encode(hashlib.sha1(
                (key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode("ascii")
            ).digest()).decode("ascii")
            if " 101 " not in lines[0] or headers.get("sec-websocket-accept", "").strip() != expected:
                raise OSError("Local DevTools upgrade refused")
            self.socket.setblocking(False)
            return self
        except BaseException:
            self.socket.close()
            raise

    def send_frame(self, opcode, payload):
        if len(payload) > 65535:
            raise ValueError("DevTools command too large")
        header = bytes([0x80 | opcode])
        header += (bytes([0x80 | len(payload)]) if len(payload) < 126
                   else b"\xfe" + struct.pack("!H", len(payload)))
        mask = os.urandom(4)
        packet = header + mask + bytes(byte ^ mask[i % 4] for i, byte in enumerate(payload))
        self.socket.settimeout(5)
        try:
            self.socket.sendall(packet)
        finally:
            self.socket.setblocking(False)

    def send(self, text):
        self.send_frame(1, text.encode("utf-8"))

    def _frame(self):
        if len(self.buffer) < 2:
            return None
        first, second = self.buffer[:2]
        if first & 0x70 or second & 0x80:
            raise ValueError("Unexpected WebSocket extensions or masked server frame")
        length, offset = second & 0x7f, 2
        if length in (126, 127):
            size = 2 if length == 126 else 8
            if len(self.buffer) < offset + size:
                return None
            length = int.from_bytes(self.buffer[offset:offset+size], "big")
            offset += size
        if length > self.LIMIT:
            raise ValueError("DevTools message exceeds capture bound")
        if len(self.buffer) < offset + length:
            return None
        payload = bytes(self.buffer[offset:offset+length])
        del self.buffer[:offset+length]
        return first & 0x0f, bool(first & 0x80), payload

    def receive(self, timeout=1):
        deadline = time.monotonic() + timeout
        while True:
            frame = self._frame()
            if frame is not None:
                opcode, final, payload = frame
                if opcode == 8:
                    raise EOFError("DevTools disconnected")
                if opcode == 9:
                    self.send_frame(10, payload)
                    continue
                if opcode == 10:
                    continue
                if opcode == 1 and not self.fragmenting:
                    self.fragments[:] = payload
                elif opcode == 0 and self.fragmenting:
                    self.fragments.extend(payload)
                else:
                    raise ValueError("Unexpected DevTools WebSocket message")
                if len(self.fragments) > self.LIMIT:
                    raise ValueError("DevTools fragmented message too large")
                self.fragmenting = not final
                if final:
                    result = self.fragments.decode("utf-8")
                    self.fragments.clear()
                    return result
                continue
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None
            ready, _, _ = select.select([self.socket], [], [], remaining)
            if not ready:
                return None
            chunk = self.socket.recv(65536)
            if not chunk:
                raise EOFError("DevTools disconnected")
            self.buffer.extend(chunk)

    def __exit__(self, *_args):
        try:
            self.send_frame(8, b"\x03\xe8")
        except OSError:
            pass
        self.socket.close()
