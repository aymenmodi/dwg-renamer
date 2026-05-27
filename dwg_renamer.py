import os
import tkinter as tk
from tkinter import filedialog, ttk, messagebox


def find_cad_pdf_pairs(root_folder):
    """Walk all subfolders and find every CAD+PDF sibling pair."""
    pairs = []
    for dirpath, dirnames, _ in os.walk(root_folder):
        dirnames_lower = {d.lower(): d for d in dirnames}
        if 'cad' in dirnames_lower and 'pdf' in dirnames_lower:
            cad_path = os.path.join(dirpath, dirnames_lower['cad'])
            pdf_path = os.path.join(dirpath, dirnames_lower['pdf'])
            pairs.append((cad_path, pdf_path))
    return pairs


def build_rename_plan(cad_folder, pdf_folder):
    """
    For each .dwg in cad_folder, find the .pdf whose stem ends with the dwg stem.
    Returns list of (old_path, new_path, status) tuples.
    """
    dwg_files = [f for f in os.listdir(cad_folder) if f.lower().endswith('.dwg')]
    pdf_stems = [os.path.splitext(f)[0] for f in os.listdir(pdf_folder) if f.lower().endswith('.pdf')]

    plan = []
    for dwg_file in sorted(dwg_files):
        dwg_stem = os.path.splitext(dwg_file)[0]          # e.g. AR-0101
        old_path = os.path.join(cad_folder, dwg_file)

        # Find PDF stem that ends with the DWG stem (case-insensitive)
        matches = [p for p in pdf_stems if p.lower().endswith(dwg_stem.lower())]

        if len(matches) == 1:
            new_name = matches[0] + '.dwg'
            new_path = os.path.join(cad_folder, new_name)
            if new_name == dwg_file:
                plan.append((old_path, new_path, 'already_correct'))
            else:
                plan.append((old_path, new_path, 'rename'))
        elif len(matches) == 0:
            plan.append((old_path, None, 'no_match'))
        else:
            plan.append((old_path, None, f'multiple_matches: {", ".join(matches)}'))

    return plan


def execute_plan(plan):
    done, skipped, errors = 0, 0, 0
    for old_path, new_path, status in plan:
        if status == 'rename':
            try:
                os.rename(old_path, new_path)
                done += 1
            except Exception as e:
                errors += 1
        elif status == 'already_correct':
            skipped += 1
        else:
            errors += 1
    return done, skipped, errors


