from __future__ import annotations

from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .automation import install_pull_timer, remove_pull_timer
from .backup_catalog import fetch_backup_catalog
from .config import TARGETS, Profile, load_config, load_profile, save_profile, target_label
from .enrollment import load_response
from .platform_support import open_directory
from .sftp_client import download_latest, fetch_host_fingerprint
from .verification import verify_encrypted_bundle


class RecoveryApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("RBF Recovery Tool")
        self.root.minsize(980, 720)
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.busy = False
        config = load_config()
        self.target = tk.StringVar(value=config.active_target)
        self.vars = {
            "host": tk.StringVar(), "port": tk.StringVar(), "username": tk.StringVar(),
            "remote_directory": tk.StringVar(), "destination_directory": tk.StringVar(),
            "ssh_key_path": tk.StringVar(), "age_identity_path": tk.StringVar(),
            "host_fingerprint": tk.StringVar(), "password": tk.StringVar(),
            "local_backup_host": tk.BooleanVar(value=True), "status": tk.StringVar(value="Ready"),
        }
        self._load_target()
        self._build()
        self.root.after(100, self._drain_events)

    def _load_target(self) -> None:
        profile = load_profile(self.target.get())
        if not Path(profile.ssh_key_path).is_file():
            legacy_key = Path.home() / "RBF-Recovery" / "rbf-recovery-readonly-ed25519"
            if legacy_key.is_file():
                profile.ssh_key_path = str(legacy_key)
        if not Path(profile.age_identity_path).is_file():
            legacy_identity = Path.home() / "RBF-Recovery" / "rbf-recovery-identity.txt"
            if legacy_identity.is_file():
                profile.age_identity_path = str(legacy_identity)
        for key in (
            "host", "port", "username", "remote_directory", "destination_directory",
            "ssh_key_path", "age_identity_path", "host_fingerprint",
        ):
            value = getattr(profile, key)
            self.vars[key].set(str(value))

    def _build(self) -> None:
        outer = ttk.Frame(self.root, padding=14)
        outer.pack(fill="both", expand=True)
        header = ttk.Frame(outer)
        header.pack(fill="x", pady=(0, 10))
        ttk.Label(header, text="Recovery target", font=("TkDefaultFont", 12, "bold")).pack(side="left")
        target_box = ttk.Combobox(header, textvariable=self.target, values=TARGETS, state="readonly", width=16)
        target_box.pack(side="left", padx=10)
        target_box.bind("<<ComboboxSelected>>", lambda _event: self._switch_target())
        ttk.Label(header, text="Test and production are stored separately; select the target deliberately.").pack(side="left")

        setup = ttk.LabelFrame(outer, text="Guided setup", padding=10)
        setup.pack(fill="x", pady=(0, 10))
        ttk.Button(setup, text="Import enrollment response…", command=self._import_response).pack(side="left")
        ttk.Checkbutton(
            setup,
            text="This device is the backup host (use loopback recovery account)",
            variable=self.vars["local_backup_host"],
        ).pack(side="left", padx=12)
        ttk.Label(
            setup,
            text="The response supplies the pinned host key; private keys remain local and are never saved in the profile.",
            wraplength=600,
        ).pack(side="left", fill="x", expand=True)

        profile_frame = ttk.LabelFrame(outer, text="Target connection", padding=10)
        profile_frame.pack(fill="x", pady=(0, 10))
        profile_frame.columnconfigure(1, weight=1)
        fields = [
            ("Backup host", "host", None), ("SSH port", "port", None),
            ("SSH user", "username", None), ("SFTP directory", "remote_directory", None),
            ("Local backup folder", "destination_directory", self._choose_destination),
            ("Private read-only SSH key", "ssh_key_path", self._choose_ssh_key),
            ("Private age identity", "age_identity_path", self._choose_identity),
            ("Pinned host fingerprint", "host_fingerprint", None),
            ("SSH passphrase (not saved)", "password", None),
        ]
        for row, (label, key, chooser) in enumerate(fields):
            ttk.Label(profile_frame, text=label).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=3)
            entry = ttk.Entry(profile_frame, textvariable=self.vars[key], show="*" if key == "password" else None)
            entry.grid(row=row, column=1, sticky="ew", pady=3)
            if key == "host_fingerprint":
                entry.configure(state="readonly")
            if chooser:
                ttk.Button(profile_frame, text="Browse…", command=chooser).grid(row=row, column=2, padx=(6, 0))

        actions = ttk.Frame(outer)
        actions.pack(fill="x", pady=(0, 8))
        self.buttons = []
        for text, command in (
            ("Save target", self._save), ("Test host key", self._check_host),
            ("Pull and verify newest", self._pull), ("Refresh catalog", self._catalog),
            ("Verify local bundle…", self._verify_selected),
        ):
            button = ttk.Button(actions, text=text, command=command)
            button.pack(side="left", padx=(0, 6))
            self.buttons.append(button)
        ttk.Button(actions, text="Open backup folder", command=self._open_destination).pack(side="right")
        timer = ttk.Frame(outer)
        timer.pack(fill="x", pady=(0, 8))
        ttk.Button(timer, text="Enable daily pull timer", command=self._enable_timer).pack(side="left")
        ttk.Button(timer, text="Remove pull timer", command=self._disable_timer).pack(side="left", padx=6)

        catalog_frame = ttk.LabelFrame(outer, text="Committed recovery sets", padding=8)
        catalog_frame.pack(fill="both", expand=True, pady=(0, 10))
        columns = ("created", "status", "reason", "size", "recovery", "artifacts")
        self.catalog = ttk.Treeview(catalog_frame, columns=columns, show="headings", height=7)
        headings = {"created": "UTC", "status": "Status", "reason": "Reason", "size": "Size", "recovery": "Recovery", "artifacts": "Artifacts"}
        for column in columns:
            self.catalog.heading(column, text=headings[column])
            self.catalog.column(column, width=120 if column != "artifacts" else 300, anchor="w")
        self.catalog.pack(fill="both", expand=True)
        ttk.Label(outer, textvariable=self.vars["status"]).pack(anchor="w")
        log_frame = ttk.LabelFrame(outer, text="Activity", padding=8)
        log_frame.pack(fill="x", pady=(8, 0))
        self.log = tk.Text(log_frame, height=5, wrap="word", state="disabled")
        self.log.pack(fill="both", expand=True)
        self._append_log("Choose a target, import its response, then test the pinned host key.")

    def _profile_from_form(self) -> Profile:
        existing = load_profile(self.target.get())
        return Profile(
            host=self.vars["host"].get(), port=int(self.vars["port"].get()),
            username=self.vars["username"].get(), remote_directory=self.vars["remote_directory"].get(),
            destination_directory=self.vars["destination_directory"].get(),
            ssh_key_path=self.vars["ssh_key_path"].get(), age_identity_path=self.vars["age_identity_path"].get(),
            host_fingerprint=self.vars["host_fingerprint"].get(),
            enrollment_id=existing.enrollment_id,
        ).normalized()

    def _save(self) -> Profile | None:
        try:
            profile = self._profile_from_form()
            path = save_profile(profile, self.target.get())
            self._append_log(f"Saved {target_label(self.target.get())} target: {path}")
            return profile
        except (ValueError, OSError) as exc:
            messagebox.showerror("Target is invalid", str(exc), parent=self.root)
            return None

    def _switch_target(self) -> None:
        if self.busy:
            return
        self._load_target()
        self._append_log(f"Switched to {target_label(self.target.get())}; no values are shared automatically.")

    def _import_response(self) -> None:
        selected = filedialog.askopenfilename(title="Enrollment response", filetypes=[("JSON", "*.json"), ("All files", "*.*")])
        if not selected:
            return
        try:
            response = load_response(Path(selected))
            local = self.vars["local_backup_host"].get()
            self.vars["host"].set("127.0.0.1" if local else response["host"])
            self.vars["port"].set(str(response["port"]))
            username = (response.get("recovery_username") or "rbf-recovery") if local else response["username"]
            self.vars["username"].set(username)
            self.vars["remote_directory"].set(response["remote_directory"])
            self.vars["host_fingerprint"].set(response["host_key_fingerprint"])
            self._append_log(f"Imported enrollment {response['enrollment_id']}; private files were not copied or stored.")
            messagebox.showinfo("Response imported", "Now select the private read-only SSH key and age identity, then click Test host key.", parent=self.root)
        except (RuntimeError, ValueError, OSError) as exc:
            messagebox.showerror("Response could not be imported", str(exc), parent=self.root)

    def _choose_destination(self) -> None:
        selected = filedialog.askdirectory(initialdir=self.vars["destination_directory"].get() or None)
        if selected:
            self.vars["destination_directory"].set(selected)

    def _choose_ssh_key(self) -> None:
        selected = filedialog.askopenfilename(title="Private read-only SSH key")
        if selected:
            self.vars["ssh_key_path"].set(selected)

    def _choose_identity(self) -> None:
        selected = filedialog.askopenfilename(title="Private age identity")
        if selected:
            self.vars["age_identity_path"].set(selected)

    def _set_busy(self, busy: bool, text: str = "") -> None:
        self.busy = busy
        state = "disabled" if busy else "normal"
        for button in self.buttons:
            button.configure(state=state)
        if text:
            self.vars["status"].set(text)
        if not busy:
            self.vars["password"].set("")

    def _worker(self, name: str, function) -> None:
        if self.busy:
            return
        self._set_busy(True, name)

        def run() -> None:
            try:
                self.events.put(("success", function()))
            except Exception as exc:
                self.events.put(("error", exc))

        threading.Thread(target=run, daemon=True).start()

    def _check_host(self) -> None:
        profile = self._save()
        if not profile:
            return

        def operation():
            actual = fetch_host_fingerprint(profile)
            expected = profile.host_fingerprint
            if expected and expected != actual:
                raise RuntimeError(f"Host-key mismatch: pinned {expected}, live {actual}")
            return ("host", actual)

        self._worker("Checking live SSH host key…", operation)

    def _pull(self) -> None:
        profile = self._save()
        if not profile:
            return
        try:
            profile.validate(require_fingerprint=True, require_files=True)
        except ValueError as exc:
            messagebox.showwarning("Setup incomplete", str(exc), parent=self.root)
            return
        password = self.vars["password"].get()
        self._worker(
            "Pulling, checking and decrypting the newest committed bundle…",
            lambda: ("pull", download_latest(profile, password=password), profile),
        )

    def _catalog(self) -> None:
        profile = self._save()
        if not profile:
            return
        try:
            profile.validate(require_fingerprint=True, require_files=True)
        except ValueError as exc:
            messagebox.showwarning("Setup incomplete", str(exc), parent=self.root)
            return
        self._worker(
            "Reading committed recovery catalog…",
            lambda: ("catalog", fetch_backup_catalog(profile, password=self.vars["password"].get())),
        )

    def _verify_selected(self) -> None:
        selected = filedialog.askopenfilename(title="Recovery bundle", filetypes=[("RBF bundle", "*.tar.gz.age"), ("All files", "*.*")])
        if not selected:
            return
        identity = Path(self.vars["age_identity_path"].get()).expanduser()
        self._worker("Verifying local encrypted bundle…", lambda: ("verified", Path(selected), verify_encrypted_bundle(Path(selected), identity)))

    def _enable_timer(self) -> None:
        profile = self._save()
        if not profile:
            return
        try:
            service, timer = install_pull_timer(self.target.get())
            self._append_log(f"Enabled timer: {service} / {timer}")
        except (RuntimeError, OSError) as exc:
            messagebox.showerror("Timer could not be enabled", str(exc), parent=self.root)

    def _disable_timer(self) -> None:
        remove_pull_timer(self.target.get())
        self._append_log(f"Removed {target_label(self.target.get())} pull timer.")

    def _open_destination(self) -> None:
        path = Path(self.vars["destination_directory"].get()).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        try:
            open_directory(path)
        except RuntimeError as exc:
            messagebox.showinfo("Backup folder", f"{path}\n\n{exc}", parent=self.root)

    def _drain_events(self) -> None:
        try:
            while True:
                kind, payload = self.events.get_nowait()
                if kind == "error":
                    self._set_busy(False, "Failed")
                    self._append_log(f"ERROR: {payload}")
                    messagebox.showerror("Operation failed", str(payload), parent=self.root)
                    continue
                self._set_busy(False, "Completed")
                if isinstance(payload, tuple) and payload[0] == "host":
                    self.vars["host_fingerprint"].set(str(payload[1]))
                    self._save()
                    self._append_log(f"Pinned host key verified: {payload[1]}")
                elif isinstance(payload, tuple) and payload[0] == "catalog":
                    self.catalog.delete(*self.catalog.get_children())
                    for entry in payload[1]:
                        self.catalog.insert("", "end", values=(
                            entry.created_at or "-", entry.status, entry.reason,
                            f"{entry.total_size_bytes / (1024 * 1024):.1f} MiB",
                            "yes" if entry.recoverable else "no", ", ".join(entry.artifact_types) or entry.detail,
                        ))
                    self._append_log(f"Catalog refreshed: {len(payload[1])} set(s).")
                elif isinstance(payload, tuple) and payload[0] == "pull":
                    self._append_log(f"Downloaded and verified: {payload[1]}")
                    messagebox.showinfo("Recovery bundle ready", str(payload[1]), parent=self.root)
                elif isinstance(payload, tuple) and payload[0] == "verified":
                    result = payload[2]
                    self._append_log(f"Verified release {result.version or 'unknown'}; {result.file_count} files; {result.bundle_sha256}")
                    messagebox.showinfo("Bundle verified", str(payload[1]), parent=self.root)
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
    try:
        ttk.Style(root).theme_use("vista")
    except tk.TclError:
        pass
    RecoveryApp(root)
    root.mainloop()
