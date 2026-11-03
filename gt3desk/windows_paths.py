"""Stable Windows user folders, independent of inherited package environments.

SHGetKnownFolderPath with KF_FLAG_NO_PACKAGE_REDIRECTION returns the current
user's normal local app-data folder. It does not change filesystem permissions.
"""

import ctypes
import os
import sys
import uuid
from pathlib import Path


class _Guid(ctypes.Structure):
    _fields_ = [("data1", ctypes.c_uint32), ("data2", ctypes.c_uint16),
                ("data3", ctypes.c_uint16), ("data4", ctypes.c_ubyte * 8)]


def local_app_data():
    if sys.platform == "win32":
        folder = _Guid.from_buffer_copy(uuid.UUID("F1B32785-6FBA-4FCF-9D55-7B8E7F157091").bytes_le)
        shell = ctypes.WinDLL("shell32", use_last_error=True)
        ole = ctypes.WinDLL("ole32", use_last_error=True)
        shell.SHGetKnownFolderPath.argtypes = [ctypes.POINTER(_Guid), ctypes.c_uint32,
                                               ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
        shell.SHGetKnownFolderPath.restype = ctypes.c_long
        ole.CoTaskMemFree.argtypes = [ctypes.c_void_p]
        pointer = ctypes.c_void_p()
        try:
            status = shell.SHGetKnownFolderPath(ctypes.byref(folder), 0x00010000, None, ctypes.byref(pointer))
            if status == 0 and pointer.value:
                return Path(ctypes.wstring_at(pointer))
        finally:
            if pointer.value:
                ole.CoTaskMemFree(pointer)
        # A regular user profile remains preferable to a package-relative env
        # value if shell folder retrieval is unavailable.
        return Path.home() / "AppData" / "Local"
    return Path(os.environ.get("LOCALAPPDATA") or Path.home() / ".local" / "share")
