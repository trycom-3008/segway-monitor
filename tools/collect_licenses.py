"""Copy the installed distributions' original license and notice files."""

import importlib.metadata
import shutil
import subprocess
import sys
from pathlib import Path


root = Path(__file__).resolve().parents[1]
target = root / "licenses"
target.mkdir(exist_ok=True)
summary = ["# Gebündelte Drittanbieter-Komponenten", "", "Originale Lizenz- und Notice-Texte stehen in den jeweiligen Unterordnern.", ""]
for distribution in sorted(importlib.metadata.distributions(), key=lambda item: item.metadata["Name"].lower()):
    name = distribution.metadata["Name"]
    summary.append(f"- {name} {distribution.version}")
    for entry in distribution.files or ():
        if not any(token in entry.name.lower() for token in ("license", "licence", "copying", "notice", "copyright")):
            continue
        if ".." in entry.parts:
            continue
        source = Path(distribution.locate_file(entry))
        if source.is_file():
            output = target / name / entry
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, output)
base = Path(sys.base_prefix)
for filename in ("LICENSE.txt", "LICENSE"):
    if (base / filename).is_file():
        shutil.copyfile(base / filename, target / ("Python-" + filename))
if (base / "tcl").is_dir():
    for source in (base / "tcl").rglob("license.terms"):
        output = target / "Tcl-Tk" / source.relative_to(base / "tcl")
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, output)
(target / "THIRD-PARTY.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
frozen = subprocess.check_output([sys.executable, "-m", "pip", "freeze", "--all"], text=True)
(root / "requirements-lock.txt").write_text(frozen, encoding="utf-8")
print(f"Lizenztexte gesammelt: {target}")
