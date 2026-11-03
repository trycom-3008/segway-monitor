"""Explicit model registry. A generic UART or brand-like name is insufficient."""

import re
from dataclasses import dataclass

from scootscoot.profiles.types import (
    Board, BoardRole, DeviceProfile, ENC2_GEN2, NINEBOT_CUSTOM, NORDIC_UART,
)
from .catalog import CATALOG, ReadSpec


class UnsupportedVehicle(ValueError):
    pass


@dataclass(frozen=True)
class MonitorModel:
    key: str
    name: str
    serial_pattern: str
    profile: DeviceProfile
    cell_groups: int
    boards: tuple[str, ...] = ("VCU", "BMS1", "BLE", "MCU", "TFT")
    registers: tuple[ReadSpec, ...] = CATALOG

    @property
    def by_key(self):
        return {spec.key: spec for spec in self.registers}

    def matches(self, name, services=()):
        if not isinstance(name, str) or not re.fullmatch(self.serial_pattern, name):
            return False
        advertised = {str(service).lower() for service in services}
        return not advertised or bool(advertised & SEGWAY_SERVICES)


SEGWAY_SERVICES = frozenset((NORDIC_UART.service.lower(), NINEBOT_CUSTOM.service.lower()))
GT3_D = MonitorModel(
    key="gt3_d", name="GT3 D", serial_pattern=r"03SDG\d{4}[A-Z]\d{4}", cell_groups=13,
    profile=DeviceProfile(
        key="gt3_d", name="Segway GT3 D", hardware_id=257, server_id=10257,
        crypto=ENC2_GEN2, transports=(NORDIC_UART, NINEBOT_CUSTOM),
        boards=(Board(BoardRole.BLE, 0x04, True),), registers=(), poll=(), identity=(),
    ),
)
MODELS = {GT3_D.key: GT3_D}


def recognize_model(name, services=()):
    return next((model for model in MODELS.values() if model.matches(name, services)), None)


def require_model(name, services=()):
    model = recognize_model(name, services)
    if model is None:
        raise UnsupportedVehicle("Für dieses Gerät ist kein unterstütztes Segway-Modellprofil verfügbar.")
    return model
