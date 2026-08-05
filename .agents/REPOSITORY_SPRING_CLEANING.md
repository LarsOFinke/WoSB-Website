# How-to: Frühjahrsputz des Repositorys

Dieser Leitfaden organisiert einen breiten Qualitätsdurchgang mit wenig
Analysewiederholung. Er ist ein Arbeitsablauf, keine zweite technische
Spezifikation. Bei Widersprüchen gelten `AGENTS.md`,
`docs/development/QUALITY_STANDARDS.md` und die dort verlinkten Primärquellen.

## 1. Ziel und Grenzen festhalten

Ein Frühjahrsputz verbessert nachweisbar Wartbarkeit, Sicherheit,
Reproduzierbarkeit oder Betriebsstabilität, ohne Produktverhalten beiläufig zu
ändern. Vor dem ersten Edit festhalten:

- betroffene Qualitätsmerkmale und Teilbäume;
- messbare Symptome wie Duplikate, falsche Abhängigkeitsrichtung, unklare
  Zuständigkeit, ungebundene Listen, unzuverlässige CI oder veraltete Doku;
- ausdrücklich unverändertes Verhalten und externe Verträge;
- benötigte gezielte Tests und das abschließende Gate.

Keine kosmetische Großumsortierung, vorsorgliche Abstraktionsschicht oder
gleichzeitige fachliche Erweiterung als „Cleanup“ tarnen. Fremde Änderungen,
generierte Ausgaben, veröffentlichte Flyway-Migrationen und Historie bleiben
unangetastet.

## 2. Tokenarmer Einstieg

```bash
bash .agents/scripts/project-context.sh
sed -n '1,280p' .agents/PROJECT_CACHE.md
bash .agents/scripts/check-changes.sh
```

Danach nur die Primärquellen des tatsächlichen Scopes lesen:

| Scope | Primärquellen |
| --- | --- |
| Gesamtqualität | `AGENTS.md`, `docs/development/QUALITY_STANDARDS.md` |
| Backend/API | `docs/architecture/ARCHITECTURE.md`, `docs/reference/API.md`, `contracts/api-contract.json` |
| Frontend/CSS | `frontend/ARCHITECTURE.md`, `docs/reference/CSS_ARCHITECTURE.md` |
| Datenbank | `docs/development/DATABASE.md`, betroffene Migrationen und Upgrade-Tests |
| Infrastruktur | `infrastructure/ARCHITECTURE.md`, `docs/deployment/OPERATIONS.md` |
| CI und Gates | `docs/development/TESTING.md`, `Makefile`, `scripts/test.sh`, `.github/workflows/` |

Mit `rg` zuerst Aufrufer, Tests, Konfiguration und Dokumentation einer
Verantwortung finden. Keine breite Dateifür-Datei-Lektüre, wenn Cache und
Primärquelle den Einstieg bereits nennen.

## 3. Befunde priorisieren

Jeden Befund einer Priorität und einem Beweis zuordnen:

1. **P0 – Daten/Sicherheit:** Datenverlust, Authentifizierungs- oder
   Autorisierungsumgehung, Secret-/PII-Leak, unsicherer Restore oder Supply Chain.
2. **P1 – Korrektheit/Betrieb:** gebrochener Vertrag, Migration, Deployment,
   Rollback, reproduzierbarer Build oder verpflichtendes Gate.
3. **P2 – Wartbarkeit/Leistung:** vermischte Verantwortung, falsche
   Abhängigkeitsrichtung, N+1, ungebundene Liste, schwer testbare Kopplung.
4. **P3 – Ordnung:** Benennung, lokale Duplikate oder Ablage ohne unmittelbares
   Fehlerrisiko.

Nur belegte Befunde bearbeiten. Ein großer oder ungewöhnlicher Dateiumfang ist
ein Prüfsignal, aber allein noch kein Refactoring-Grund. P0/P1 zuerst in kleinen,
einzeln prüfbaren Änderungen schließen.

## 4. SOLID und KISS projektgerecht anwenden

SOLID ist hier eine Entscheidungshilfe, kein Klassenzähler:

- **Eine benennbare Verantwortung:** Transport bindet, Service entscheidet,
  Repository persistiert, Mapper übersetzt. Frontend-Seiten komponieren,
  Composables steuern Abläufe, API-Module transportieren, Domain-Module rechnen.
