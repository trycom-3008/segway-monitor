"""Small native UI components used by Segway Monitor."""

import tkinter as tk


class RowTooltip:
    def __init__(self, tree, text_for_row, *, delay=450):
        self.tree, self.text_for_row, self.delay = tree, text_for_row, delay
        self.row = None
        self.timer = None
        self.window = None
        self.label = None
        tree.bind("<Motion>", self._motion, add="+")
        for event in ("<Leave>", "<ButtonPress>", "<MouseWheel>", "<Escape>"):
            tree.bind(event, lambda _event: self.hide(), add="+")

    def _motion(self, event):
        row = self.tree.identify_row(event.y) if self.tree.identify_region(event.x, event.y) == "cell" else ""
        if row == self.row:
            return
        self.hide()
        if row:
            self.row = row
            self.timer = self.tree.after(self.delay, lambda: self.show(row, event.x_root + 18, event.y_root + 18))

    def show(self, row, x, y):
        self.timer = None
        if not self.tree.exists(row):
            return
        text = self.text_for_row(row)
        if not text:
            return
        if self.window:
            self.window.destroy()
        self.window = tk.Toplevel(self.tree)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.label = tk.Label(self.window, text=text, justify="left", anchor="w", wraplength=490,
                              bg="#203347", fg="#eff7ff", font=("Segoe UI", 10), padx=15, pady=12,
                              relief="solid", borderwidth=1)
        self.label.pack()
        self.window.update_idletasks()
        width, height = self.window.winfo_reqwidth(), self.window.winfo_reqheight()
        x = max(0, min(x, self.tree.winfo_screenwidth() - width - 12))
        y = max(0, min(y, self.tree.winfo_screenheight() - height - 45))
        self.window.geometry(f"+{x}+{y}")
        self.window.deiconify()

    def hide(self):
        if self.timer:
            self.tree.after_cancel(self.timer)
        self.timer = None
        self.row = None
        if self.window:
            self.window.destroy()
        self.window = self.label = None
