from tkinter import messagebox, ttk

from .backup_catalog import fetch_backup_catalog


class RecoveryCatalogMixin:
    def _build_catalog(self, outer) -> None:
        catalog_frame = ttk.LabelFrame(
            outer, text="Backups auf dem Backup-Server", padding=8
        )
        catalog_frame.pack(fill="both", pady=(0, 10))
        catalog_actions = ttk.Frame(catalog_frame)
        catalog_actions.pack(fill="x", pady=(0, 6))
        self.catalog_button = ttk.Button(
            catalog_actions, text="Katalog aktualisieren", command=self._refresh_catalog
        )
        self.catalog_button.pack(side="left")
        ttk.Label(
            catalog_actions,
            text="Erfolgreich = Commit-Manifest, Artefakte und Prüfsummen vollständig",
        ).pack(side="left", padx=(10, 0))
        columns = ("created", "status", "reason", "size", "recovery", "artifacts")
        self.catalog = ttk.Treeview(
            catalog_frame, columns=columns, show="headings", height=5
        )
        headings = {
            "created": "Zeitpunkt (UTC)",
            "status": "Status",
            "reason": "Anlass",
            "size": "Größe",
            "recovery": "Recovery",
            "artifacts": "Bestandteile",
        }
        widths = {
            "created": 190,
            "status": 100,
            "reason": 100,
            "size": 90,
            "recovery": 85,
            "artifacts": 360,
        }
        for column in columns:
            self.catalog.heading(column, text=headings[column])
            self.catalog.column(column, width=widths[column], anchor="w")
        self.catalog.pack(fill="both", expand=True)

    def _refresh_catalog(self) -> None:
        profile = self._save()
        if not profile:
            return
        try:
            profile.validate(require_fingerprint=True)
        except ValueError as exc:
            messagebox.showwarning("Host-Key fehlt", str(exc), parent=self.root)
            return
        password = self.vars["password"].get()
        self._worker(
            "Backup-Katalog wird gelesen …",
            lambda: ("catalog", fetch_backup_catalog(profile, password=password)),
        )
