from pathlib import Path
import queue
from tkinter import messagebox

from .verification import VerificationResult


class RecoveryEventMixin:
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
                    messagebox.showerror(
                        "Vorgang fehlgeschlagen", str(payload), parent=self.root
                    )
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
            and payload[0] in {"lab_import_checked", "recovery_verified"}
        ):
            result = payload[1]
            self._refresh_lab_status()
            if payload[0] == "lab_import_checked":
                self._append_log(
                    f"DB-Importprüfung bestanden; dies ist kein vollständiger Recovery-Nachweis. Bericht: {result.report}"
                )
                messagebox.showinfo(
                    "DB-Importprüfung bestanden",
                    "Der Dump ist technisch importierbar. Migrationen, Schlüssel und "
                    "API-Readiness wurden nicht geprüft.\n\n"
                    f"Bericht: {result.report}",
                    parent=self.root,
                )
            else:
                self._append_log(
                    f"Vollständiger Recovery-Preflight bestanden ({result.compatibility}); Bericht: {result.report}"
                )
                messagebox.showinfo(
                    "Recovery vollständig verifiziert",
                    "Import, Migration, Schlüsselprüfung und API-Readiness waren "
                    "erfolgreich.\n\n"
                    f"Bericht: {result.report}",
                    parent=self.root,
                )
            return
        if isinstance(payload, tuple) and payload and payload[0].startswith("lab_"):
            self._refresh_lab_status()
            if payload[0] in {"lab_started", "lab_restored"}:
                details = payload[1]
                self._append_log(
                    f"DB-Labor bereit: {details.host}:{details.port}/{details.database} "
                    f"als {details.username}"
                )
                messagebox.showinfo(
                    "Lokales DB-Labor bereit",
                    f"Host: {details.host}\nPort: {details.port}\n"
                    f"Datenbank: {details.database}\nBenutzer: {details.username}\n\n"
                    "Das Kennwort liegt ausschließlich in der lokalen geschützten Lab-Konfiguration.",
                    parent=self.root,
                )
            elif payload[0] == "lab_setup":
                self._append_log(
                    "Rootless Docker und das lokale DB-Labor wurden eingerichtet."
                )
            else:
                self._append_log("DB-Labor wurde gestoppt.")
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
