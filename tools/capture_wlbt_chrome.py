"""Observe only the owner's WLBT tab over an already authorized Android ADB.

Only Network.enable/disable are sent to the page's DevTools socket. No page
JavaScript, reload, Bluetooth command, tuning action, cookies or HTTP bodies.
Only CSV vehicle frames from the exact WLBT server, after a matching
device_info, are retained. Secrets are saved with Windows user DPAPI only.
"""

import argparse
import json
import re
import secrets
import select
import subprocess
import sys
import time
from pathlib import Path
from contextlib import ExitStack
from urllib.parse import urlsplit
from urllib.request import ProxyHandler, build_opener

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from gt3desk.data import utc_now
from gt3desk.key_store import _dpapi
from tools.local_devtools import LocalDevtoolsWebSocket

ADB = ROOT / "tools" / "android" / "platform-tools" / "adb.exe"


class CaptureNotReadyError(RuntimeError):
    def __init__(self, stage):
        super().__init__(stage)
        self.stage = stage


def is_wlbt_page(url):
    try:
        parsed = urlsplit(url)
        return (parsed.scheme == "https" and parsed.hostname == "wlbt.1dragon.de"
                and parsed.port in (None, 443) and not parsed.username and not parsed.password)
    except (TypeError, ValueError):
        return False


def is_wlbt_socket(url):
    try:
        parsed = urlsplit(url)
        return (parsed.scheme == "wss" and parsed.hostname == "ws-nb.1dragon.de"
                and parsed.port in (None, 443) and parsed.path in ("", "/")
                and not parsed.username and not parsed.password and not parsed.query)
    except (TypeError, ValueError):
        return False


class VehicleFrames:
    def __init__(self, vehicle_name):
        self.name = vehicle_name
        self.sockets = {}
        self.entries = []
        self.byte_count = 0
        self.summary_seen = False
        self.unexpected_action = False
        self.last_target_activity = 0
        self.diagnostics = {"websockets_created": 0, "matching_server_sockets": 0,
                            "websocket_messages_seen": 0, "unmatched_socket_messages": 0,
                            "device_info_seen": 0, "matching_device_info": 0,
                            "binary_messages_seen": 0}

    def accept(self, message):
        method, params = message.get("method"), message.get("params", {})
        ident = params.get("requestId")
        if method == "Network.webSocketCreated":
            self.diagnostics["websockets_created"] += 1
            if is_wlbt_socket(params.get("url", "")):
                # Binding belongs to one socket, not globally to this tab.
                self.sockets[ident] = False
                self.diagnostics["matching_server_sockets"] += 1
            return
        if method == "Network.webSocketClosed":
            self.sockets.pop(ident, None)
            return
        if method not in ("Network.webSocketFrameSent", "Network.webSocketFrameReceived"):
            return
        self.diagnostics["websocket_messages_seen"] += 1
        if ident not in self.sockets:
            self.diagnostics["unmatched_socket_messages"] += 1
            return
        response = params.get("response", {})
        payload = response.get("payloadData")
        if response.get("opcode") != 1:
            self.diagnostics["binary_messages_seen"] += 1
        if response.get("opcode") != 1 or not isinstance(payload, str) or len(payload) > 8192:
            return
        sent = method.endswith("Sent")
        try:
            data = json.loads(payload)
        except ValueError:
            data = None
        if isinstance(data, dict):
            if sent and data.get("type") == "device_info":
                self.diagnostics["device_info_seen"] += 1
                self.sockets[ident] = data.get("name") == self.name
                if self.sockets[ident]:
                    self.diagnostics["matching_device_info"] += 1
                return
            if not self.sockets[ident]:
                return
            kind = data.get("type")
            if not isinstance(kind, str) or not re.fullmatch(r"[a-zA-Z0-9_]{1,64}", kind):
                return
            if sent and kind in ("flash_firmware", "write_config", "set_config"):
                self.unexpected_action = True
            if not sent and kind == "device_summary":
                self.summary_seen = True
            # Keep only a type label. Excludes license keys and summary contents.
            if len(self.entries) >= 2000:
                raise ValueError("Target trace reached its capture limit")
            self.entries.append({"direction": "phone-to-server" if sent else "server-to-phone",
                                 "message_type": kind})
            self.last_target_activity = time.monotonic()
            return
        if not self.sockets[ident] or not re.fullmatch(r"\d{1,3}(?:,\d{1,3}){0,511}", payload):
            return
        values = [int(part) for part in payload.split(",")]
        if any(value > 255 for value in values):
            return
        if len(self.entries) >= 2000 or self.byte_count + len(values) > 512 * 1024:
            raise ValueError("Target trace reached its capture limit")
        self.byte_count += len(values)
        self.entries.append({"direction": "phone-to-server" if sent else "server-to-phone",
                             "time": params.get("timestamp"), "bytes_hex": bytes(values).hex()})
        self.last_target_activity = time.monotonic()

    def public_summary(self):
        return {"vehicle_frame_count": sum("bytes_hex" in row for row in self.entries),
                "vehicle_bytes": self.byte_count, "device_summary_seen": self.summary_seen,
                "unexpected_action_seen": self.unexpected_action,
                "diagnostics": self.diagnostics.copy()}


