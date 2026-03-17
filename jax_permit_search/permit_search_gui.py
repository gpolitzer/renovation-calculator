#!/usr/bin/env python3
"""
JAX EPICS Permit Search — GUI
Double-click this file to open the search window.

BEFORE RUNNING:
  1. Close all Opera windows
  2. Double-click  launch_opera_debug.bat
  3. Make sure VPN is ON in Opera
  4. Then double-click this file (or run:  python permit_search_gui.py)
"""

import csv
import json
import re
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk(); root.withdraw()
    messagebox.showerror("Missing library",
        "Playwright is not installed.\n\nOpen a terminal and run:\n"
        "  pip install playwright\n  playwright install chromium")
    sys.exit(1)

# ── constants ────────────────────────────────────────────────────────────────
SITE_URL = "https://jaxepics.coj.net"
API_URL  = "https://jaxepicsapi.coj.net/api/AdvancedSearches/Advanced"
CDP_URL  = "http://localhost:9222"
APP_TITLE = "JAX EPICS — Permit Search"

# ── address normalizer ────────────────────────────────────────────────────────
_ABBREV = {
    r'\bROAD\b':      'RD',    r'\bSTREET\b':   'ST',
    r'\bAVENUE\b':    'AVE',   r'\bDRIVE\b':    'DR',
    r'\bLANE\b':      'LN',    r'\bCOURT\b':    'CT',
    r'\bCIRCLE\b':    'CIR',   r'\bBOULEVARD\b':'BLVD',
    r'\bPLACE\b':     'PL',    r'\bTERRACE\b':  'TER',
    r'\bTRAIL\b':     'TRL',   r'\bPARKWAY\b':  'PKWY',
    r'\bHIGHWAY\b':   'HWY',   r'\bEXPRESSWAY\b':'EXPY',
    r'\bNORTH\b':     'N',     r'\bSOUTH\b':    'S',
    r'\bEAST\b':      'E',     r'\bWEST\b':     'W',
}

def normalize_address(raw: str) -> str:
    """Upper-case and replace long-form street words with standard abbreviations."""
    text = raw.strip().upper()
    for pattern, abbrev in _ABBREV.items():
        text = re.sub(pattern, abbrev, text)
    # collapse multiple spaces
    return re.sub(r'\s+', ' ', text)


# ── API logic (same as search_permits.py) ────────────────────────────────────

def call_api(address):
    """Connect to Opera and call the EPICS API. Returns list of permit dicts."""
    address = normalize_address(address)   # "8319 Springtree Road" → "8319 SPRINGTREE RD"

    url = (f"{API_URL}?page=1&pageSize=500"
           f"&filter=&sortActive=FullPermitNumber&sortDirection=asc&forSpreadSheet=false")

    body = {
        "SavedSearchColumns": [
            {"ColumnId": 1}, {"ColumnId": 2}, {"ColumnId": 3}, {"ColumnId": 4},
            {"ColumnId": 5}, {"ColumnId": 6}, {"ColumnId": 7}, {"ColumnId": 8}
        ],
        "SavedSearchFilters": [{
            "SavedSearchFilterId": 0,
            "SavedSearchId": 0,
            "ColumnId": 8,
            "OperatorId": 2,   # 2 = Contains (more forgiving than 1 = Equals)
            "Order": -1,
            "Obj": {"SearchString": address},
            "groupedSectionControls": {},
            "Completed": True,
            "DateEntered": datetime.now().strftime("%a %b %d %Y"),
            "DateUpdated": datetime.now().strftime("%a %b %d %Y"),
            "EvalValueString": json.dumps({"SearchString": address}),
            "IsActive": True,
            "SavedSearch": None,
            "DisplayInWidget": True,
            "PinnedInWidget": False,
            "Sort": 0
        }],
        "UserSavedSearches": [],
        "UserSavedSearchWidgets": [],
        "TableId": 82
    }

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)
        contexts = browser.contexts
        context  = contexts[0] if contexts else browser.new_context()
        page     = context.new_page()

        page.goto(SITE_URL, wait_until="networkidle", timeout=60_000)
        time.sleep(2)

        result = page.evaluate(
            """async ([url, body]) => {
                try {
                    const r = await fetch(url, {
                        method: 'POST',
                        headers: {
                            'content-type': 'application/json',
                            'accept': 'application/json, text/plain, */*',
                            'referer': 'https://jaxepics.coj.net/',
                            'ignoreloading': ''
                        },
                        body: JSON.stringify(body)
                    });
                    if (!r.ok) return { error: `HTTP ${r.status}` };
                    return { success: true, data: await r.json() };
                } catch (e) { return { error: e.toString() }; }
            }""",
            [url, body]
        )

        page.close()
        browser.close()

    if not result or "error" in result:
        raise RuntimeError(result.get("error", "Unknown API error") if result else "No response")

    data   = result.get("data", {})
    values = data.get("values", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])

    permits = []
    for item in values:
        permit_num  = (item.get("FullPermitNumber") or item.get("fullPermitNumber") or
                       item.get("PermitNumber") or "")
        permit_type = (item.get("PermitTypeDescription") or item.get("permitTypeDescription") or
                       item.get("PermitType") or "")

        year = ""
        date_issued = item.get("DateIssued") or item.get("dateIssued") or ""
        if date_issued:
            m = re.search(r'(\d{4})', str(date_issued))
            if m:
                year = m.group(1)
        if not year and permit_num:
            m4 = re.search(r'-(\d{4})-', str(permit_num))
            if m4:
                year = m4.group(1)
            else:
                m2 = re.search(r'-(\d{2})-', str(permit_num))
                if m2:
                    year = str(2000 + int(m2.group(1)))

        if permit_num:
            permits.append({"permit_number": permit_num,
                             "permit_type":   permit_type,
                             "year":          year})
    return permits


