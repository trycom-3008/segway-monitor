"""Prepare a public source tree from an explicit allowlist, never the workspace."""

import hashlib
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from gt3desk import EXE_NAME, __version__

ROOT_FILES = (
    ".gitignore", ".gitattributes", "LICENSE", "NOTICE", "README.md",
    "RELEASE_NOTES.md", "GITHUB_RELEASE.md", "PARAMETER.md", "build.ps1",
    "requirements.txt", "requirements-build.txt", "requirements-lock.txt",
    "credential-format.example.txt", "Segway-Monitor-starten.cmd",
    "run_segway_monitor.py", "assets/version-info.txt",
)
TOOLS = (
    "collect_licenses.py", "export_parameter_reference.py", "package_release.py",
    "prepare_public_release.py", "install_monitor_local.py",
    # Generic utilities needed by the existing offline regression tests.
    # Actual captures, browser assets and Android platform tools are excluded.
    "capture_wlbt_chrome.py", "local_devtools.py", "probe_wlbt_vehicle.py",
    "probe_wlbt_backend.py", "analyze_wlbt_trace.py",
)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source = ROOT / "release" / f"Segway-Monitor-v{__version__}"
    files = [ROOT / name for name in ROOT_FILES]
    files += [ROOT / "tools" / name for name in TOOLS]
    files += sorted((ROOT / "gt3desk").glob("*.py"))
    files += sorted((ROOT / "tests").glob("test_*.py"))
    files += sorted(path for path in (ROOT / "licenses").rglob("*") if path.is_file())
    expected = {path.relative_to(ROOT).as_posix() for path in files}
    source.mkdir(parents=True, exist_ok=True)
    unexpected = [path.relative_to(source).as_posix() for path in source.rglob("*")
                  if path.is_file() and ".git" not in path.relative_to(source).parts
                  and "__pycache__" not in path.relative_to(source).parts
                  and path.relative_to(source).as_posix() not in expected]
    if unexpected:
        raise ValueError("Unexpected files in public staging directory; review before publication")
    manifest = []
    for path in files:
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(ROOT):
            raise ValueError("Unexpected source file location")
        relative = path.relative_to(ROOT)
        if path.suffix.lower() in (".gt3key", ".dpapi", ".exe", ".dll"):
            raise ValueError("Private material or executable in source allowlist")
        data = path.read_bytes()
        if relative.parts[0] != "licenses":
            text = data.decode("utf-8-sig")
            # Only the synthetic model fixture belongs in public source.
            serials = re.findall(r"\b03SDG\d{4}[A-Z]\d{4}\b", text)
            if any(serial != "03SDG0000A0001" for serial in serials) or re.search(r"[A-Z]:\\Users\\[^\\\s]+", text):
                raise ValueError("Owner-specific identifier in public source")
            if re.search(r"github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", text):
                raise ValueError("Possible credential in public source")
        output = source / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, output)
        manifest.append({"path": relative.as_posix(), "sha256": sha256(output)})

    archive = ROOT / f"Segway-Monitor-Source-v{__version__}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as package:
        for entry in manifest:
            package.write(source / entry["path"], entry["path"])
    with zipfile.ZipFile(archive) as package:
        if package.testzip() is not None or set(package.namelist()) != expected:
            raise ValueError("Source archive verification failed")
    windows_archive = ROOT / f"Segway-Monitor-Windows-v{__version__}.zip"
    with zipfile.ZipFile(windows_archive) as package:
        if package.testzip() is not None:
            raise ValueError("Windows archive verification failed")
        if hashlib.sha256(package.read(EXE_NAME)).hexdigest() != sha256(ROOT / f"dist-v{__version__}" / EXE_NAME):
            raise ValueError("Windows executable mismatch")
        for required in ("LICENSE", "NOTICE", "README.md", "RELEASE_NOTES.md", "PARAMETER.md"):
            if package.read(required) != (ROOT / required).read_bytes():
                raise ValueError("Public documentation differs from source")
    (ROOT / "SHA256SUMS.txt").write_text("".join(
        f"{sha256(path)}  {path.name}\n" for path in (windows_archive, archive)), encoding="ascii")
    manifest_path = ROOT / "release" / f"manifest-v{__version__}.json"
    manifest_path.write_text(json.dumps({"version": __version__, "files": manifest}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"source_tree": str(source), "source_files": len(manifest),
                      "source_archive": archive.name, "checksums": "SHA256SUMS.txt",
                      "manifest": str(manifest_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