# ── GUI ──────────────────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DWG Renamer  –  by Aymen")
        self.resizable(True, True)
        self.minsize(780, 520)
        self.configure(bg="#1e1e2e")
        self._build_ui()

    def _build_ui(self):
        PAD = dict(padx=12, pady=6)
        BG = "#1e1e2e"
        CARD = "#2a2a3e"
        ACCENT = "#7c6af7"
        FG = "#cdd6f4"
        FG2 = "#a6adc8"
        GREEN = "#a6e3a1"
        RED = "#f38ba8"
        YELLOW = "#f9e2af"

        self.configure(bg=BG)

        # ── header ──
        hdr = tk.Frame(self, bg=ACCENT, height=4)
        hdr.pack(fill="x")

        title_frame = tk.Frame(self, bg=BG)
        title_frame.pack(fill="x", padx=16, pady=(12, 4))
        tk.Label(title_frame, text="DWG Renamer", font=("Segoe UI", 16, "bold"),
                 bg=BG, fg=FG).pack(side="left")
        tk.Label(title_frame, text="  Match CAD files to PDF names automatically",
                 font=("Segoe UI", 10), bg=BG, fg=FG2).pack(side="left", pady=4)

        # ── folder picker ──
        picker = tk.Frame(self, bg=CARD, padx=12, pady=10)
        picker.pack(fill="x", padx=16, pady=(4, 0))

        tk.Label(picker, text="Parent Folder:", font=("Segoe UI", 10, "bold"),
                 bg=CARD, fg=FG).grid(row=0, column=0, sticky="w")

        self.folder_var = tk.StringVar()
        entry = tk.Entry(picker, textvariable=self.folder_var, width=70,
                         font=("Segoe UI", 9), bg="#313244", fg=FG,
                         insertbackground=FG, relief="flat", bd=6)
        entry.grid(row=0, column=1, padx=(8, 8), sticky="ew")
        picker.columnconfigure(1, weight=1)

        browse_btn = tk.Button(picker, text="Browse…", font=("Segoe UI", 9, "bold"),
                               bg=ACCENT, fg="white", relief="flat", bd=0,
                               padx=10, pady=4, cursor="hand2",
                               command=self._browse)
        browse_btn.grid(row=0, column=2)

        # ── action buttons ──
        btn_frame = tk.Frame(self, bg=BG)
        btn_frame.pack(fill="x", padx=16, pady=8)

        self.preview_btn = tk.Button(btn_frame, text="🔍  Preview Changes",
                                     font=("Segoe UI", 10, "bold"),
                                     bg="#45475a", fg=FG, relief="flat", bd=0,
                                     padx=14, pady=6, cursor="hand2",
                                     command=self._preview)
        self.preview_btn.pack(side="left", padx=(0, 8))

        self.rename_btn = tk.Button(btn_frame, text="✅  Rename Files",
                                    font=("Segoe UI", 10, "bold"),
                                    bg=ACCENT, fg="white", disabledforeground="white",
                                    relief="flat", bd=0,
                                    padx=14, pady=6, cursor="hand2",
                                    state="disabled", command=self._rename)
        self.rename_btn.pack(side="left")

        self.clear_btn = tk.Button(btn_frame, text="🗑  Clear",
                                   font=("Segoe UI", 10),
                                   bg="#45475a", fg=FG2, relief="flat", bd=0,
                                   padx=10, pady=6, cursor="hand2",
                                   command=self._clear)
        self.clear_btn.pack(side="right")

        # ── stats bar ──
        self.stats_var = tk.StringVar(value="Ready. Select a parent folder and click Preview.")
        stats_bar = tk.Frame(self, bg=CARD, padx=12, pady=6)
        stats_bar.pack(fill="x", padx=16, pady=(0, 4))
        tk.Label(stats_bar, textvariable=self.stats_var, font=("Segoe UI", 9),
                 bg=CARD, fg=FG2, anchor="w").pack(fill="x")

        # ── log table ──
        table_frame = tk.Frame(self, bg=BG)
        table_frame.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        cols = ("status", "old_name", "new_name", "folder")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings",
                                 selectmode="browse")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=CARD, foreground=FG,
                        fieldbackground=CARD, rowheight=24,
                        font=("Consolas", 8))
        style.configure("Treeview.Heading", background="#313244", foreground=FG,
                        font=("Segoe UI", 9, "bold"), relief="flat")
        style.map("Treeview", background=[("selected", ACCENT)])

        self.tree.tag_configure("rename", foreground=GREEN)
        self.tree.tag_configure("correct", foreground=FG2)
        self.tree.tag_configure("error", foreground=RED)
        self.tree.tag_configure("warn", foreground=YELLOW)

        headers = {"status": ("Status", 90), "old_name": ("Current DWG Name", 200),
                   "new_name": ("New Name (from PDF)", 260), "folder": ("Location", 180)}
        for col, (label, width) in headers.items():
            self.tree.heading(col, text=label)
            self.tree.column(col, width=width, minwidth=60)

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        self._plan = []

    def _browse(self):
        folder = filedialog.askdirectory(title="Select Parent Folder")
        if folder:
            self.folder_var.set(folder)
            self._clear_log()
            self.rename_btn.config(state="disabled")

    def _clear_log(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        self._plan = []

    def _clear(self):
        self.folder_var.set("")
        self._clear_log()
        self.rename_btn.config(state="disabled")
        self.stats_var.set("Ready. Select a parent folder and click Preview.")

    def _preview(self):
        root = self.folder_var.get().strip()
        if not root or not os.path.isdir(root):
            messagebox.showwarning("No folder", "Please select a valid parent folder first.")
            return

        self._clear_log()
        pairs = find_cad_pdf_pairs(root)

        if not pairs:
            self.stats_var.set("No CAD/PDF sibling folder pairs found under the selected folder.")
            return

        all_plans = []
        for cad_folder, pdf_folder in pairs:
            plan = build_rename_plan(cad_folder, pdf_folder)
            all_plans.extend([(cad_folder, *p) for p in plan])

        to_rename = 0
        for cad_folder, old_path, new_path, status in all_plans:
            old_name = os.path.basename(old_path)
            rel_folder = os.path.relpath(cad_folder, root)
            if status == 'rename':
                new_name = os.path.basename(new_path)
                tag = "rename"
                label = "✏ Rename"
                to_rename += 1
            elif status == 'already_correct':
                new_name = "— already correct —"
                tag = "correct"
                label = "✓ OK"
            else:
                new_name = f"⚠ {status}"
                tag = "error" if 'multiple' not in status else "warn"
                label = "✗ Skip"

            self.tree.insert("", "end", values=(label, old_name, new_name, rel_folder), tags=(tag,))

        self._plan = [(old_path, new_path, status)
                      for _, old_path, new_path, status in all_plans]

        total = len(all_plans)
        pairs_found = len(pairs)
        self.stats_var.set(
            f"Found {pairs_found} CAD/PDF pair(s) │ "
            f"{total} DWG file(s) scanned │ "
            f"{to_rename} will be renamed"
        )

        if to_rename > 0:
            self.rename_btn.config(state="normal")
        else:
            self.rename_btn.config(state="disabled")

    def _rename(self):
        if not self._plan:
            return
        to_rename = [(o, n, s) for o, n, s in self._plan if s == 'rename']
        if not to_rename:
            return

        confirm = messagebox.askyesno(
            "Confirm Rename",
            f"About to rename {len(to_rename)} file(s).\n\nThis cannot be undone automatically.\nProceed?"
        )
        if not confirm:
            return

        done, skipped, errors = execute_plan(self._plan)

        messagebox.showinfo(
            "Done",
            f"✅ Renamed:  {done}\n"
            f"⏭ Skipped (already correct):  {skipped}\n"
            f"❌ Errors / unmatched:  {errors}"
        )

        # Refresh preview to show updated state
        self._preview()
        self.rename_btn.config(state="disabled")


if __name__ == "__main__":
    app = App()
    app.mainloop()
