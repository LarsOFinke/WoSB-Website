from datetime import datetime, timezone
from pathlib import Path
from tkinter import filedialog, messagebox

from .docker_lab import (
    connection as lab_connection,
    docker_is_rootless,
    import_check_bundle,
    initialize_lab,
    lab_status,
    start_lab,
    stop_lab,
    verify_recovery,
)
from .linux_setup import setup_rootless_lab
from .platform_support import open_directory


class RecoveryLabMixin:
    def _refresh_lab_status(self) -> None:
        try:
            status = lab_status()
            docker_mode = (
                "rootless"
                if status.docker_available and docker_is_rootless()
                else ("rootful" if status.docker_available else "nicht verfügbar")
            )
            self.vars["lab_status"].set(
                f"Lokales DB-Labor: {status.detail} · Docker {docker_mode}"
            )
        except Exception as exc:
            self.vars["lab_status"].set(f"Lokales DB-Labor: Fehler ({exc})")

    def _lab_setup(self) -> None:
        from .automation import executable_path

        self._worker(
            "Rootless Docker und das DB-Labor werden eingerichtet …",
            lambda: ("lab_setup", setup_rootless_lab(executable_path())),
        )

    def _lab_init(self) -> None:
        try:
            details = initialize_lab()
            self._append_log(f"DB-Labor initialisiert: {details.host}:{details.port}")
            self._refresh_lab_status()
        except Exception as exc:
            messagebox.showerror("DB-Labor", str(exc), parent=self.root)

    def _lab_start(self) -> None:
        self._worker(
            "Lokales PostgreSQL-Labor wird gestartet …",
            lambda: ("lab_started", start_lab()),
        )

    def _lab_stop(self) -> None:
        self._worker(
            "Lokales PostgreSQL-Labor wird gestoppt …",
            lambda: ("lab_stopped", stop_lab()),
        )

    def _lab_credentials(self) -> None:
        try:
            details = lab_connection()
        except Exception as exc:
            messagebox.showerror("DB-Labor", str(exc), parent=self.root)
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(details.dsn)
        messagebox.showinfo(
            "Lokale PostgreSQL-Verbindungsdaten",
            f"Host: {details.host}\nPort: {details.port}\n"
            f"Datenbank: {details.database}\nBenutzer: {details.username}\n"
            f"Kennwort: {details.password}\n\n"
            "Die vollständige DSN wurde in die Zwischenablage kopiert.",
            parent=self.root,
        )

    def _report_path(self, prefix: str) -> Path:
        root = (
            Path(self.vars["destination_directory"].get()).expanduser()
            / "recovery-reports"
        )
        root.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        return root / f"{prefix}-{timestamp}.json"

    def _select_bundle(self, title: str) -> Path | None:
        selected = filedialog.askopenfilename(
            title=title,
            filetypes=[
                ("RBF Recovery Bundle", "*.tar.gz.age"),
                ("Alle Dateien", "*.*"),
            ],
        )
        return Path(selected) if selected else None

    def _lab_import_check(self) -> None:
        bundle = self._select_bundle(
            "Recovery-Bundle für reine DB-Importprüfung auswählen"
        )
        if bundle is None:
            return
        identity = Path(self.vars["age_identity_path"].get())
        report = self._report_path("import-check")
        self._worker(
            "Bundle wird technisch importiert; Migration und API werden dabei nicht geprüft …",
            lambda: (
                "lab_import_checked",
                import_check_bundle(bundle, identity, report),
            ),
        )

    def _recovery_verify(self) -> None:
        bundle = self._select_bundle(
            "Recovery-Bundle für vollständigen Recovery-Preflight auswählen"
        )
        if bundle is None:
            return
        repository = filedialog.askdirectory(
            title="WoSB-Repository mit aktuellem Backend auswählen",
            mustexist=True,
        )
        if not repository:
            return
        identity = Path(self.vars["age_identity_path"].get())
        report = self._report_path("recovery-preflight")
        self._worker(
            "Dump wird importiert, migriert und mit dem aktuellen API-Image auf Readiness geprüft …",
            lambda: (
                "recovery_verified",
                verify_recovery(bundle, identity, Path(repository), report),
            ),
        )

    def _open_destination(self) -> None:
        path = Path(self.vars["destination_directory"].get()).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        try:
            open_directory(path)
        except RuntimeError as exc:
            messagebox.showinfo("Zielordner", f"{path}\n\n{exc}", parent=self.root)