def adb(serial, *args):
    result = subprocess.run([str(ADB), "-s", serial, *args], capture_output=True, timeout=15)
    if result.returncode:
        raise CaptureNotReadyError("usb_adb_unavailable")
    return result.stdout.decode("utf-8", errors="replace").strip()


def discover(serial, port):
    opener = build_opener(ProxyHandler({}))
    try:
        with opener.open(f"http://127.0.0.1:{port}/json/list", timeout=5) as response:
            raw = response.read(2 * 1024 * 1024 + 1)
    except OSError:
        raise CaptureNotReadyError("chrome_socket_unavailable") from None
    if len(raw) > 2 * 1024 * 1024:
        raise ValueError("Browser inventory too large")
    pages = json.loads(raw)
    # Other tab titles, URLs and identifiers are never printed or persisted.
    targets = [page for page in pages if page.get("type") == "page"
               and is_wlbt_page(page.get("url", ""))]
    if not targets:
        raise CaptureNotReadyError("wlbt_tab_missing")
    if len(targets) > 8:
        raise CaptureNotReadyError("too_many_wlbt_tabs")
    return [page["webSocketDebuggerUrl"] for page in targets]


def observe(capture, urls, seconds):
    # Observe existing WLBT pages only; do not guess which duplicate is active
    # or require the owner to close tabs. Request IDs stay scoped per page.
    with ExitStack() as stack:
        active = {}
        for page_index, url in enumerate(urls):
            try:
                ws = stack.enter_context(LocalDevtoolsWebSocket(url))
                ws.send(json.dumps({"id": 1, "method": "Network.enable"}))
                deadline = time.monotonic() + 5
                enabled = False
                while time.monotonic() < deadline:
                    message = ws.receive(.25)
                    if message:
                        event = json.loads(message)
                        if event.get("id") == 1:
                            enabled = "error" not in event
                            break
                if enabled:
                    active[ws.socket] = (page_index, ws)
            except (OSError, EOFError, ValueError):
                continue
        if not active:
            raise CaptureNotReadyError("chrome_observer_unavailable")
        print(json.dumps({"status": "listening", "seconds": seconds,
                          "wlbt_pages_observed": len(active),
                          "instruction": "WLBT-Seite neu laden und nur Verbinden ausführen."}), flush=True)
        deadline = time.monotonic() + seconds
        last_progress = 0
        previous_summary = None
        end_reason = "time_limit"
        try:
            while active and time.monotonic() < deadline:
                ready = [sock for sock, (_, ws) in active.items() if ws.buffer]
                if not ready:
                    ready, _, _ = select.select(list(active), [], [], min(1, max(.01, deadline-time.monotonic())))
                for sock in ready:
                    page_index, ws = active[sock]
                    try:
                        message = ws.receive(.05)
                    except (OSError, EOFError):
                        del active[sock]
                        continue
                    if message:
                        event = json.loads(message)
                        params = event.get("params", {})
                        if "requestId" in params:
                            params["requestId"] = f"{page_index}/{params['requestId']}"
                        capture.accept(event)
                if capture.unexpected_action:
                    end_reason = "unexpected_user_action"
                    break
                now = time.monotonic()
                summary = capture.public_summary()
                if summary != previous_summary and now - last_progress >= 5:
                    print(json.dumps({"status": "progress", **summary}), flush=True)
                    previous_summary, last_progress = summary, now
                if capture.summary_seen and now - capture.last_target_activity >= 2:
                    end_reason = "device_summary_received"
                    break
            if not active:
                end_reason = "connection_closed"
        except ValueError:
            end_reason = "capture_limit_or_invalid_message"
        finally:
            for _, ws in active.values():
                try:
                    ws.send(json.dumps({"id": 2, "method": "Network.disable"}))
                except OSError:
                    pass
        return end_reason


