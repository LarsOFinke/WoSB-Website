# Backend-Architektur

## Abhängigkeitsrichtung

`routes -> application services -> domain models/repositories -> database`

Die FastAPI-Routen bleiben absichtlich funktionsbasiert und dünn. Zustandsbehaftete oder
mehrstufige Use-Cases liegen in Services. Reine Regeln werden als kleine Policies,
Validatoren, Mapper oder Value-Parser modelliert. OOP wird eingesetzt, wenn dadurch
Abhängigkeiten injizierbar oder Verantwortlichkeiten klarer werden; einfache, reine
Funktionen bleiben Funktionen.

## Konfiguration

`app.configuration.SettingsLoader` ist der Composition Root. Er verbindet
`EnvironmentSource`, `IniConfigSource` und die fachlichen Reader zu einem unveränderlichen
`Settings`-Aggregat. `app.core.config.settings` ist nur die kompatible globale Instanz.

## Große Use-Cases

- Stammdaten: getrennte Category-, Option- und Ship-Services mit Mapper und Unit-of-Work
- Build-Validierung: Optionskatalog, Upgrade-Zugriff, Waffenvalidator, Slot-Factory und
  koordinierender `BuildValidator`
- Squads: Repository, Zugriffspolitik, Mapper und `SquadService`
- Webhooks: Envelope-Factory, Encoder, Signer, Transport und Delivery-Service
- Security-Dashboard: separater Threat-Scorer und koordinierender Service

Kompatibilitätsfassaden behalten bestehende Funktionsimporte für Router, Tests und andere
Module bei. Neue Logik sollte direkt gegen die Klassen getestet werden.
