param([string]$OutputDirectory = 'dist-v1.0.0')
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$taskDistRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot $OutputDirectory))
$taskWorkspacePrefix = $PSScriptRoot.TrimEnd('\') + '\'
if (-not $taskDistRoot.StartsWith($taskWorkspacePrefix, [StringComparison]::OrdinalIgnoreCase)) { throw 'Der Ausgabeordner muss innerhalb dieses Projekts liegen.' }
$taskPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) { throw 'Bitte zuerst die Projektumgebung laut README einrichten.' }
& $taskPython tools\collect_licenses.py
if ($LASTEXITCODE -ne 0) { throw 'Lizenztexte konnten nicht gesammelt werden.' }
& $taskPython tools\export_parameter_reference.py
if ($LASTEXITCODE -ne 0) { throw 'Parameterreferenz konnte nicht erstellt werden.' }
$env:PYINSTALLER_CONFIG_DIR = Join-Path $PSScriptRoot 'build\pyinstaller-cache'
& $taskPython -m PyInstaller --noconfirm --onefile --windowed --name Segway-Monitor --version-file assets\version-info.txt --distpath $taskDistRoot --collect-submodules winrt --copy-metadata scootscoot --copy-metadata bleak run_segway_monitor.py
if ($LASTEXITCODE -ne 0) { throw 'EXE-Build fehlgeschlagen.' }
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'README.md') -Destination (Join-Path $taskDistRoot 'README.md')
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'credential-format.example.txt') -Destination (Join-Path $taskDistRoot 'credential-format.example.txt')
foreach ($taskReleaseFile in @('RELEASE_NOTES.md','PARAMETER.md','Segway-Monitor-starten.cmd','LICENSE','NOTICE')) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot $taskReleaseFile) -Destination $taskDistRoot
}
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'licenses')) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'licenses') -Destination $taskDistRoot -Recurse -Force
}