- **Erweiterung am stabilen Vertrag:** vorhandene Operation-Handler,
  Domain-Module und Infrastruktur-Helper erweitern, statt parallele
  Kompatibilitätspfade einzuführen.
- **Austauschbarkeit:** Vererbung nur bei tatsächlich substituierbaren Typen;
  meist sind kleine Komposition und Konstruktorinjektion klarer.
- **Schmale Schnittstellen:** nur die Daten und Operationen übergeben, die ein
  Verbraucher benötigt; keine generischen Manager-, Context- oder Utility-
  Sammelobjekte.
- **Abhängigkeiten nach innen:** Fachregeln kennen HTTP, Vue, Dateisystem oder
  konkrete Clients nur, wenn dies ihre echte Verantwortung ist.

KISS begrenzt die Umsetzung:

- zunächst die kleinste fachlich vollständige Ursache beheben;
- vorhandene Abstraktionen wiederverwenden;
- Extraktion nur bei klarerer Verantwortung, Lebensdauer oder Testbarkeit;
- zwei lesbare lokale Zeilen nicht durch ein allgemeines Framework ersetzen;
- tote Pfade erst nach Aufrufer-, Konfigurations-, Doku- und Migrationprüfung
  entfernen;
- Dateien um 300–400 Zeilen auf Trennstellen prüfen, die 420-Zeilen-Grenze aber
  nicht durch inhaltslose Wrapper umgehen.

## 5. API-, Sicherheits- und Datenschutzdurchgang

Für jede betroffene Operation vom Vertrag bis zur Persistenz verfolgen:

```text
api-contract -> generierter Controller -> Operation-Handler -> Service
             -> Repository/Mapper -> Migration/Index -> Tests/Dokumentation
```

Dabei prüfen:

- serverseitige Authentifizierung und Autorisierung, einschließlich Objekt- und
  Flottenbezug; Frontend-Guards zählen nicht als Sicherheitsgrenze;
- Session/JWT, CSRF, Host, Origin und CORS für mutierende Browserzugriffe;
- typisierte Eingabevalidierung, erlaubte Sortierfelder, parametrisierte Queries,
  begrenzte Pagination, Payloadgröße und Uploadtypen;
- Transaktionsgrenze einschließlich erforderlichem Audit-Eintrag;
- keine Lazy Loads außerhalb der Transaktion, N+1 oder ungebundene Collections;
- knappe 4xx-Fehler und zentrale 5xx-Diagnose ohne Payloads, Secrets, Tokens,
  vollständige IP-Adressen oder personenbezogene Inhalte;
- Zweck, Aufbewahrung sowie Export-, Berichtigungs- und Löschpfad für neue
  personenbezogene Daten;
- sparsame, nicht blockierende Webhooks und explizit erlaubter Outbound-Zugriff.

Schemaänderungen nur als neue kleine Flyway-Vorwärtsmigration umsetzen. Entity,
Index, leere Datenbank, unterstütztes Upgrade, Backup und Restore gemeinsam
prüfen; Hibernate bleibt auf `validate`.

## 6. CI/CD- und Supply-Chain-Durchgang

Workflows als ausführbaren Produktionsvertrag behandeln:

- Actions, Laufzeiten, Scanner und Testabhängigkeiten fest versionieren;
- jede verwendete Toolchain und Testabhängigkeit explizit installieren;
- Secrets nur über Secret-/Environment-Grenzen übergeben und leere optionale
  Secrets nicht als echte Zugangsdaten an Tools reichen;
- Cache ist Beschleunigung, nie Voraussetzung für Korrektheit;
- kompilierte JAR-/Frontend-Artefakte vor Image- oder Release-Build erzeugen und
  sicherstellen, dass `.dockerignore` sie nicht aus dem Build-Kontext entfernt;
- Release-Artefakte bleiben source-frei, inventarisiert, checksummiert und vor
  Installation fail-closed verifiziert;
- Container bleiben read-only, capability-dropped und ohne eingebettete Secrets;
- Migration, Backup, Readiness, Umschaltung und Rollback als einen Ablauf prüfen;
- keine Scanner- oder Testfehler mit `continue-on-error`, `failOnError=false` oder
  permissiven Fallbacks verdecken;
- Zeitlimits für dokumentierte Cold-Start-Pfade realistisch wählen, ohne Hänger
  unbegrenzt laufen zu lassen.

