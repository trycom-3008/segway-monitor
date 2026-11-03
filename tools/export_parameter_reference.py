"""Generate a public reference from the same descriptions used by the UI."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from gt3desk import __version__
from gt3desk.catalog import CATALOG, SOURCE
from gt3desk.parameters import component_name, parameter_info, parameter_unit


def main():
    lines = [f"# Segway Monitor {__version__} · Parameterreferenz", "",
             "Modell: GT3 D. Das Hauptprofil umfasst 87 Felder; 19 weitere gehören zu einem zweiten BMS.", "",
             "Die Anwendung zeigt die zusätzlichen BMS2-Felder nach eindeutiger Erkennung an.", "",
             "| Technischer Name | Anzeige | Baugruppe | Einheit / Format | Erklärung |",
             "| --- | --- | --- | --- | --- |"]
    for spec in CATALOG:
        entry = parameter_info(spec)
        cells = (spec.key, entry.label, component_name(spec.board), parameter_unit(spec), entry.description)
        lines.append("| " + " | ".join(cell.replace("|", "\\|").replace("\n", " ") for cell in cells) + " |")
    lines += ["", f"Registergrundlage: [GT3-Protokollreferenz]({SOURCE}).", "",
              "Einzelne Herstellerkodierungen sind noch nicht vollständig zugeordnet. Die Beschreibungen benennen dies beim betreffenden Feld; die Rohdaten bleiben in Details und Export verfügbar.", ""]
    (ROOT / "PARAMETER.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
