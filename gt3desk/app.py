"""Native Segway Monitor UI. Radio I/O stays on the existing asyncio worker."""

import queue
import time
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from . import APP_NAME, __version__
from .catalog import BY_KEY, CATALOG
from .data import format_value, import_credential, make_report, parse_password, write_csv, write_json
from .key_store import (adopt_saved_key, key_search_directories, latest_key, load_saved_key,
                        normalize_address, remember_credential)
from .models import GT3_D, MODELS, recognize_model
from .parameters import component_name, display_value, parameter_info, parameter_text, parameter_unit
from .widgets import RowTooltip
from .worker import AsyncWorker


BG, PANEL, CARD = "#0b111b", "#121d2b", "#192638"
FG, MUTED, ACCENT, AMBER = "#ecf3fb", "#9db0c6", "#51e0b4", "#efbb69"
MODEL_COLOR = "#68cfff"
MODULE_STATES = {"online": "Antwortet", "no_response": "Keine Antwort", "not_detected": "Nicht erkannt",
                 "not_queried": "Nicht abgefragt"}
ACCESS_HELP = """Segway Monitor verwenden

1. Scooter einschalten und „Segway suchen“ wählen.
2. Dein Fahrzeug auswählen. Ein gespeicherter Zugang wird automatisch geladen.
3. Beim ersten Mal „Schlüssel importieren“ verwenden. Unterstützt werden verschlüsselte .gt3key-Dateien und eigene JSON-Schlüsseldateien.
4. „Werte lesen“ ruft die aktuellen Betriebswerte einmal ab.
5. „Live-Abfrage starten“ aktualisiert diese Werte regelmäßig.
6. „Alle Profilwerte lesen“ ergänzt Kennungen, Firmwarestände und die weiteren Parameter.

Parameter verstehen

Die Parameterliste zeigt deutsche Bezeichnungen und die jeweilige Baugruppe.
Bewege den Mauszeiger über eine Zeile, um ihre Funktion zu sehen. Ein Klick zeigt die ausführliche Erklärung samt technischem Namen, Register und Rohbytes unter der Tabelle.
„Code“, „Bitfeld“ und „Rohwert“ bezeichnen Angaben, deren Einzelkodierung noch nicht vollständig zugeordnet ist.

Akku und Baugruppen

Unter „Akku & Baugruppen“ stehen die Zellgruppenspannungen, Temperaturkanäle und die tatsächlichen Antworten der einzelnen Steuergeräte.
Das Haupt-BMS überwacht den Hauptakku. Ein zweites BMS wird bei einer vollständigen Abfrage auf eigenständige Akku-Kennung und plausible Spannung geprüft. Seine Parameter erscheinen bei eindeutiger Erkennung.
Ein Strich in einem Temperaturkanal bedeutet, dass für diesen Kanal kein plausibler Wert vorliegt.

Zugang und Export

Nach dem Import merkt sich Segway Monitor den Zugang für dieses Fahrzeug unabhängig vom Programmordner. „Eingabe leeren“ leert das aktuelle Feld; gespeicherte Zugänge bleiben erhalten.
Der Import startet noch keine Datenabfrage. Dafür „Werte lesen“ oder „Alle Profilwerte lesen“ wählen.
JSON- und CSV-Exporte enthalten Messwerte, Erklärungen, Baugruppen, Zeitstempel und Rohdaten.

Unterstützte Modelle

Release 1.0 unterstützt den Segway GT3 D. Die Modellprofile können um weitere geprüfte Modelle ergänzt werden.
"""


