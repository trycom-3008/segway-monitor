"""Local installation without cloud-bound credentials or executable-relative keys."""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from gt3desk import EXE_NAME, __version__
from gt3desk.key_store import _local_only, adopt_saved_key, latest_key
from gt3desk.models import require_model
from gt3desk.windows_paths import local_app_data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--address")
    parser.add_argument("--vehicle-name")
    args = parser.parse_args()
    if bool(args.address) != bool(args.vehicle_name):
        parser.error("Address and vehicle name must be given together")
    local = _local_only(local_app_data())
    parent = _local_only(local / "Programs" / "SegwayMonitor")
    destination = _local_only(parent / __version__)
    if not destination.is_relative_to(parent) or not destination.is_relative_to(local):
        raise ValueError("Unexpected installation target")
    source = ROOT / f"dist-v{__version__}"
    if not (source / EXE_NAME).is_file():
        raise FileNotFoundError("Build the release first")
    for path in source.rglob("*"):
        if path.is_symlink() or not path.resolve().is_relative_to(source.resolve()):
            raise ValueError("Unexpected build location")
        if path.suffix.lower() in (".gt3key", ".dpapi"):
            raise ValueError("Public release must not contain owner credentials")
    shutil.copytree(source, destination, dirs_exist_ok=True)
    registered = False
    if args.address:
        require_model(args.vehicle_name)
        saved = latest_key(args.address, args.vehicle_name, confirmed_only=True)
        adopted = adopt_saved_key(saved)
        registered = adopted.state in ("confirmed", "imported")
    print(json.dumps({"application": str(destination / EXE_NAME),
                      "key_registered_in_local_user_profile": registered}, ensure_ascii=True))


if __name__ == "__main__":
    main()
