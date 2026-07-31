# RBF Recovery Tool

Gemeinsamer Python-/Tk-Client für die gefrorenen Windows- und Linux-Recovery-Programme. Er lädt
das neueste verschlüsselte Recovery-Bundle über SFTP mit explizit gepinntem SSH-Host-Key, prüft
die Transport-Prüfsumme, entschlüsselt mit einer ausschließlich lokal vorhandenen age-Identität
und validiert das vollständige Manifest.

Das Profil speichert keine Passwörter oder privaten Schlüssel, sondern nur Pfade und Metadaten.
Downloads erfolgen über `.part`-Dateien mit atomarer Umbenennung. Archive werden auf Pfad-
Traversal, Links, Spezialdateien, Duplikate, Größenlimits und jede Manifest-Prüfsumme geprüft.

## Betriebsarten

```text
rbf-recovery-tool                 grafische Oberfläche
rbf-recovery-tool pull            neuestes Bundle laden und vollständig prüfen
rbf-recovery-tool verify ...      lokales Bundle prüfen
rbf-recovery-tool timer ...       Linux-systemd-Benutzertimer verwalten
rbf-recovery-tool lab ...         lokales PostgreSQL-Recovery-Labor verwalten
```

Windows und Linux werden nativ auf dem jeweiligen Betriebssystem gebaut. `age`, `age-keygen`,
Paramiko und ihre nativen Abhängigkeiten werden von PyInstaller eingebettet.

## Linux-spezifisch

Der Linux-Client kann einen systemd-Benutzertimer einrichten und optional ein lokales
PostgreSQL-Recovery-Labor verwenden. Das Labor bevorzugt rootless Docker, bindet PostgreSQL nur
an Loopback und kann den verifizierten DB-Dump aus einem Recovery-Bundle direkt importieren.
Die Docker-Paketinstallation ist bewusst ein getrenntes administratives Hilfsskript; die GUI und
der normale Backup-Client benötigen keine Root-Rechte und verändern keine Firewall.
