# Versionierung

Royal Blackwater Fleet verwendet `MAJOR.MINOR.PATCH`. Die höchste zutreffende
Änderungsklasse bestimmt die nächste Version; niedrigere Stellen werden beim
Erhöhen zurückgesetzt.

| Klasse | Form | Verwenden für | Beispiel ab `1.0.0` |
| --- | --- | --- | --- |
| Patch | `x.y.Z` | Hotfixes, Fehler-, Sicherheits- und Dokumentationskorrekturen sowie kompatible interne Verbesserungen | `1.0.1` |
| Minor | `x.Y.0` | Rückwärtskompatible Features, neue optionale API-Felder und additive Funktionen oder Migrationen | `1.1.0` |
| Major | `X.0.0` | Inkompatible Verträge, Konfigurationen oder Migrationen sowie ausdrücklich große Produkterweiterungen | `2.0.0` |

Ein Feature mit zusätzlichem Patch-Anteil bleibt ein Minor-Release; eine
inkompatible Änderung bleibt ein Major-Release. Reine Größe allein macht eine
Änderung nicht inkompatibel, kann bei einer bewusst als Produktmeilenstein
geplanten Erweiterung aber einen Major-Sprung begründen.

Vor jedem Release:

1. Änderungsklasse anhand des gesamten Release-Inhalts bestimmen.
2. Nächste Nummer mit `bash .agents/scripts/next-version.sh patch|minor|major`
   prüfen.
3. `VERSION` sowie Maven-, Frontend- und API-Vertragsversion gemeinsam ändern;
   generierte Referenzen anschließend über ihren Generator aktualisieren.
4. Vollständiges Release-Gate ausführen, committen und erst aus diesem sauberen
   Commit das Artefakt bauen.

Aktivierte oder anderweitig veröffentlichte Release-Versionen und ihre
Artefakte sind unveränderlich und werden niemals wiederverwendet. Vorabstände
verwenden bei Bedarf SemVer-Suffixe wie `-rc.1`; Produktionsartefakte bleiben
bei der dreiteiligen Version aus `VERSION`.
