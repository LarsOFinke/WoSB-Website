from __future__ import annotations

from pathlib import Path

from app.configuration import Settings, SettingsLoader


BACKEND_ROOT = Path(__file__).resolve().parents[3]
settings: Settings = SettingsLoader.for_backend(BACKEND_ROOT).load()

__all__ = ["BACKEND_ROOT", "Settings", "SettingsLoader", "settings"]
