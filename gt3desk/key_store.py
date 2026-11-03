"""Windows-user-bound storage for a newly negotiated BLE key.

Each attempt creates a new encrypted file before SET_PWD is sent. Earlier keys
are retained. Imported phone credentials continue to be memory-only.
"""

import base64
import ctypes
import hashlib
import json
import os
import re
import secrets
import sys
from dataclasses import dataclass, field
from pathlib import Path

from .data import parse_password, utc_now
from .windows_paths import local_app_data


class KeyStorageError(OSError):
    pass


class _Blob(ctypes.Structure):
    _fields_ = [("size", ctypes.c_uint32), ("data", ctypes.POINTER(ctypes.c_ubyte))]


def _dpapi(data: bytes, *, decrypt=False):
    if sys.platform != "win32":
        raise KeyStorageError("Die verschlüsselte Schlüsselsicherung benötigt Windows.")
    crypt = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    operation = crypt.CryptUnprotectData if decrypt else crypt.CryptProtectData
    operation.argtypes = [ctypes.POINTER(_Blob), ctypes.c_void_p, ctypes.POINTER(_Blob),
                          ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32, ctypes.POINTER(_Blob)]
    operation.restype = ctypes.c_int
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    buffer = ctypes.create_string_buffer(data)
    incoming = _Blob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    outgoing = _Blob()
    try:
        # CRYPTPROTECT_UI_FORBIDDEN, per-user protection. No machine-wide flag.
        if not operation(ctypes.byref(incoming), None, None, None, None, 0x01, ctypes.byref(outgoing)):
            raise KeyStorageError("Windows konnte den BLE-Schlüssel nicht verarbeiten. "
                                  "Es wird kein unverschlüsselter Ersatz gespeichert.")
        return ctypes.string_at(outgoing.data, outgoing.size)
    finally:
        ctypes.memset(buffer, 0, len(buffer))
        if outgoing.data:
            ctypes.memset(outgoing.data, 0, outgoing.size)
            kernel.LocalFree(ctypes.cast(outgoing.data, ctypes.c_void_p))


def default_key_directory():
    return storage_root() / "keys"


def storage_root():
    return local_app_data() / "SegwayMonitor"


def _local_only(path):
    resolved = Path(path).resolve()
    for variable in ("OneDrive", "OneDriveConsumer", "OneDriveCommercial"):
        cloud = os.environ.get(variable)
        if cloud and resolved.is_relative_to(Path(cloud).resolve()):
            raise KeyStorageError("Bitte einen lokalen Speicherort außerhalb von OneDrive verwenden.")
    return resolved


def _device_id(address):
    return hashlib.sha256(normalize_address(address).encode("ascii")).hexdigest()[:24]


def normalize_address(address):
    compact = re.sub(r"[\s:-]", "", address)
    if not re.fullmatch(r"[0-9a-fA-F]{12}", compact):
        raise ValueError("Die Bluetooth-Adresse ist ungültig.")
    return ":".join(compact[i:i+2].upper() for i in range(0, 12, 2))


def key_search_directories():
    # A local encrypted recovery copy may sit beside the application. It is
    # never part of the distributable ZIP or executable.
    app_folder = (Path(sys.executable).resolve().parent if getattr(sys, "frozen", False)
                  else Path(__file__).resolve().parents[1])
    local = storage_root().parent
    return list(dict.fromkeys((default_key_directory(), local / "GT3Desk" / "keys",
        local / "Programs" / "GT3Desk" / "0.2.2" / "keys", app_folder / "keys")))


@dataclass(repr=False)
class SavedKey:
    password: bytes = field(repr=False)
    device_name: str
    address: str
    state: str
    path: Path


def save_pending(password, device_name, address, *, directory=None):
    if len(password) != 16 or not device_name or len(device_name) > 128:
        raise ValueError("Ungültige lokale Kopplungsdaten.")
    record = {"schema": "gt3desk.key.v1", "password": password.hex(),
              "device_name": device_name, "address": normalize_address(address),
              "created_at": utc_now(), "state": "pending"}
    protected = _dpapi(json.dumps(record, ensure_ascii=False).encode("utf-8"))
    folder = Path(directory) if directory is not None else default_key_directory()
    _local_only(folder)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{_device_id(address)}-{secrets.token_hex(8)}.gt3key"
    envelope = {"schema": "gt3desk.dpapi.v1", "created_at": record["created_at"],
                "protected": base64.b64encode(protected).decode("ascii")}
    # Exclusive creation and fsync: do not replace an earlier valid key, and
    # return to the handshake only once the pending key is on disk.
    with path.open("x", encoding="utf-8") as output:
        json.dump(envelope, output)
        output.flush()
        os.fsync(output.fileno())
    loaded = load_saved_key(path, expected_address=address, expected_name=device_name)
    if loaded.password != password:
        raise KeyStorageError("Der gesicherte Schlüssel konnte nicht verifiziert werden.")
    return path


