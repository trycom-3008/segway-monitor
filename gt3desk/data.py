"""Typed readings and credential-free exports."""

import csv
import io
import json
import re
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path

from . import APP_NAME, __version__
from .catalog import CATALOG, PROFILE_NOTE, SOURCE, ReadSpec
from .parameters import component_name, parameter_info, parameter_unit


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


@dataclass
class Reading:
    key: str
    label: str
    board: str
    index: int
    value: object
    unit: str
    raw_hex: str
    status: str
    time: str


def decode_reading(spec: ReadSpec, raw: bytes | None) -> Reading:
    now = utc_now()
    base = dict(key=spec.key, label=parameter_info(spec).label, board=spec.board,
                index=spec.index, unit=parameter_unit(spec), raw_hex=(raw or b"").hex(), time=now)
    if raw is None:
        return Reading(**base, value=None, status="Keine Antwort")
    if len(raw) < spec.length:
        return Reading(**base, value=None, status="Antwort zu kurz")
    payload = raw[:spec.length]
    if spec.kind == "ascii":
        value = payload.rstrip(b"\x00").decode("ascii", errors="replace").strip()
    elif spec.kind == "hex":
        value = payload.hex(" ")
    elif spec.kind == "u16_array":
        value = [round(int.from_bytes(payload[i:i+2], "little") * spec.scale, 6)
                 for i in range(0, spec.length, 2)]
    else:
        integer = int.from_bytes(payload, "little", signed=spec.kind.startswith("i"))
        if spec.kind == "version":
            value = f"{integer >> 8}.{(integer >> 4) & 15}.{integer & 15}"
        elif spec.kind == "date":
            try:
                value = date(2000 + (integer >> 9), (integer >> 5) & 15, integer & 31).isoformat()
            except ValueError:
                return Reading(**base, value=None, status="Datum unklar")
        else:
            value = integer if spec.scale == 1.0 else round(integer * spec.scale, 6)
    numbers = value if isinstance(value, list) else [value]
    def out_of_range(number):
        return isinstance(number, (int, float)) and (
            (spec.minimum is not None and number < spec.minimum)
            or (spec.maximum is not None and number > spec.maximum)
        )
    invalid_count = sum(out_of_range(number) for number in numbers)
    if invalid_count:
        if isinstance(value, list) and invalid_count < len(value):
            # Keep plausible measured channels; never display an invalid
            # channel as a temperature or fabricate a replacement value.
            value = [None if out_of_range(number) else number for number in value]
            return Reading(**base, value=value,
                           status=f"Teilweise gelesen · {invalid_count} Kanäle außerhalb Profilbereich")
        return Reading(**base, value=None, status="Außerhalb Profilbereich")
    return Reading(**base, value=value, status="Gelesen")


def format_value(value):
    if value is None:
        return "—"
    if isinstance(value, list):
        return " / ".join(format_value(item) for item in value)
    if isinstance(value, float):
        return f"{value:.3f}".rstrip("0").rstrip(".").replace(".", ",")
    return str(value)


def parse_password(text: str) -> bytes | None:
    cleaned = re.sub(r"\s+", "", text)
    if not cleaned:
        return None
    if not re.fullmatch(r"[0-9a-fA-F]{32}", cleaned):
        raise ValueError("Der BLE-Schlüssel muss aus genau 32 Hex-Zeichen bestehen (16 Bytes).")
    return bytes.fromhex(cleaned)


@dataclass(repr=False)
class ImportedCredential:
    password: bytes
    device_name: str | None = None


def import_credential(path: Path) -> ImportedCredential:
    if path.stat().st_size > 256 * 1024:
        raise ValueError("Die Schlüsseldatei ist zu groß (maximal 256 KB).")
    try:
        obj = json.loads(path.read_text(encoding="utf-8-sig"))
    except (ValueError, UnicodeError):
        raise ValueError("Die Datei enthält kein gültiges JSON.") from None
    if not isinstance(obj, dict) or not isinstance(obj.get("password"), str):
        raise ValueError('Erwartet wird ein JSON-Objekt mit dem Feld "password" (32 Hex-Zeichen).')
    password = parse_password(obj["password"])
    if password is None:
        raise ValueError("Die Schlüsseldatei enthält einen leeren Schlüssel.")
    device_name = obj.get("device_name") or obj.get("serial")
    if device_name is not None and (not isinstance(device_name, str) or len(device_name) > 128):
        raise ValueError("Die Fahrzeugkennung in der Datei ist ungültig.")
    return ImportedCredential(password, device_name)


def make_report(device: dict, gatt: list, readings: dict[str, Reading], access: str):
    from .models import GT3_D, MODELS
    # Explicit allowlists: no credential, handshake challenge or notification
    # frames are included, even if callers extend their internal state later.
    allowed_device = {k: device[k] for k in ("name", "address", "rssi", "services", "model", "model_name") if k in device}
    model = MODELS.get(device.get("model"), GT3_D)
    rows = []
    for spec in model.registers:
        if spec.key in readings:
            row = asdict(readings[spec.key])
            row.update({"component": component_name(spec.board), "technical_name": spec.name,
                        "description": parameter_info(spec).description})
            rows.append(row)
    return {
        "schema": "segway-monitor.report.v1", "app_name": APP_NAME, "app_version": __version__,
        "exported_at": utc_now(), "device": allowed_device, "access": access,
        "profile": device.get("model", "gt3_d"), "profile_note": PROFILE_NOTE,
        "source": SOURCE, "gatt": gatt,
        "readings": rows,
        "not_read": [s.key for s in model.registers if s.key not in readings],
    }


def write_json(path: Path, report: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def _safe_csv(value):
    text = str(value)
    # Text cells cannot become formulas when the CSV is opened in Excel.
    return "'" + text if text.lstrip().startswith(("=", "+", "-", "@")) else text


def write_csv(path: Path, report: dict):
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, delimiter=";")
    writer.writerow(["Zeit UTC", "Baugruppe", "Modul", "Technischer Name", "Register", "Bezeichnung",
                     "Erklärung", "Wert", "Einheit", "Status", "Rohbytes"])
    for row in report["readings"]:
        value = row["value"]
        display = json.dumps(value, ensure_ascii=False) if isinstance(value, list) else ("" if value is None else value)
        cells = [row["time"], row.get("component", component_name(row["board"])), row["board"],
                 row.get("technical_name", row["key"]), f"0x{row['index']:02X}", row["label"], row.get("description", ""),
                 display, row["unit"], row["status"], row["raw_hex"]]
        writer.writerow([_safe_csv(cell) if isinstance(cell, str) else cell for cell in cells])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stream.getvalue(), encoding="utf-8-sig")