def run(args):
    if not re.fullmatch(r"[A-Za-z0-9._:-]+", args.serial):
        raise ValueError("Invalid ADB serial")
    if not re.fullmatch(r"[A-Za-z0-9]{14}", args.vehicle_name):
        raise ValueError("Invalid Segway BLE name")
    # Validate encryption before observing any owner traffic.
    if _dpapi(_dpapi(b"GT3 Desk capture check"), decrypt=True) != b"GT3 Desk capture check":
        raise OSError("DPAPI self-check failed")
    port = adb(args.serial, "forward", "tcp:0", "localabstract:chrome_devtools_remote")
    if not re.fullmatch(r"\d{1,5}", port):
        raise ValueError("Invalid ADB forward port")
    capture = VehicleFrames(args.vehicle_name)
    try:
        urls = discover(args.serial, port)
        if args.check:
            return {"status": "ready", "matching_wlbt_tabs": len(urls), "capture_started": False}
        end_reason = observe(capture, urls, args.seconds)
        result = capture.public_summary()
        result.update({"status": "complete", "schema": "gt3desk.wlbt-chrome-capture.v1",
                       "end_reason": end_reason})
        if result["vehicle_frame_count"]:
            folder = ROOT / "research" / "wlbt" / "encrypted-traces"
            folder.mkdir(parents=True, exist_ok=True)
            name = f"wlbt-{time.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(4)}.dpapi"
            trace = {"schema": "gt3desk.wlbt-chrome-trace.v1", "created_at": utc_now(),
                     "vehicle_name": args.vehicle_name, "entries": capture.entries}
            with (folder / name).open("xb") as output:
                output.write(_dpapi(json.dumps(trace).encode("utf-8")))
            result["encrypted_trace"] = name
        summary_path = ROOT / "research" / "wlbt" / "capture-last-summary.json"
        summary_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        return result
    finally:
        try:
            adb(args.serial, "forward", "--remove", f"tcp:{port}")
        except (OSError, CaptureNotReadyError):
            pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("serial")
    parser.add_argument("--vehicle-name", required=True)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--seconds", type=int, choices=range(30, 301), default=180)
    args = parser.parse_args()
    try:
        print(json.dumps(run(args), ensure_ascii=True), flush=True)
    except CaptureNotReadyError as error:
        print(json.dumps({"status": "not_ready", "stage": error.stage}))
        return 1
    except (OSError, ValueError, KeyError) as error:
        # Do not echo page data, frame bytes or server-provided strings.
        print(json.dumps({"status": "failed", "error_type": type(error).__name__,
                          "message": "Chrome/WLBT-Verbindung nicht bereit; kein App-Start oder Fahrzeugbefehl."}))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
