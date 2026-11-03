# Segway Monitor · Release 1.0.0

[Deutsch](README.md) · [English](README.en.md)

Open source Windows desktop application for reading **Segway GT3 D** scooter
telemetry over Bluetooth Low Energy. The application interface is currently
in German; this guide explains how to get started.

[Download the Windows app · 1.0.0](https://github.com/trycom-3008/segway-monitor/releases/download/v1.0.0/Segway-Monitor-Windows-v1.0.0.zip)
· [Release and checksums](https://github.com/trycom-3008/segway-monitor/releases/tag/v1.0.0)
· [Feedback and bug reports](https://github.com/trycom-3008/segway-monitor/issues)

## Features

- Live battery level, voltage, speed and other operating values.
- Full GT3 D profile with 87 fields, including firmware and vehicle information.
- Battery view with 13 cell-group voltages, voltage spread and temperature channels.
- Individual BMS and component response status.
- Detection of an optional second BMS with 19 additional fields.
- German parameter names, component labels, hover explanations and raw-value details.
- JSON and CSV exports with parameter descriptions and timestamps.
- Local, Windows-DPAPI-protected credential storage and automatic loading.
- Discovery limited to recognized devices with a supported model profile.

## Requirements and first use

You need a 64-bit Windows PC with Bluetooth, a powered-on supported scooter
and **your own vehicle's BLE key**. Each new user must provide their own key;
the download does not contain credentials or automatically obtain them.
Python is not required to run the Windows release.

1. Download and fully extract `Segway-Monitor-Windows-v1.0.0.zip`.
2. Start `Segway-Monitor.exe` and select **Segway suchen** (find a Segway).
3. Select the scooter. Existing credentials are loaded automatically.
4. On first use, choose **Schlüssel importieren** (import key) and select your own
   `.gt3key` backup or a JSON file matching `credential-format.example.txt`.
5. Choose **Werte lesen** (read values), **Live-Abfrage starten** (start live polling)
   or **Alle Profilwerte lesen** (read the full profile).

Importing a key stores the credentials; choose a read command to fetch values.
Saved credentials are bound to the Windows user. Copying the application to
another PC does not transfer access to a vehicle.

## Supported hardware and validation

**GT3 D is the currently validated model.** Authentication, live reads and full
reads were tested on the owner's real GT3 D with its existing modified firmware.
Other models and all stock firmware versions have not been validated.

The full read returned 85 complete fields, one partially valid temperature field
and one unanswered display-firmware field. The main BMS answered all 22 requests.
Two temperature channels were implausible and remain individually blank; the
other channels are retained. Unknown manufacturer codes are described as such.
The source tree passed 66 automated offline tests. The Windows executable is
currently unsigned.

The model registry can be extended with independently validated profiles.
This release does not claim compatibility with every Segway or Ninebot model.

## Parameter reference and development

The complete German reference for all 106 catalogue fields is in
[PARAMETER.md](PARAMETER.md). The [German README](README.md#entwicklung) contains
build and diagnostic instructions. The internal Python package is `gt3desk`.

To report a problem, open an [issue](https://github.com/trycom-3008/segway-monitor/issues)
with the application version, scooter model, firmware versions, Windows version
and the steps that produced the problem. Keep BLE keys and authentication frames
out of public reports.

## License and attribution

Original application code is available under the [MIT License](LICENSE).
Third-party software and derived material retain their original licenses;
see [NOTICE](NOTICE) and the [licenses](licenses) directory.

Segway Monitor is an independent, unofficial application. It is not affiliated
with or endorsed by Segway or Ninebot. The trademarks identify compatible hardware.
