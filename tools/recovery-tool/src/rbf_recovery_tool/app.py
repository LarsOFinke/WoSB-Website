from __future__ import annotations

from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .config import Profile, load_profile, save_profile
from .platform_support import open_directory
from .sftp_client import download_latest, fetch_host_fingerprint
from .verification import VerificationResult, generate_identity, verify_encrypted_bundle


class RecoveryApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("RBF Recovery Tool")
        self.root.minsize(820, 620)
        self.profile = load_profile()
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.busy = False
        self.vars = {
            "host": tk.StringVar(value=self.profile.host),
            "port": tk.StringVar(value=str(self.profile.port)),
            "username": tk.StringVar(value=self.profile.username),
            "remote_directory": tk.StringVar(value=self.profile.remote_directory),
            "destination_directory": tk.StringVar(value=self.profile.destination_directory),
            "ssh_key_path": tk.StringVar(value=self.profile.ssh_key_path),
            "age_identity_path": tk.StringVar(value=self.profile.age_identity_path),
            "host_fingerprint": tk.StringVar(value=self.profile.host_fingerprint),
            "password": tk.StringVar(),
            "deep_verify": tk.BooleanVar(value=True),
            "status": tk.StringVar(value="Bereit"),
        }
        self._build()
        self.root.after(100, self._drain_events)

    def _build(self) -> None:
        outer = ttk.Frame(self.root, padding=14)
        outer.pack(fill="both", expand=True)
        profile_frame = ttk.LabelFrame(outer, text="Serverprofil", padding=12)
        profile_frame.pack(fill="x")
        profile_frame.columnconfigure(1, weight=1)
        rows = [
            ("Server", "host", None),
            ("SSH-Port", "port", None),
            ("SSH-Benutzer", "username", None),
            ("Remote-Verzeichnis", "remote_directory", None),
            ("Lokaler Zielordner", "destination_directory", self._choose_destination),
            ("SSH-Schlüssel (optional)", "ssh_key_path", self._choose_ssh_key),
            ("age-Identität", "age_identity_path", self._choose_identity),
            ("Gepinnter Host-Key", "host_fingerprint", None),
            ("SSH-Kennwort/Passphrase (nicht gespeichert)", "password", None),
        ]
        for index, (label, key, chooser) in enumerate(rows):
            ttk.Label(profile_frame, text=label).grid(
                row=index, column=0, sticky="w", padx=(0, 10), pady=4
            )
            show = "*" if key == "password" else None
            entry = ttk.Entry(profile_frame, textvariable=self.vars[key], show=show)
            entry.grid(row=index, column=1, sticky="ew", pady=4)
            if key == "host_fingerprint":
                entry.configure(state="readonly")
            if chooser:
                ttk.Button(profile_frame, text="…", width=4, command=chooser).grid(
                    row=index, column=2, padx=(6, 0), pady=4
                )
            if key == "age_identity_path":
                self.identity_button = ttk.Button(
                    profile_frame, text="Neu", command=self._generate_identity
                )
                self.identity_button.grid(row=index, column=3, padx=(6, 0), pady=4)

        actions = ttk.Frame(outer, padding=(0, 12, 0, 8))
        actions.pack(fill="x")
        self.save_button = ttk.Button(actions, text="Profil speichern", command=self._save)
        self.save_button.pack(side="left")
        self.host_button = ttk.Button(actions, text="Host-Key prüfen", command=self._check_host)
        self.host_button.pack(side="left", padx=6)
        self.download_button = ttk.Button(
            actions, text="Neuestes Backup laden", command=self._download
        )
        self.download_button.pack(side="left", padx=6)
        self.verify_button = ttk.Button(
            actions, text="Lokales Bundle prüfen", command=self._verify_selected
        )
        self.verify_button.pack(side="left", padx=6)
        ttk.Button(
            actions, text="Zielordner öffnen", command=self._open_destination
        ).pack(side="right")

        options = ttk.Frame(outer)
        options.pack(fill="x", pady=(0, 8))
        ttk.Checkbutton(
            options,
            text="Nach dem Download vollständig entschlüsseln und Manifest prüfen",
            variable=self.vars["deep_verify"],
        ).pack(side="left")

        self.progress = ttk.Progressbar(outer, mode="determinate", maximum=100)
        self.progress.pack(fill="x", pady=(0, 5))
        ttk.Label(outer, textvariable=self.vars["status"]).pack(anchor="w")

        log_frame = ttk.LabelFrame(outer, text="Protokoll", padding=8)
        log_frame.pack(fill="both", expand=True, pady=(10, 0))
        self.log = tk.Text(log_frame, height=14, wrap="word", state="disabled")
        self.log.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(log_frame, command=self.log.yview)
        scrollbar.pack(side="right", fill="y")
        self.log.configure(yscrollcommand=scrollbar.set)
        self._append_log(
            "Das Profil speichert keine Kennwörter oder privaten Schlüssel, "
            "sondern nur Dateipfade."
        )

    def _profile_from_form(self) -> Profile:
        return Profile(
            host=self.vars["host"].get(),
            port=int(self.vars["port"].get()),
            username=self.vars["username"].get(),
            remote_directory=self.vars["remote_directory"].get(),
            destination_directory=self.vars["destination_directory"].get(),
            ssh_key_path=self.vars["ssh_key_path"].get(),
            age_identity_path=self.vars["age_identity_path"].get(),
            host_fingerprint=self.vars["host_fingerprint"].get(),
        ).normalized()

    def _save(self) -> Profile | None:
        try:
            profile = self._profile_from_form()
            path = save_profile(profile)
            self.profile = profile
            self._append_log(f"Profil gespeichert: {path}")
            return profile
        except Exception as exc:
            messagebox.showerror("Profil ungültig", str(exc), parent=self.root)
            return None

    def _choose_destination(self) -> None:
        selected = filedialog.askdirectory(
            initialdir=self.vars["destination_directory"].get() or None
        )
        if selected:
            self.vars["destination_directory"].set(selected)

    def _choose_ssh_key(self) -> None:
        selected = filedialog.askopenfilename(title="SSH-Schlüssel auswählen")
        if selected:
            self.vars["ssh_key_path"].set(selected)

    def _choose_identity(self) -> None:
        selected = filedialog.askopenfilename(title="age-Identität auswählen")
        if selected:
            self.vars["age_identity_path"].set(selected)

    def _generate_identity(self) -> None:
        selected = filedialog.asksaveasfilename(
            title="Neue age-Identität speichern",
            initialfile="rbf-recovery-identity.txt",
            defaultextension=".txt",
            filetypes=[("age-Identität", "*.txt"), ("Alle Dateien", "*.*")],
        )
        if not selected:
            return
        target = Path(selected)

        def operation():
            return ("identity", target, generate_identity(target))

        self._worker("Neue age-Identität wird erstellt …", operation)

    def _set_busy(self, busy: bool, text: str = "") -> None:
        self.busy = busy
        state = "disabled" if busy else "normal"
        for button in (
            self.save_button,
            self.host_button,
            self.download_button,
            self.verify_button,
            self.identity_button,
        ):
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
                result = function()
                self.events.put(("success", result))
            except Exception as exc:
                self.events.put(("error", exc))

        threading.Thread(target=run, daemon=True).start()

    def _check_host(self) -> None:
        profile = self._save()
        if not profile:
            return

        def operation():
            fingerprint = fetch_host_fingerprint(profile)
            return ("host", fingerprint)

        self._worker("SSH-Host-Key wird geprüft …", operation)

    def _download(self) -> None:
        profile = self._save()
        if not profile:
            return
        try:
            profile.validate(require_fingerprint=True)
        except ValueError as exc:
            messagebox.showwarning("Host-Key fehlt", str(exc), parent=self.root)
            return
        password = self.vars["password"].get()
        deep_verify = bool(self.vars["deep_verify"].get())

        def progress(transferred: int, total: int) -> None:
            percent = int(transferred * 100 / total) if total else 0
            self.events.put(("progress", max(0, min(100, percent))))

        def operation():
            bundle = download_latest(profile, password=password, progress=progress)
            if deep_verify:
                result = verify_encrypted_bundle(bundle, Path(profile.age_identity_path))
                return ("download_verified", bundle, result)
            return ("download", bundle)

        self._worker("Recovery-Bundle wird geladen …", operation)

    def _verify_selected(self) -> None:
        selected = filedialog.askopenfilename(
            title="Recovery-Bundle auswählen",
            filetypes=[("RBF Recovery Bundle", "*.tar.gz.age"), ("Alle Dateien", "*.*")],
        )
        if not selected:
            return
        identity = Path(self.vars["age_identity_path"].get())
        self._worker(
            "Recovery-Bundle wird vollständig geprüft …",
            lambda: ("verified", Path(selected), verify_encrypted_bundle(Path(selected), identity)),
        )

    def _open_destination(self) -> None:
        path = Path(self.vars["destination_directory"].get()).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        try:
            open_directory(path)
        except RuntimeError as exc:
            messagebox.showinfo("Zielordner", f"{path}\n\n{exc}", parent=self.root)

    def _drain_events(self) -> None:
        try:
            while True:
                kind, payload = self.events.get_nowait()
                if kind == "progress":
                    self.progress["value"] = int(payload)
                    continue
                if kind == "error":
                    self._set_busy(False, "Fehlgeschlagen")
                    self._append_log(f"FEHLER: {payload}")
                    messagebox.showerror("Vorgang fehlgeschlagen", str(payload), parent=self.root)
                    continue
                self._handle_success(payload)
        except queue.Empty:
            pass
        self.root.after(100, self._drain_events)

    def _handle_success(self, payload: object) -> None:
        self._set_busy(False, "Erfolgreich")
        self.progress["value"] = 100
        if isinstance(payload, tuple) and payload and payload[0] == "host":
            fingerprint = str(payload[1])
            current = self.vars["host_fingerprint"].get()
            if current and current != fingerprint:
                self.vars["status"].set("Host-Key abgelehnt")
                messagebox.showerror(
                    "SSH-Host-Key geändert",
                    f"Gespeichert: {current}\nAktuell: {fingerprint}\n\n"
                    "Nicht verbinden, bevor die Änderung unabhängig geprüft wurde.",
                    parent=self.root,
                )
                return
            if not current:
                trusted = messagebox.askyesno(
                    "SSH-Host-Key vertrauen?",
                    f"Fingerprint:\n{fingerprint}\n\n"
                    "Über einen zweiten Kanal prüfen und nur dann bestätigen.",
                    parent=self.root,
                )
                if not trusted:
                    return
                self.vars["host_fingerprint"].set(fingerprint)
                self._save()
            self._append_log(f"SSH-Host-Key bestätigt: {fingerprint}")
            return
        if isinstance(payload, tuple) and payload and payload[0] == "identity":
            identity_path = Path(payload[1])
            public_key = str(payload[2])
            self.vars["age_identity_path"].set(str(identity_path))
            self._save()
            self._append_log(f"Neue age-Identität erstellt: {identity_path}")
            messagebox.showinfo(
                "Öffentlichen Schlüssel auf dem Pi eintragen",
                f"Privater Schlüssel:\n{identity_path}\n\n"
                f"Öffentlicher Schlüssel:\n{public_key}\n\n"
                "BACKUP_AGE_RECIPIENT auf dem Pi auf diesen öffentlichen Schlüssel setzen.",
                parent=self.root,
            )
            return
        if (
            isinstance(payload, tuple)
            and payload
            and payload[0] in {"download", "download_verified", "verified"}
        ):
            bundle = payload[1]
            self._append_log(f"Bundle: {bundle}")
            if len(payload) > 2 and isinstance(payload[2], VerificationResult):
                result = payload[2]
                self._append_log(
                    f"Vollständig geprüft: Version {result.version or 'unbekannt'}, "
                    f"{result.file_count} Dateien, SHA-256 {result.bundle_sha256}"
                )
            messagebox.showinfo("Recovery-Bundle bereit", str(bundle), parent=self.root)

    def _append_log(self, message: str) -> None:
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
