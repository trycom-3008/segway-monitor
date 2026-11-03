"""Package only the built application directory; never owner credentials."""

import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from gt3desk import EXE_NAME, __version__


def main():
    folder = ROOT / f"dist-v{__version__}"
    if not (folder / EXE_NAME).is_file():
        raise FileNotFoundError("Build the EXE first")
    for required in ("LICENSE", "NOTICE", "README.md", "RELEASE_NOTES.md", "PARAMETER.md"):
        if not (folder / required).is_file():
            raise FileNotFoundError(f"Required release file missing: {required}")
    paths = sorted(path for path in folder.rglob("*") if path.is_file())
    for path in paths:
        relative = path.relative_to(folder)
        if relative.parts[0].lower() in ("keys", "reports", "research") or path.name == "key-index.json":
            raise ValueError("Owner data and research files must not enter a public release")
        if path.is_symlink() or not path.resolve().is_relative_to(folder.resolve()):
            raise ValueError("Unexpected release file location")
        if path.suffix.lower() in (".dpapi", ".gt3key"):
            raise ValueError("Private owner material must not enter a release")
    archive = ROOT / f"Segway-Monitor-Windows-v{__version__}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as output:
        for path in paths:
            output.write(path, path.relative_to(folder).as_posix())
    with zipfile.ZipFile(archive) as output:
        if output.testzip() is not None:
            raise OSError("Release CRC check failed")
    print(f"Release erstellt und CRC geprüft: {archive.name} ({archive.stat().st_size} Bytes, {len(paths)} Dateien)")


if __name__ == "__main__":
    main()