Spezifisch für OWASP/NVD: Ein leerer Cache umfasst mehrere hunderttausend
Datensätze. Ohne API-Key lokal nur Verbindung und korrekte Key-Behandlung
verifizieren; den vollständigen verpflichtenden Scan im GitHub-Workflow mit
Maven-Cache und möglichst `NVD_API_KEY` ausführen.
Das Setzen dieses GitHub-Secrets erfordert keinen Repository-Push: anschließend
den Security-Workflow per `gh workflow run security.yml` neu starten oder den
fehlgeschlagenen Lauf wiederholen.

Commits bilden kleine, geprüfte Aufräumschritte; Pushes bilden bewusst gebündelte
CI-Grenzen. Da jeder Push nach `main` den NVD-Dependency-Check anstößt, nicht jeden
lokalen Commit sofort pushen. Vor dem Push prüfen, ob der Stand als gemeinsame
CI-Einheit sinnvoll abgeschlossen ist und der externe Scan wirklich erneut
benötigt wird.

Für jeden reparierten CI-Vertrag eine kleine statische oder dynamische
Regressionprüfung ergänzen. Workflow-Syntax prüfen und den konkreten vormals
fehlgeschlagenen Befehl lokal reproduzieren, soweit die Umgebung es erlaubt.

## 7. Strukturieren ohne Großumbau

In dieser Reihenfolge arbeiten:

1. veraltete oder widersprüchliche Einstiege und Verträge korrigieren;
2. falsche Abhängigkeitsrichtungen an der kleinsten fachlichen Grenze beheben;
3. überladene Dateien entlang bestehender Verantwortungen teilen;
4. echte Duplikate nach Tests in die bereits zuständige Schicht ziehen;
5. Namen und Verzeichnisse nur ändern, wenn Navigation und Ownership klarer
   werden;
6. tote Dateien erst nach `rg`, Build-, Runtime-, Packaging- und Dokuprüfung
   entfernen;
7. Architektur-, Betriebs-, Test- und `.agents`-Navigation im selben Schritt
   aktualisieren.

Keine mechanische „Layer-Vervollständigung“: Ein Feature braucht nur die
Verzeichnisse und Typen, für die es reale Verantwortung gibt.

## 8. Änderungen in prüfbaren Pässen umsetzen

Pro Pass nur eine Ursache oder eng gekoppelte Invariante bearbeiten:

1. Ausgangsfehler mit kleinstem passenden Befehl reproduzieren.
2. Aufrufer, Test, Konfiguration und Doku lesen.
3. Ursache mit minimalem vollständigem Diff beheben.
4. Regressiontest ergänzen und fokussiert ausführen.
5. `bash .agents/scripts/check-changes.sh --run` verwenden.
6. Nach mehreren Pässen erst dann das Voll-Gate starten:

```bash
python3 -m pip install -r requirements-ci.txt
bash .agents/scripts/check-all.sh
```

Lang laufende Prozesse in derselben Session beenden lassen. Nicht eng pollen,
nicht wegen stiller Phasen neu starten und keine wiederholten Vollausgaben
anfordern. Erst Abschluss oder handlungsrelevanten Fehler auswerten.

Bei fehlender lokaler Toolchain, Docker-/Port-Sandbox oder externem Dienst den
Umgebungsblocker ausdrücklich vom Produktfehler trennen und nur den fehlenden
Teil in einer unterstützten Umgebung erneut ausführen.

## 9. Abschlusskriterien

Der Frühjahrsputz ist abgeschlossen, wenn:

- jeder umgesetzte Befund eine belegte Ursache und passende Regressionprüfung
  besitzt;
- Verhalten, Vertrag, Konfiguration, Migration und Dokumentation übereinstimmen;
- Sicherheits-, Datenschutz-, Performance- und Recovery-Folgen geprüft sind;
- gezielte Gates und `make validate` ohne versteckte Skips erfolgreich waren;
- generierte Dateien, lokale Umgebungen und fremde Änderungen unberührt bleiben;
- `git diff --check`, strikte Repository-Prüfung und Arbeitsbaumkontrolle sauber
  sind;
- verbleibende Befunde nach Priorität, Beleg und nächstem sicheren Schritt
  dokumentiert sind.

Commit oder Push gehören nicht zum Frühjahrsputz, solange sie nicht ausdrücklich
beauftragt wurden.