# ── GUI ──────────────────────────────────────────────────────────────────────

class PermitSearchApp(tk.Tk):

    def __init__(self, initial_address=""):
        super().__init__()
        self.title(APP_TITLE)
        self.resizable(True, True)
        self.minsize(700, 450)
        self._permits = []
        self._build_ui()
        self._center()

        # If launched with an address (e.g. from the calculator), auto-search
        if initial_address:
            self._addr_var.set(initial_address)
            self.after(500, self._start_search)   # small delay so window renders first

    # ── layout ───────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── top bar ──
        top = tk.Frame(self, padx=12, pady=10)
        top.pack(fill="x")

        tk.Label(top, text="Address:", font=("Segoe UI", 11)).pack(side="left")

        self._addr_var = tk.StringVar()
        self._entry = ttk.Entry(top, textvariable=self._addr_var, width=38,
                                font=("Segoe UI", 11))
        self._entry.pack(side="left", padx=(6, 8))
        self._entry.bind("<Return>", lambda e: self._start_search())

        self._search_btn = ttk.Button(top, text="🔍  Search",
                                      command=self._start_search, width=12)
        self._search_btn.pack(side="left")

        self._save_btn = ttk.Button(top, text="💾  Save CSV",
                                    command=self._save_csv, width=12,
                                    state="disabled")
        self._save_btn.pack(side="left", padx=(8, 0))

        # ── status bar ──
        self._status_var = tk.StringVar(value="Enter an address and click Search.")
        status_bar = tk.Label(self, textvariable=self._status_var,
                              anchor="w", padx=12, pady=4,
                              font=("Segoe UI", 9), fg="#555")
        status_bar.pack(fill="x", side="bottom")

        # ── results table ──
        cols = ("permit_number", "permit_type", "year")
        frame = tk.Frame(self)
        frame.pack(fill="both", expand=True, padx=12, pady=(0, 6))

        self._tree = ttk.Treeview(frame, columns=cols, show="headings",
                                  selectmode="browse")
        self._tree.heading("permit_number", text="Permit Number")
        self._tree.heading("permit_type",   text="Permit Type")
        self._tree.heading("year",          text="Year")
        self._tree.column("permit_number", width=200, anchor="w")
        self._tree.column("permit_type",   width=280, anchor="w")
        self._tree.column("year",          width=80,  anchor="center")

        vsb = ttk.Scrollbar(frame, orient="vertical",   command=self._tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        # ── zebra stripes ──
        self._tree.tag_configure("odd",  background="#f5f7fa")
        self._tree.tag_configure("even", background="#ffffff")

    def _center(self):
        self.update_idletasks()
        w, h = 760, 500
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    # ── search ───────────────────────────────────────────────────────────────

    def _start_search(self):
        address = self._addr_var.get().strip()
        if not address:
            messagebox.showwarning("No address", "Please enter a street address.")
            return

        # clear old results
        for row in self._tree.get_children():
            self._tree.delete(row)
        self._permits = []
        self._save_btn.config(state="disabled")
        self._search_btn.config(state="disabled")
        normalized = normalize_address(address)
        self._status(f"Searching for: {normalized}  …", color="#e67e00")

        # run in background thread so UI stays responsive
        threading.Thread(target=self._run_search, args=(address,),
                         daemon=True).start()

    def _run_search(self, address):
        try:
            permits = call_api(address)
            self.after(0, self._show_results, permits, address)
        except Exception as e:
            self.after(0, self._show_error, str(e))

    def _show_results(self, permits, address):
        self._permits = permits
        self._search_btn.config(state="normal")

        if not permits:
            self._status(f"No permits found for: {address}", color="#c0392b")
            return

        for i, p in enumerate(permits):
            tag = "odd" if i % 2 else "even"
            self._tree.insert("", "end", values=(
                p["permit_number"], p["permit_type"], p["year"]
            ), tags=(tag,))

        self._save_btn.config(state="normal")
        self._status(f"✅  {len(permits)} permit(s) found for: {address}",
                     color="#27ae60")

    def _show_error(self, msg):
        self._search_btn.config(state="normal")
        if "connect" in msg.lower() or "9222" in msg:
            messagebox.showerror("Cannot connect to Opera",
                "Could not connect to Opera.\n\n"
                "Please:\n"
                "  1. Close ALL Opera windows\n"
                "  2. Double-click  launch_opera_debug.bat\n"
                "  3. Make sure VPN is ON in Opera\n"
                "  4. Click Search again")
        else:
            messagebox.showerror("Error", f"Search failed:\n\n{msg}")
        self._status(f"Error: {msg}", color="#c0392b")

    # ── CSV export ────────────────────────────────────────────────────────────

    def _save_csv(self):
        if not self._permits:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save permits as CSV"
        )
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["permit_number", "permit_type", "year"])
            writer.writeheader()
            writer.writerows(self._permits)
        self._status(f"✅  Saved {len(self._permits)} rows → {path}", color="#27ae60")

    # ── helpers ───────────────────────────────────────────────────────────────

    def _status(self, msg, color="#555"):
        self._status_var.set(msg)
        # find the label widget and update its colour
        for w in self.winfo_children():
            if isinstance(w, tk.Label) and w.cget("textvariable") == str(self._status_var):
                w.config(fg=color)
                break


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--address", default="", help="Pre-fill address and auto-search")
    args = parser.parse_args()
    app = PermitSearchApp(initial_address=args.address)
    app.mainloop()