class App:
    def __init__(self, root):
        self.root = root
        self.model = GT3_D
        root.title(f"{APP_NAME} {__version__} · {self.model.name}")
        root.geometry(f"{min(1440, max(1120, root.winfo_screenwidth()-80))}x{min(900, max(730, root.winfo_screenheight()-100))}")
        root.minsize(1120, 720)
        root.configure(bg=BG)
        self.events = queue.SimpleQueue()
        self.worker = AsyncWorker(lambda event, value: self.events.put((event, value)))
        self.busy = self.live = self.closing = False
        self.address = None
        self.devices, self.visible_devices = [], []
        self.readings, self.modules, self.gatt = {}, {}, []
        self.active_boards = set(self.model.boards)
        self.access = "Noch nicht verbunden"
        self.key_device = self.key_address = self.loaded_key_path = None
        self._setting_key = False
        self.last_job, self.live_timer = "", None
        self.device_var = tk.StringVar()
        self.model_var = tk.StringVar(value=self.model.name)
        self.status = tk.StringVar(value="Bereit · Segway suchen oder gespeichertes Fahrzeug auswählen")
        self.access_var = tk.StringVar(value=self.access)
        self.password = tk.StringVar()
        self.key_status = tk.StringVar(value="Kein Zugang geladen")
        self.search_var = tk.StringVar()
        self.module_var = tk.StringVar(value="Alle Baugruppen")
        self.count_var = tk.StringVar()
        self.last_update = tk.StringVar(value="Noch keine Fahrzeugdaten gelesen")
        self.battery_status = tk.StringVar(value="Hauptakku noch nicht abgefragt")
        self.temperature_status = tk.StringVar(value="Temperaturkanäle noch nicht abgefragt")
        self.cell_summary = tk.StringVar(value="Zellgruppen noch nicht abgefragt")
        self._styles()
        self._build()
        self.password.trace_add("write", self._password_changed)
        self._update_rows()
        self._update_count()
        self._buttons()
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.after(80, self._drain)

    def _styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TFrame", background=BG)
        style.configure("Panel.TFrame", background=PANEL)
        style.configure("TLabel", background=BG, foreground=FG, font=("Segoe UI", 10))
        style.configure("TButton", background=CARD, foreground=FG, padding=(11, 8),
                        borderwidth=0, font=("Segoe UI", 10))
        style.map("TButton", background=[("active", "#263c54"), ("disabled", "#16202e")],
                  foreground=[("disabled", "#65768b")])
        style.configure("Accent.TButton", background=ACCENT, foreground=BG, font=("Segoe UI Semibold", 10))
        style.map("Accent.TButton", background=[("active", "#82efd0"), ("disabled", "#214638")],
                  foreground=[("disabled", "#759387")])
        style.configure("TEntry", fieldbackground=BG, foreground=FG, padding=7, insertcolor=FG)
        style.configure("TCombobox", fieldbackground=BG, background=CARD, foreground=FG, arrowcolor=FG, padding=6)
        style.map("TCombobox", fieldbackground=[("readonly", BG)], foreground=[("readonly", FG)])
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=PANEL, foreground=MUTED, padding=(15, 10), font=("Segoe UI Semibold", 10))
        style.map("TNotebook.Tab", background=[("selected", CARD)], foreground=[("selected", ACCENT)])
        style.configure("Treeview", background=PANEL, fieldbackground=PANEL, foreground=FG,
                        rowheight=31, borderwidth=0, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background=CARD, foreground=MUTED, relief="flat",
                        font=("Segoe UI Semibold", 9), padding=7)
        style.map("Treeview", background=[("selected", "#254b59")])
        style.configure("Horizontal.TProgressbar", troughcolor=CARD, background=ACCENT, borderwidth=0, thickness=4)
        self.root.option_add("*TCombobox*Listbox.background", PANEL)
        self.root.option_add("*TCombobox*Listbox.foreground", FG)

    def _label(self, parent, text="", *, size=10, color=FG, bg=BG, bold=False, **kwargs):
        return tk.Label(parent, text=text, bg=bg, fg=color, anchor="w",
                        font=("Segoe UI Semibold" if bold else "Segoe UI", size), **kwargs)

    def _build(self):
        header = ttk.Frame(self.root, padding=(22, 17))
        header.pack(fill="x")
        self.brand_label = self._label(header, APP_NAME, size=26, bold=True)
        self.brand_label.pack(side="left")
        self.model_label = self._label(header, textvariable=self.model_var, size=21, color=MODEL_COLOR, bold=True)
        self.model_label.pack(side="left", padx=(18, 0))
        self._label(header, f"Release {__version__}", size=9, color=MUTED).pack(side="right")
        body = ttk.Frame(self.root, padding=(22, 0, 22, 10))
        body.pack(fill="both", expand=True)
        side_shell = ttk.Frame(body, style="Panel.TFrame", width=280)
        side_shell.pack(side="left", fill="y", padx=(0, 16))
        side_shell.pack_propagate(False)
        self.side_canvas = tk.Canvas(side_shell, bg=PANEL, highlightthickness=0, width=264)
        side_scroll = ttk.Scrollbar(side_shell, orient="vertical", command=self.side_canvas.yview)
        side_scroll.pack(side="right", fill="y")
        self.side_canvas.pack(side="left", fill="both", expand=True)
        self.side_canvas.configure(yscrollcommand=side_scroll.set)
        side = ttk.Frame(self.side_canvas, style="Panel.TFrame", padding=15)
        side_window = self.side_canvas.create_window((0, 0), window=side, anchor="nw")
        side.bind("<Configure>", lambda _event: self.side_canvas.configure(scrollregion=self.side_canvas.bbox("all")))
        self.side_canvas.bind("<Configure>", lambda event: self.side_canvas.itemconfigure(side_window, width=event.width))
        self._label(side, "FAHRZEUG", bg=PANEL, color=MUTED, size=9, bold=True).pack(fill="x", pady=(0, 9))
        self.scan_button = ttk.Button(side, text="Segway suchen", style="Accent.TButton", command=self.scan)
        self.scan_button.pack(fill="x")
        self.combo = ttk.Combobox(side, textvariable=self.device_var, state="readonly")
        self.combo.pack(fill="x", pady=(11, 7))
        self.combo.bind("<<ComboboxSelected>>", self._select)
        self.device_detail = self._label(side, "Kein Fahrzeug ausgewählt", bg=PANEL, color=MUTED,
                                         size=9, justify="left", wraplength=235)
        self.device_detail.pack(fill="x", pady=(0, 12))
        self.check_button = ttk.Button(side, text="Werte lesen", command=self.read_live)
        self.check_button.pack(fill="x", pady=3)
        ttk.Separator(side).pack(fill="x", pady=16)
        self._label(side, "GESPEICHERTER ZUGANG", bg=PANEL, color=MUTED, size=9, bold=True).pack(fill="x")
        self._label(side, textvariable=self.key_status, bg=PANEL, color=ACCENT, size=9,
                    wraplength=235, justify="left").pack(fill="x", pady=(8, 6))
        self.key_entry = ttk.Entry(side, textvariable=self.password, show="•", font=("Consolas", 10))
        self.key_entry.pack(fill="x")
        self.import_button = ttk.Button(side, text="Schlüssel importieren", command=self.import_key)
        self.import_button.pack(fill="x", pady=(8, 3))
        self.load_button = ttk.Button(side, text="Gespeicherten Zugang laden", command=self.load_key)
        self.load_button.pack(fill="x", pady=3)
        self.clear_button = ttk.Button(side, text="Eingabe leeren", command=self.clear_key)
        self.clear_button.pack(fill="x", pady=3)
        ttk.Separator(side).pack(fill="x", pady=16)
        self._label(side, "VERBINDUNGSSTATUS", bg=PANEL, color=MUTED, size=9, bold=True).pack(fill="x")
        self._label(side, textvariable=self.access_var, bg=PANEL, color=FG, size=10,
                    justify="left", wraplength=235).pack(fill="x", pady=(8, 9))
        self.inspect_button = ttk.Button(side, text="Bluetooth-Dienste anzeigen", command=self.inspect)
        self.inspect_button.pack(fill="x", pady=3)
        main = ttk.Frame(body)
        main.pack(side="left", fill="both", expand=True)
        toolbar = ttk.Frame(main)
        toolbar.pack(fill="x", pady=(0, 10))
        self.live_button = ttk.Button(toolbar, text="Live-Abfrage starten", style="Accent.TButton", command=self.toggle_live)
        self.live_button.pack(side="left", padx=(0, 8))
        self.full_button = ttk.Button(toolbar, text="Alle Profilwerte lesen", command=self.read_all)
        self.full_button.pack(side="left", padx=(0, 8))
        self.stop_button = ttk.Button(toolbar, text="Stoppen", command=self.stop)
        self.stop_button.pack(side="left")
        self.export_button = ttk.Button(toolbar, text="Exportieren …", command=self.export)
        self.export_button.pack(side="right")
        self._label(main, textvariable=self.last_update, color=MUTED, size=9).pack(fill="x", pady=(0, 10))
        self.notebook = ttk.Notebook(main)
        self.notebook.pack(fill="both", expand=True)
        overview = ttk.Frame(self.notebook, padding=(0, 14))
        parameters = ttk.Frame(self.notebook, padding=(0, 10))
        battery = ttk.Frame(self.notebook, padding=(0, 14))
        connection = ttk.Frame(self.notebook, padding=(0, 10))
        help_page = ttk.Frame(self.notebook, padding=(0, 10))
        for page, title in ((overview, "Übersicht"), (parameters, "Parameter"), (battery, "Akku & Baugruppen"),
                            (connection, "Verbindung"), (help_page, "Bedienung")):
            self.notebook.add(page, text=title)
        self.cards = {}
        grid = ttk.Frame(overview)
        grid.pack(fill="x")
        for index, (key, title, unit) in enumerate((
                ("VCU.rBattery", "AKKULADESTAND", "%"), ("VCU.rSpeed", "GESCHWINDIGKEIT", "km/h"),
                ("VCU.rMileage", "KILOMETERSTAND", "km"), ("BMS1.rBMSVolt", "AKKUSPANNUNG", "V"),
                ("BMS1.rBMSCur", "AKKUSTROM", "A"), ("VCU.rBodyTemp", "STEUERUNGSTEMPERATUR", "°C"))):
            card = tk.Frame(grid, bg=CARD, padx=14, pady=13)
            card.grid(row=index//3, column=index%3, sticky="nsew", padx=(0, 7), pady=(0, 7))
            grid.columnconfigure(index%3, weight=1, uniform="cards")
            self._label(card, title, bg=CARD, color=MUTED, size=9, bold=True).pack(fill="x")
            value = self._label(card, "—", bg=CARD, size=25, bold=True)
            value.pack(fill="x", pady=(8, 0))
            self._label(card, unit, bg=CARD, color=MUTED, size=10).pack(fill="x")
            self.cards[key] = value
        summary = tk.Frame(overview, bg=PANEL, padx=17, pady=15)
        summary.pack(fill="both", expand=True, pady=(10, 0))
        self._label(summary, "DATENABRUF", bg=PANEL, color=ACCENT, size=10, bold=True).pack(fill="x")
        self._label(summary, textvariable=self.count_var, bg=PANEL, size=17, bold=True).pack(fill="x", pady=(9, 11))
        self._label(summary, "Live aktualisiert die laufenden Betriebswerte.\n"
                    "„Alle Profilwerte lesen“ ergänzt die weiteren Fahrzeug- und Akkudaten.\n\n"
                    "In der Parameterliste erklärt ein Hover die Funktion.\n"
                    "Ein Klick zeigt die Baugruppe und die technischen Details.",
                    bg=PANEL, color=MUTED, size=10, justify="left", wraplength=650).pack(fill="x")
        filters = ttk.Frame(parameters)
        filters.pack(fill="x", pady=(0, 8))
        self._label(filters, "Suchen", color=MUTED, size=9).pack(side="left", padx=(0, 7))
        ttk.Entry(filters, textvariable=self.search_var).pack(side="left", fill="x", expand=True, padx=(0, 9))
        self.module_combo = ttk.Combobox(filters, textvariable=self.module_var, state="readonly", width=25)
        self.module_combo.pack(side="right")
        self._update_module_filter()
        self.search_var.trace_add("write", lambda *_: self._update_rows())
        self.module_var.trace_add("write", lambda *_: self._update_rows())
        self.table = self._table(parameters,
            ("label", "component", "value", "unit", "status", "technical"),
            ("Parameter", "Baugruppe", "Wert", "Einheit", "Status", "Technischer Name"),
            (260, 170, 190, 70, 180, 210))
        self.table.tag_configure("received", foreground=FG)
        self.table.tag_configure("missing", foreground=MUTED)
        self.table.tag_configure("partial", foreground=AMBER)
        self.table.bind("<<TreeviewSelect>>", self.row_detail)
        self.table.bind("<Double-1>", self.row_detail)
        self.tooltip = RowTooltip(self.table, self._hover_text)
        self.detail_text = self._text(parameters, height=7, expand=False)
        self._replace_text(self.detail_text, "Eine Parameterzeile auswählen, um Funktion und technische Details anzuzeigen.")
        self._build_battery(battery)
        self.gatt_text = self._text(connection)
        self._replace_text(self.gatt_text, "Noch keine Dienste abgefragt.\n„Bluetooth-Dienste anzeigen“ liest die Schnittstellen des gewählten Segways.")
        self.help_text = self._text(help_page)
        self._replace_text(self.help_text, ACCESS_HELP)
        footer = ttk.Frame(self.root, padding=(22, 0, 22, 12))
        footer.pack(fill="x")
        self.progress = ttk.Progressbar(footer, mode="determinate")
        self.progress.pack(fill="x", pady=(0, 7))
        self._label(footer, textvariable=self.status, color=MUTED, size=10, wraplength=1300, justify="left").pack(fill="x")
        def side_wheel(widget):
            if not isinstance(widget, ttk.Combobox):
                widget.bind("<MouseWheel>", lambda event: self.side_canvas.yview_scroll(-int(event.delta/120), "units"), add="+")
            for child in widget.winfo_children():
                side_wheel(child)
        side_wheel(side)

    def _table(self, parent, columns, headings, widths, *, height=None):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)
        kwargs = {"height": height} if height else {}
        tree = ttk.Treeview(frame, columns=columns, show="headings", **kwargs)
        for column, heading, width in zip(columns, headings, widths):
            tree.heading(column, text=heading)
            tree.column(column, width=width, minwidth=55, stretch=column in ("label", "component"))
        tree.grid(row=0, column=0, sticky="nsew")
        y_scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        x_scroll.grid(row=1, column=0, sticky="ew")
        tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        return tree

    def _build_battery(self, parent):
        self._label(parent, "Hauptakku und Zellgruppen", size=18, bold=True).pack(fill="x")
        self._label(parent, textvariable=self.battery_status, color=ACCENT).pack(fill="x", pady=(7, 8))
        self.cell_frame = ttk.Frame(parent)
        self.cell_frame.pack(fill="x")
        self._render_cells()
        self._label(parent, textvariable=self.cell_summary, color=MUTED, size=9).pack(fill="x", pady=(4, 8))
        self._label(parent, textvariable=self.temperature_status, color=FG, size=10, wraplength=850).pack(fill="x", pady=(0, 12))
        self._label(parent, "Baugruppen und Antworten", size=15, bold=True).pack(fill="x", pady=(0, 8))
        self.module_table = self._table(parent, ("component", "state", "answers", "detail"),
            ("Baugruppe", "Status", "Antworten", "Einordnung"), (185, 135, 80, 420), height=6)
        self._update_modules()

    def _render_cells(self):
        for child in self.cell_frame.winfo_children():
            child.destroy()
        self.cell_labels = []
        for index in range(self.model.cell_groups):
            card = tk.Frame(self.cell_frame, bg=CARD, padx=9, pady=7)
            card.grid(row=index//7, column=index%7, sticky="nsew", padx=(0, 5), pady=(0, 5))
            self.cell_frame.columnconfigure(index%7, weight=1, uniform="cells")
            self._label(card, f"Gruppe {index+1}", bg=CARD, color=MUTED, size=9).pack(fill="x")
            label = self._label(card, "— V", bg=CARD, size=13, bold=True)
            label.pack(fill="x", pady=(5, 0))
            self.cell_labels.append(label)

    def _text(self, parent, *, height=None, expand=True):
        holder = ttk.Frame(parent)
        holder.pack(fill="both", expand=expand, pady=(6, 0))
        kwargs = {"height": height} if height else {}
        text = tk.Text(holder, wrap="word", bg=PANEL, fg=FG, insertbackground=FG, relief="flat",
                       font=("Segoe UI", 10), padx=14, pady=10, spacing3=4, **kwargs)
        text.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(holder, command=text.yview)
        scrollbar.pack(side="right", fill="y")
        text.configure(yscrollcommand=scrollbar.set)
        return text

    @staticmethod
    def _replace_text(widget, text):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    def _start(self, name, operation):
        if self.busy or self.closing:
            return
        self.last_job = name
        self._cancel_live_timer()
        self.tooltip.hide()
        self.busy = True
        self.progress.configure(value=0)
        self._buttons()
        self.worker.submit(operation)

    def _buttons(self):
        available = bool(self.address) and not self.busy
        for button in (self.inspect_button, self.check_button, self.full_button, self.live_button,
                       self.load_button, self.import_button):
            button.configure(state="normal" if available else "disabled")
        self.scan_button.configure(state="disabled" if self.busy else "normal")
        self.combo.configure(state="disabled" if self.busy else "readonly")
        self.clear_button.configure(state="disabled" if self.busy else "normal")
        self.key_entry.configure(state="normal" if available else "disabled")
        self.stop_button.configure(state="normal" if self.busy or self.live else "disabled")
        self.live_button.configure(text="Live-Abfrage läuft" if self.live else "Live-Abfrage starten")

    def scan(self):
        self.live = False
        self._start("scan", lambda service: service.scan())

    def _populate_devices(self):
        self.visible_devices = [row for row in self.devices if recognize_model(row.get("name"), row.get("services", ()))]
        self.combo["values"] = [f"{row.get('model_name', self.model.name)} · {row['name']}" for row in self.visible_devices]
        selected = next((index for index, row in enumerate(self.visible_devices) if row["address"] == self.address), None)
        if selected is None and len(self.visible_devices) == 1:
            selected = 0
        if selected is not None:
            self.combo.current(selected)
            self._select()
        else:
            self.device_var.set("")
            self._set_device(None)
        self._buttons()

    def _select(self, _event=None):
        index = self.combo.current()
        if 0 <= index < len(self.visible_devices):
            self._set_device(self.visible_devices[index])

    def _set_device(self, row):
        model = recognize_model(row.get("name"), row.get("services", ())) if row else None
        if row and model is None:
            row = None
        address = row["address"] if row else None
        if address != self.address:
            self.live = False
            self._cancel_live_timer()
            self.clear_key()
            self.readings, self.modules, self.gatt = {}, {}, []
            self.access = "Noch nicht verbunden"
            self.access_var.set(self.access)
            self.last_update.set("Noch keine Fahrzeugdaten gelesen")
            if model:
                self.model = model
                if len(self.cell_labels) != model.cell_groups:
                    self._render_cells()
            self.active_boards = set(self.model.boards)
            for card in self.cards.values():
                card.configure(text="—")
            self._replace_text(self.detail_text, "Eine Parameterzeile auswählen, um Details anzuzeigen.")
            self._replace_text(self.gatt_text, "Für dieses Fahrzeug wurden noch keine Bluetooth-Dienste gelesen.")
            self.address = address
            self.model_var.set(self.model.name)
            self.root.title(f"{APP_NAME} {__version__} · {self.model.name}")
            self._update_module_filter()
            self._update_rows()
            self._update_count()
            self._update_modules()
            self._update_battery()
            if row:
                self.load_key(automatic=True)
        self.device_detail.configure(text=(f"{row['name']}\n{address}\nSignal {row.get('rssi', '?')} dBm" if row else
                                            "Kein unterstützter Segway ausgewählt"))
        self._buttons()

    def inspect(self):
        if self.address:
            self._start("inspect", lambda service: service.inspect(self.address))

    def _device(self):
        return next((row for row in self.devices if row["address"] == self.address), None)

    def _read(self, full=False):
        device = self._device()
        if not device or not recognize_model(device.get("name"), device.get("services", ())):
            return
        try:
            password = parse_password(self.password.get())
        except ValueError as error:
            self.live = False
            messagebox.showerror("Zugang prüfen", str(error), parent=self.root)
            return
        if ((self.key_device and self.key_device != device["name"]) or
                (self.key_address and normalize_address(self.key_address) != normalize_address(self.address))):
            self.live = False
            messagebox.showerror("Anderes Fahrzeug", "Bitte einen Zugang für das ausgewählte Fahrzeug laden.", parent=self.root)
            return
        address = self.address
        self._start("read", lambda service: service.read(address, password, full=full))

    def read_live(self):
        self.live = False
        self._read()

    def read_all(self):
        self.live = False
        self._read(full=True)

    def toggle_live(self):
        self.live = True
        self._read()

    def stop(self):
        self.live = False
        self._cancel_live_timer()
        self.worker.cancel()
        self._buttons()

    def _cancel_live_timer(self):
        if self.live_timer is not None:
            self.root.after_cancel(self.live_timer)
            self.live_timer = None

    def _password_changed(self, *_args):
        if not self._setting_key:
            self.key_device = self.key_address = self.loaded_key_path = None
            self.key_status.set("Zugang eingegeben" if self.password.get() else "Kein Zugang geladen")

    def clear_key(self):
        self.password.set("")
        self.key_device = self.key_address = self.loaded_key_path = None
        self.key_status.set("Kein Zugang geladen")

    def _apply_key(self, saved):
        self._setting_key = True
        try:
            self.password.set(saved.password.hex())
            self.key_device, self.key_address, self.loaded_key_path = saved.device_name, saved.address, saved.path
        finally:
            self._setting_key = False
        self.key_status.set("Zugang gespeichert · bestätigt" if saved.state == "confirmed" else "Zugang importiert und gespeichert")

    def load_key(self, *, automatic=False):
        device = self._device()
        if not device:
            return
        try:
            saved = latest_key(self.address, device["name"], confirmed_only=automatic)
            saved = adopt_saved_key(saved)
        except (OSError, ValueError) as error:
            self.key_status.set("Einmaliger Schlüsselimport erforderlich")
            if not automatic:
                messagebox.showerror("Zugang nicht geladen",
                    f"{error}\n\nEine .gt3key- oder JSON-Datei kann direkt importiert werden.", parent=self.root)
            return
        self._apply_key(saved)
        if not automatic:
            self.status.set("Gespeicherter Zugang geladen · Datenabfrage kann gestartet werden")

    def import_key(self):
        device = self._device()
        if not device:
            return
        path = filedialog.askopenfilename(title="Zugang für deinen Segway importieren", parent=self.root,
            filetypes=[("Verschlüsselte Sicherung", "*.gt3key"), ("JSON-Schlüsseldatei", "*.json"), ("Alle Dateien", "*.*")])
        if not path:
            return
        try:
            if Path(path).suffix.lower() == ".gt3key":
                imported = load_saved_key(path, expected_address=self.address, expected_name=device["name"])
                saved = adopt_saved_key(imported)
            else:
                imported = import_credential(Path(path))
                if imported.device_name and imported.device_name != device["name"]:
                    raise ValueError("Die Datei gehört zu einer anderen Fahrzeugkennung.")
                saved = remember_credential(imported.password, device["name"], self.address)
        except (OSError, ValueError) as error:
            messagebox.showerror("Import fehlgeschlagen", str(error), parent=self.root)
            return
        self._apply_key(saved)
        self.status.set("Zugang dauerhaft gespeichert · Jetzt „Alle Profilwerte lesen“ oder Live-Abfrage starten")

    def _confirm_current_key(self):
        device = self._device()
        if not device or not self.password.get():
            return
        try:
            saved = remember_credential(parse_password(self.password.get()), device["name"], self.address, confirmed=True)
            self._apply_key(saved)
        except (OSError, ValueError):
            self.key_status.set("Zugang funktioniert · Speichern fehlgeschlagen")

    def _update_module_filter(self):
        choices = ["Alle Baugruppen"] + [component_name(board) for board in self.model.boards if board in self.active_boards]
        if "BMS2" in self.active_boards:
            choices.append(component_name("BMS2"))
        self.module_combo["values"] = choices
        if self.module_var.get() not in choices:
            self.module_var.set("Alle Baugruppen")

    def _catalog(self):
        return [spec for spec in self.model.registers if spec.board in self.active_boards]

    def _update_rows(self):
        if not hasattr(self, "table"):
            return
        self.tooltip.hide() if hasattr(self, "tooltip") else None
        query, component = self.search_var.get().casefold().strip(), self.module_var.get()
        wanted = []
        for spec in self._catalog():
            entry = parameter_info(spec)
            if component != "Alle Baugruppen" and component_name(spec.board) != component:
                continue
            if query and query not in f"{entry.label} {entry.description} {spec.key} {component_name(spec.board)}".casefold():
                continue
            wanted.append(spec)
        ids = {spec.key for spec in wanted}
        for old in set(self.table.get_children()) - ids:
            self.table.delete(old)
        for position, spec in enumerate(wanted):
            row = self.readings.get(spec.key)
            values = (parameter_info(spec).label, component_name(spec.board), display_value(spec, row.value) if row else "—",
                      parameter_unit(spec), row.status if row else "Noch nicht abgefragt", spec.key)
            partial = bool(row and row.status.startswith("Teilweise"))
            tag = "partial" if partial else ("received" if row and row.value is not None else "missing")
            if self.table.exists(spec.key):
                self.table.item(spec.key, values=values, tags=(tag,))
                self.table.move(spec.key, "", position)
            else:
                self.table.insert("", position, iid=spec.key, values=values, tags=(tag,))

    def _hover_text(self, key):
        spec = self.model.by_key.get(key)
        if spec is None:
            return ""
        entry, row = parameter_info(spec), self.readings.get(key)
        text = f"{entry.label}\n{component_name(spec.board)}\n\n{entry.description}"
        if row:
            text += f"\n\nAktuell: {format_value(row.value)} {parameter_unit(spec)}\n{row.status}"
        return text + f"\n\nTechnik: {spec.key}"

    def row_detail(self, _event=None):
        selected = self.table.selection()
        if selected and selected[0] in self.model.by_key:
            spec = self.model.by_key[selected[0]]
            self._replace_text(self.detail_text, parameter_text(spec, self.readings.get(spec.key)))

    def _update_count(self):
        selected = [self.readings[spec.key] for spec in self._catalog() if spec.key in self.readings]
        count = sum(row.value is not None for row in selected)
        partial = sum(row.status.startswith("Teilweise") for row in selected)
        self.count_var.set(f"{count} / {len(self._catalog())} Parameter mit Daten" + (f" · {partial} teilweise" if partial else ""))

    def _update_modules(self):
        if not hasattr(self, "module_table"):
            return
        for board in (*self.model.boards, "BMS2"):
            state = self.modules.get(board, {})
            values = (component_name(board), MODULE_STATES.get(state.get("state"), "Noch nicht abgefragt"),
                      state.get("answers", "—"), state.get("detail", ""))
            if self.module_table.exists(board):
                self.module_table.item(board, values=values)
            else:
                self.module_table.insert("", "end", iid=board, values=values)

    def _update_battery(self):
        bms = self.modules.get("BMS1", {})
        if bms:
            self.battery_status.set(f"Haupt-BMS: {MODULE_STATES.get(bms.get('state'), 'Noch nicht abgefragt')} · {bms.get('detail', '')}")
        else:
            self.battery_status.set("Hauptakku noch nicht abgefragt")
        cells = self.readings.get("BMS1.rBmsCellVolFrequence")
        values = cells.value if cells and isinstance(cells.value, list) else []
        for index, label in enumerate(self.cell_labels):
            label.configure(text=(format_value(values[index]) + " V") if index < len(values) else "— V")
        valid = [value for value in values if value is not None]
        if valid:
            delta = round((max(valid) - min(valid)) * 1000, 3)
            self.cell_summary.set(f"{len(valid)} Zellgruppen · min. {format_value(min(valid))} V · max. {format_value(max(valid))} V · Differenz {format_value(delta)} mV")
        else:
            self.cell_summary.set("Zellgruppen noch nicht abgefragt")
        temps = self.readings.get("BMS1.rBmsTempFrequence")
        self.temperature_status.set("Akku-Temperaturkanäle: " + format_value(temps.value) + " °C" if temps else
                                    "Temperaturkanäle noch nicht abgefragt")

    def export(self):
        device = self._device()
        if not device:
            return
        path = filedialog.asksaveasfilename(title="Fahrzeugdaten exportieren", parent=self.root, defaultextension=".json",
            initialfile=f"Segway-Monitor-{self.model.name.replace(' ', '-')}-{datetime.now():%Y%m%d-%H%M%S}.json",
            filetypes=[("JSON · Daten und Erklärungen", "*.json"), ("CSV · Tabelle", "*.csv")])
        if not path:
            return
        report = make_report(device, self.gatt, self.readings, self.access)
        report["modules"] = self.modules
        try:
            (write_csv if Path(path).suffix.lower() == ".csv" else write_json)(Path(path), report)
        except OSError:
            messagebox.showerror("Export fehlgeschlagen", "Datei konnte nicht gespeichert werden.", parent=self.root)
            return
        self.status.set(f"Bericht gespeichert: {Path(path).name}")

    def _drain(self):
        if self.closing:
            return
        changed = False
        while True:
            try:
                event, value = self.events.get_nowait()
            except queue.Empty:
                break
            if event == "status":
                self.status.set(value)
            elif event == "devices":
                self.devices = value
                self._populate_devices()
            elif event == "model":
                self.model = MODELS[value]
                self.model_var.set(self.model.name)
            elif event == "gatt":
                self.gatt = value
                text = []
                for service in value:
                    text.append(f"Dienst: {service['uuid']} · {service.get('description', '')}")
                    text.extend(f"  {char['uuid']} · {', '.join(char['properties'])}" for char in service["characteristics"])
                    text.append("")
                self._replace_text(self.gatt_text, "\n".join(text))
            elif event == "reading":
                self.readings[value.key] = value
                if value.key in self.cards:
                    self.cards[value.key].configure(text=format_value(value.value))
                self.last_update.set("Letzte Antwort: " + value.time.replace("T", " ").replace("+00:00", " UTC"))
                changed = True
            elif event == "modules":
                self.modules.update(value)
                if value.get("BMS2", {}).get("state") == "online":
                    self.active_boards.add("BMS2")
                self._update_module_filter()
                self._update_modules()
                changed = True
            elif event == "access":
                self.access = value
                self.access_var.set(value)
                self._confirm_current_key()
            elif event == "progress":
                self.progress.configure(value=value[0], maximum=value[1])
            elif event == "error":
                self.access, message = value
                self.access_var.set(self.access)
                self.status.set(f"{self.access}: {message}")
                self.live = False
            elif event == "done":
                self.busy = False
                self._buttons()
                if self.live and self.last_job == "read":
                    self.live_timer = self.root.after(5000, self._next_live)
        if changed:
            self._update_rows()
            self._update_count()
            self._update_battery()
            self.row_detail()
        self.root.after(80, self._drain)

    def _next_live(self):
        self.live_timer = None
        if self.live and not self.busy and not self.closing:
            self._read()

    def close(self):
        if self.closing:
            return
        self.closing = True
        self.live = False
        self.tooltip.hide()
        self._cancel_live_timer()
        self.clear_key()
        self.worker.shutdown()
        self.close_started = time.monotonic()
        self._wait_close()

    def _wait_close(self):
        if not self.worker.thread.is_alive() or time.monotonic() - self.close_started > 12:
            self.root.destroy()
        else:
            self.root.after(100, self._wait_close)


def launch(self_check=False, *, self_check_key=None, gui_diagnose=None):
    root = tk.Tk()
    if self_check:
        root.withdraw()
    app = App(root)
    checked = None
    if self_check:
        root.update_idletasks()
        assert len(app.table.get_children()) == 87
        assert len(app.cards) == 6 and len(app.cell_labels) == 13
        assert not hasattr(app, "pair_button") and not hasattr(app, "show_all_check")
        assert str(app.brand_label.cget("fg")) != str(app.model_label.cget("fg"))
        if self_check_key:
            address, name = self_check_key
            row = {"address": address, "name": name, "candidate": True}
            app.devices = [row]
            app._set_device(row)
            checked = {"key_loaded": bool(app.password.get()),
                       "vehicle_binding_matches": app.key_device == name and app.key_address is not None
                           and normalize_address(app.key_address) == normalize_address(address),
                       "key_source": str(app.loaded_key_path) if app.loaded_key_path else None,
                       "search_directories": [str(path) for path in key_search_directories()]}
        if not gui_diagnose:
            root.after(150, app.close)
    if gui_diagnose:
        checked = {"validation": {"key_loaded": False, "scan_found_vehicle": False}, "readings": []}
        started = time.monotonic()
        stage = "scan"

        def poll():
            nonlocal stage, checked
            if time.monotonic() - started > 230:
                checked["validation"]["error"] = "GUI-Diagnose hat die Zeitgrenze erreicht"
                app.close()
                return
            if app.busy:
                root.after(150, poll)
                return
            if stage == "scan":
                selected = next((index for index, row in enumerate(app.visible_devices)
                                 if normalize_address(row["address"]) == normalize_address(gui_diagnose)), None)
                if selected is None:
                    checked["validation"]["error"] = "Fahrzeug nicht gefunden"
                    app.close()
                    return
                app.combo.current(selected)
                app._select()
                checked["validation"].update({"scan_found_vehicle": True, "key_loaded": bool(app.password.get())})
                stage = "read"
                app.read_all()
                root.after(150, poll)
                return
            validation = checked["validation"]
            checked = make_report(app._device() or {}, app.gatt, app.readings, app.access)
            checked.update({"modules": app.modules, "validation": validation})
            validation["visible_parameters"] = len(app.table.get_children())
            validation["described_parameters"] = sum(bool(parameter_info(spec).description) for spec in app._catalog())
            app.close()

        app.scan()
        root.after(150, poll)
    root.mainloop()
    return checked