def load_saved_key(path, *, expected_address=None, expected_name=None):
    path = Path(path)
    if path.stat().st_size > 64 * 1024:
        raise ValueError("Die Schlüsseldatei ist zu groß.")
    try:
        envelope = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(envelope, dict) or envelope.get("schema") != "gt3desk.dpapi.v1":
            raise ValueError()
        blob = base64.b64decode(envelope["protected"], validate=True)
        obj = json.loads(_dpapi(blob, decrypt=True).decode("utf-8"))
        if (obj.get("schema") != "gt3desk.key.v1" or obj.get("state") not in ("pending", "imported", "confirmed")
                or not isinstance(obj.get("device_name"), str) or not obj["device_name"]
                or not isinstance(obj.get("address"), str)):
            raise ValueError()
        password = parse_password(obj["password"])
        if password is None:
            raise ValueError()
    except (KeyError, TypeError, ValueError, UnicodeError):
        raise ValueError("Die verschlüsselte Schlüsseldatei ist ungültig.") from None
    if expected_address and normalize_address(obj["address"]) != normalize_address(expected_address):
        raise ValueError("Die Schlüsseldatei gehört zu einem anderen Fahrzeug.")
    if expected_name and obj["device_name"] != expected_name:
        raise ValueError("Die Schlüsseldatei gehört zu einer anderen Fahrzeugkennung.")
    return SavedKey(password, obj["device_name"], obj["address"], obj["state"], path)


def latest_key(address, device_name, *, directory=None, confirmed_only=False):
    if directory is None:
        indexed = _indexed_key(address, device_name)
        if indexed is not None and (not confirmed_only or indexed.state in ("confirmed", "imported")):
            return indexed
    folders = [Path(directory)] if directory is not None else key_search_directories()
    candidates, errors = [], []
    for folder in folders:
        try:
            # Path.glob suppresses filesystem errors. Preserve read failures so
            # they are not misleadingly reported as a missing key.
            paths = [path for path in folder.iterdir()
                     if path.suffix.lower() == ".gt3key" and path.is_file()][:256]
        except FileNotFoundError:
            continue
        except OSError as error:
            errors.append(error)
            continue
        for path in paths:
            try:
                saved = load_saved_key(path, expected_address=address, expected_name=device_name)
                if not confirmed_only or saved.state in ("confirmed", "imported"):
                    candidates.append(saved)
            except OSError as error:
                errors.append(error)
            except ValueError:
                # Identity comes from protected contents, never the filename.
                continue
    if candidates:
        # An unconfirmed attempt must not hide an already working credential.
        return max(candidates, key=lambda saved: (saved.state == "confirmed", saved.path.stat().st_mtime_ns))
    if errors:
        raise errors[0]
    raise FileNotFoundError("Für dieses Fahrzeug wurde keine passende "
                            + ("bestätigte " if confirmed_only else "") + "Schlüsselsicherung gefunden.")


def mark_confirmed(path):
    _set_state(path, "confirmed")


def _set_state(path, state):
    key = load_saved_key(path)
    record = {"schema": "gt3desk.key.v1", "password": key.password.hex(),
              "device_name": key.device_name, "address": key.address,
              "created_at": utc_now(), "state": state}
    protected = _dpapi(json.dumps(record, ensure_ascii=False).encode("utf-8"))
    envelope = {"schema": "gt3desk.dpapi.v1", "created_at": record["created_at"],
                "protected": base64.b64encode(protected).decode("ascii")}
    temporary = key.path.with_suffix(f".{secrets.token_hex(8)}.tmp")
    with temporary.open("x", encoding="utf-8") as output:
        json.dump(envelope, output)
        output.flush()
        os.fsync(output.fileno())
    temporary.replace(key.path)


def _read_index():
    path = storage_root() / "key-index.json"
    try:
        if path.stat().st_size > 128 * 1024:
            return {}
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("schema") == "segway-monitor.key-index.v1" and isinstance(data.get("vehicles"), dict):
            return data["vehicles"]
    except (OSError, ValueError, AttributeError):
        pass
    return {}


def _indexed_key(address, device_name):
    entry = _read_index().get(normalize_address(address), {})
    filename = entry.get("key_file") if isinstance(entry, dict) else None
    if not isinstance(filename, str) or Path(filename).name != filename or not filename.endswith(".gt3key"):
        return None
    try:
        return load_saved_key(default_key_directory() / filename,
                              expected_address=address, expected_name=device_name)
    except (OSError, ValueError):
        return None


def _remember_file(saved):
    folder = _local_only(storage_root())
    folder.mkdir(parents=True, exist_ok=True)
    entries = _read_index()
    address = normalize_address(saved.address)
    entry = {"device_name": saved.device_name, "key_file": saved.path.name}
    if entries.get(address) == entry:
        return
    entries[address] = entry
    record = {"schema": "segway-monitor.key-index.v1", "vehicles": entries}
    temporary = folder / ("key-index-" + secrets.token_hex(8) + ".tmp")
    with temporary.open("x", encoding="utf-8") as output:
        json.dump(record, output, ensure_ascii=False)
        output.flush()
        os.fsync(output.fileno())
    temporary.replace(folder / "key-index.json")


def remember_credential(password, device_name, address, *, confirmed=False):
    """Persist an explicitly imported/verified credential and its exact location.

    Version-independent lookup uses a direct file reference, so relaunch does
    not depend on filename globbing or on the executable's working directory.
    """
    _local_only(default_key_directory())
    current = _indexed_key(address, device_name)
    state = "confirmed" if confirmed else "imported"
    if current is not None and current.password == password:
        if confirmed and current.state != "confirmed":
            _set_state(current.path, "confirmed")
            current = load_saved_key(current.path)
        _remember_file(current)
        return current
    path = save_pending(password, device_name, address)
    _set_state(path, state)
    saved = load_saved_key(path, expected_address=address, expected_name=device_name)
    _remember_file(saved)
    return saved


def adopt_saved_key(saved):
    return remember_credential(saved.password, saved.device_name, saved.address,
                               confirmed=saved.state == "confirmed")
