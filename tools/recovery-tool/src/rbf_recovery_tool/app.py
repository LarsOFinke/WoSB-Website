from __future__ import annotations

import queue
from pathlib import Path
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .backup_catalog import fetch_backup_catalog
from .config import TARGETS, controller_username, load_profile, target_label
from .controller import sync_latest
from .platform_support import open_directory
from .sftp_client import connect, fetch_host_fingerprint
from .verification import verify_encrypted_bundle


class RecoveryApp:
    """Operational dashboard; enrollment is deliberately not a GUI concern."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("RBF Recovery Tool")
        self.root.minsize(980, 680)
        self.root.configure(bg="#111827")
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.busy = False
        self.target = tk.StringVar(value="test")
        self.status = tk.StringVar(value="Ready")
        self.password = tk.StringVar()
        self._build()
        self._refresh_target()
        self.root.after(100, self._drain_events)

    def _build(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background="#111827")
        style.configure("TLabel", background="#111827", foreground="#e5e7eb")
        style.configure("Muted.TLabel", foreground="#9ca3af")
        style.configure("Title.TLabel", font=("TkDefaultFont", 22, "bold"), foreground="#f9fafb")
        style.configure("Section.TLabelframe", background="#1f2937", foreground="#f9fafb")
        style.configure("Section.TLabelframe.Label", background="#1f2937", foreground="#f9fafb")
        style.configure("TButton", padding=(10, 7))
        style.configure("Primary.TButton", background="#2563eb", foreground="white")
        outer = ttk.Frame(self.root, padding=18)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="RBF Recovery Tool", style="Title.TLabel").pack(anchor="w")
        ttk.Label(outer, text="Operational backup control · enrollment is completed on the website and terminal", style="Muted.TLabel").pack(anchor="w", pady=(2, 14))
        controls = ttk.Frame(outer)
        controls.pack(fill="x", pady=(0, 12))
        ttk.Label(controls, text="Target").pack(side="left")
        target_box = ttk.Combobox(controls, textvariable=self.target, values=TARGETS, state="readonly", width=16)
        target_box.pack(side="left", padx=8)
        target_box.bind("<<ComboboxSelected>>", lambda _event: self._refresh_target())
        ttk.Label(controls, textvariable=self.status, style="Muted.TLabel").pack(side="left", padx=12)
        ttk.Entry(controls, textvariable=self.password, show="*", width=24).pack(side="right")
        ttk.Label(controls, text="SSH passphrase (not saved)").pack(side="right", padx=8)
        metrics = ttk.Frame(outer)
        metrics.pack(fill="x", pady=(0, 12))
        self.target_card = self._card(metrics, "Selected target")
        self.connection_card = self._card(metrics, "Connection")
        self.storage_card = self._card(metrics, "Local storage")
        for card in (self.target_card, self.connection_card, self.storage_card):
            card.pack(side="left", fill="x", expand=True, padx=(0, 8))
        body = ttk.Frame(outer)
        body.pack(fill="both", expand=True)
        left = ttk.LabelFrame(body, text="Operations", style="Section.TLabelframe", padding=12)
        left.pack(side="left", fill="y", padx=(0, 12))
        self.buttons: list[ttk.Button] = []
        for text, command, primary in (("Check connection", self._check_host, False), ("Run fresh backup", self._pull, True), ("Sync published backup", self._sync, False), ("Refresh catalog", self._catalog, False), ("Verify local bundle…", self._verify_selected, False), ("Open backup folder", self._open_destination, False)):
            button = ttk.Button(left, text=text, command=command, style="Primary.TButton" if primary else "TButton")
            button.pack(fill="x", pady=4)
            self.buttons.append(button)
        ttk.Label(left, text="Test and production profiles, keys and storage are isolated.\nNo setup or automatic timers are managed here.", style="Muted.TLabel", wraplength=220).pack(anchor="w", pady=(14, 0))
        right = ttk.Frame(body)
        right.pack(side="left", fill="both", expand=True)
        catalog_frame = ttk.LabelFrame(right, text="Committed recovery sets", style="Section.TLabelframe", padding=8)
        catalog_frame.pack(fill="both", expand=True)
        columns = ("created", "status", "reason", "size", "recovery", "artifacts")
        self.catalog = ttk.Treeview(catalog_frame, columns=columns, show="headings")
        for column, heading, width in (("created", "UTC", 150), ("status", "Status", 90), ("reason", "Reason", 160), ("size", "Size", 90), ("recovery", "Recovery", 80), ("artifacts", "Artifacts", 260)):
            self.catalog.heading(column, text=heading)
            self.catalog.column(column, width=width, anchor="w")
        self.catalog.pack(fill="both", expand=True)
        log_frame = ttk.LabelFrame(right, text="Activity", style="Section.TLabelframe", padding=8)
        log_frame.pack(fill="x", pady=(10, 0))
        self.log = tk.Text(log_frame, height=6, wrap="word", state="disabled", bg="#0f172a", fg="#e5e7eb")
        self.log.pack(fill="both", expand=True)
        self._append_log("Ready. Select a configured target and run an operation.")

    @staticmethod
    def _card(parent: ttk.Frame, title: str) -> ttk.Frame:
        card = ttk.LabelFrame(parent, text=title, style="Section.TLabelframe", padding=10)
        label = ttk.Label(card, style="Muted.TLabel")
        label.pack(anchor="w")
        card.value_label = label  # type: ignore[attr-defined]
        return card

    def _refresh_target(self) -> None:
        profile = load_profile(self.target.get())
        self.target_card.value_label.configure(text=target_label(self.target.get()))  # type: ignore[attr-defined]
        configured = bool(profile.host and profile.username and profile.host_fingerprint)
        self.connection_card.value_label.configure(text=f"{'Configured' if configured else 'Not configured'} · {profile.host or '—'}")  # type: ignore[attr-defined]
        self.storage_card.value_label.configure(text=profile.destination_directory or "—")  # type: ignore[attr-defined]
        self._append_log(f"Selected {target_label(self.target.get())} target.")

    def _profile(self, files: bool = True):
        profile = load_profile(self.target.get()).normalized()
        if profile.username != controller_username(self.target.get()):
            raise ValueError(
                f"The {self.target.get()} profile is bound to {profile.username!r}; "
                f"expected {controller_username(self.target.get())!r}."
            )
        profile.validate(require_fingerprint=True, require_files=files)
        return profile

    def _set_busy(self, busy: bool, text: str = "") -> None:
        self.busy = busy
        for button in self.buttons:
            button.configure(state="disabled" if busy else "normal")
        if text:
            self.status.set(text)
        if not busy:
            self.password.set("")

    def _worker(self, text: str, function) -> None:
        if self.busy:
            return
        self._set_busy(True, text)
        def run() -> None:
            try:
                self.events.put(("success", function()))
            except Exception as exc:
                self.events.put(("error", exc))
        threading.Thread(target=run, daemon=True).start()

    def _check_host(self) -> None:
        try:
            profile = self._profile(files=False)
        except ValueError as exc:
            messagebox.showwarning("Target unavailable", str(exc), parent=self.root)
            return
        def check() -> tuple[str, str]:
            fingerprint = fetch_host_fingerprint(profile)
            client = connect(profile, password=self.password.get())
            client.close()
            return "host", fingerprint
        self._worker("Checking SSH authentication…", check)

    def _pull(self) -> None:
        try:
            profile = self._profile()
        except ValueError as exc:
            messagebox.showwarning("Target unavailable", str(exc), parent=self.root)
            return
        self._worker("Requesting, downloading and verifying backup…", lambda: ("pull", sync_latest(profile, password=self.password.get(), trigger=True)))

    def _sync(self) -> None:
        try:
            profile = self._profile()
        except ValueError as exc:
            messagebox.showwarning("Target unavailable", str(exc), parent=self.root)
            return
        self._worker("Syncing and verifying published backup…", lambda: ("sync", sync_latest(profile, password=self.password.get(), allow_empty=True)))

    def _catalog(self) -> None:
        try:
            profile = self._profile()
        except ValueError as exc:
            messagebox.showwarning("Target unavailable", str(exc), parent=self.root)
            return
        self._worker("Reading committed catalog…", lambda: ("catalog", fetch_backup_catalog(profile, password=self.password.get())))

    def _verify_selected(self) -> None:
        selected = filedialog.askopenfilename(title="Recovery bundle", filetypes=[("RBF bundle", "*.tar.gz.age"), ("All files", "*.*")])
        if not selected:
            return
        profile = load_profile(self.target.get())
        self._worker("Verifying local bundle…", lambda: ("verified", verify_encrypted_bundle(Path(selected), Path(profile.age_identity_path))))

    def _open_destination(self) -> None:
        path = Path(load_profile(self.target.get()).destination_directory).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        try:
            open_directory(path)
        except RuntimeError as exc:
            messagebox.showinfo("Backup folder", f"{path}\n\n{exc}", parent=self.root)

    def _drain_events(self) -> None:
        try:
            while True:
                kind, payload = self.events.get_nowait()
                self._set_busy(False, "Failed" if kind == "error" else "Completed")
                if kind == "error":
                    self._append_log(f"ERROR: {payload}")
                    messagebox.showerror("Operation failed", str(payload), parent=self.root)
                    continue
                if payload[0] == "host":
                    self._append_log(f"Connection verified: {payload[1]}")
                elif payload[0] in {"pull", "sync"}:
                    self._append_log(f"Backup synchronized: {payload[1] or 'no new set'}")
                    if payload[1]:
                        messagebox.showinfo("Backup ready", str(payload[1]), parent=self.root)
                elif payload[0] == "catalog":
                    self.catalog.delete(*self.catalog.get_children())
                    for entry in payload[1]:
                        self.catalog.insert("", "end", values=(entry.created_at or "-", entry.status, entry.reason, f"{entry.total_size_bytes / (1024 * 1024):.1f} MiB", "yes" if entry.recoverable else "no", ", ".join(entry.artifact_types) or entry.detail))
                    self._append_log(f"Catalog refreshed: {len(payload[1])} set(s).")
                elif payload[0] == "verified":
                    self._append_log(f"Bundle verified: {payload[1].bundle_sha256}")
        except queue.Empty:
            pass
        self.root.after(100, self._drain_events)

    def _append_log(self, message: str) -> None:
        if not hasattr(self, "log"):
            return
        self.log.configure(state="normal")
        self.log.insert("end", message + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")


def main() -> None:
    root = tk.Tk()
    RecoveryApp(root)
    root.mainloop()
