# Deployment-Incidents und bekannte Fehlerbilder

Für die erste Eingrenzung vom Ursprung `./debug.sh` verwenden und Bereich,
Kategorie, Zeitraum sowie Zeilenlimit möglichst eng wählen. Die lokal redigierte
Datei unter `.diagnostics/` ist die bevorzugte Grundlage für Agentenanalyse;
Rohlogs vom Ziel weder dauerhaft sammeln noch ungeprüft weitergeben.

## 1. `Permission denied` bei Skripten

**Symptom:** `install-artifact.sh`, `stop.sh`, `install-systemd.sh` oder
`scripts/test.sh` lassen sich nach SCP oder einem Root-Build nicht ausführen.

**Ursache:** Ausführungsbits oder Eigentümer wurden beim Kopieren bzw. durch
`sudo ./deploy.sh` verändert.

**Diagnose und Behebung:**

```bash
find infrastructure/scripts -type f -name '*.sh' ! -perm -u+x -print
sudo chown -R root:root /opt/rbf/releases/<version>/infrastructure/scripts
sudo find /opt/rbf/releases/<version>/infrastructure/scripts -type f -name '*.sh' -exec chmod 0755 {} +
```

Der Origin-Build repariert generierte Verzeichnisse für den aufrufenden Benutzer;
Release-Pakete normalisieren die Skript-Rechte. Nicht den gesamten Installationsroot
pauschal auf `0777` setzen.

## 2. Falsches Artefakt trotz neuer Version

**Symptom:** Docker trägt `rbf-hub-api:1.0.1`, Spring Boot meldet aber `v1.0.0`.

**Ursache:** Im Maven-Target lagen mehrere JARs und das älteste bzw. ein
stales JAR wurde gepackt.

**Lösung:** `build-artifact.sh` löscht alte `rbf-api-*.jar` (außer `.original`)
und akzeptiert ausschließlich `rbf-api-${VERSION}.jar`. Danach neu bauen und
mit `./update.sh` übertragen; kein altes Archiv wiederverwenden.

## 3. Gleiche Version wird als immutable abgewiesen

**Symptom:** `Immutable release already exists and is active`.

**Ursache:** Die Versionsnummer wurde nach der Aktivierung erneut verwendet.
Aktivierte Releases sind unveränderlich; auch ein nachträglicher Hotfix oder eine
Dokumentationskorrektur benötigt deshalb eine neue Patch-Version.

**Lösung:** Die Änderung nach
[`VERSIONING.md`](../development/VERSIONING.md) klassifizieren, `VERSION` und die
gekoppelten Versionsquellen erhöhen und ein neues Artefakt bauen. Den aktiven
Release, seine Metadaten, `shared/.env` oder `shared/data` niemals manuell
löschen, um dieselbe Versionsnummer erneut zu verwenden.

## 4. NGINX startet in einer Restart-Schleife

**Symptom:** `could not open error log file` oder
`chown(/var/cache/nginx/client_temp) ... Operation not permitted`.

**Ursache:** Der Container lief nicht mit den Rechten, die das Standard-Image
für Cache-Verzeichnisse erwartet, während Root-Dateisysteme read-only gemountet
waren.

**Lösung:** Die Release-Konfiguration nutzt einen direkten NGINX-Start,
stderr-Logs und beschreibbare, passend besessene Runtime-Verzeichnisse. Nach
einer Änderung immer prüfen:

```bash
sudo docker compose --env-file /opt/rbf/shared/.env \
  -f /opt/rbf/current/infrastructure/compose.release.yml ps -a
sudo docker compose --env-file /opt/rbf/shared/.env \
  -f /opt/rbf/current/infrastructure/compose.release.yml logs --tail=200 gateway
```

## 5. systemd schlägt fehl und Logs scheinen verschwunden

**Symptom:** `rbf-hub.service` endet mit `status=2/INVALIDARGUMENT`; danach sind
API/Postgres-Container entfernt.

**Ursache:** Der Aktivierungsfehler wurde vor dem Compose-Cleanup nicht dauerhaft
gesichert oder ein Netzwerk blieb durch einen verwaisten Container belegt.

**Lösung:** Die aktuelle Aktivierung schreibt zuerst
`/opt/rbf/shared/deployments/failed-<version>-<timestamp>.log`. Erst diese Datei,
`journalctl` und `docker compose ps -a` sichern, dann gezielt bereinigen:

```bash
sudo docker ps -aq --filter label=com.docker.compose.project=rbf-hub | xargs -r sudo docker rm -f
sudo docker network ls --filter name=rbf-hub_ --format '{{.ID}}' | xargs -r sudo docker network rm
```

Danach erneut mit `./update.sh` deployen. `docker compose down` nicht als ersten
Diagnoseschritt verwenden.

## 6. PostgreSQL meldet „database system is shutting down“

**Symptom:** systemd beendet sich unmittelbar nach dem Start des Postgres-
Containers mit `psql ... FATAL: the database system is shutting down`.

**Ursache:** Ein einfacher Port-/Container-Check war positiv, bevor PostgreSQL
Verbindungen tatsächlich annahm.

**Lösung:** Der Readiness-Pfad wartet auf `pg_isready` und eine erfolgreiche
`psql -c 'select 1'`-Abfrage. Bei einem Einzeltest einige Sekunden warten und
anschließend den API-Readiness-Endpunkt prüfen.

## 7. Backup-Manifest verweist außerhalb des Release-Baums

**Symptom:** `Artifact is outside the infrastructure tree` für eine Datei unter
`/opt/rbf/shared/data/backups`.

**Ursache:** Der Manifest-Generator erwartete fälschlich, dass gemeinsam genutzte
Backups unter `/opt/rbf/<release>/infrastructure` liegen.

**Aktueller Betriebsentscheid:** Origin-Deployments verwenden vorübergehend
`--skip-backup`; der Backup-Runner bleibt für manuelle Tests verfügbar, bis die
Pfadmodellierung separat korrigiert und ein Restore erneut validiert wurde.

## 8. 401 bei Registrierung oder anonymen Endpunkten

**Symptom:** `POST /api/auth/register` oder Cookie-/Privacy-Endpunkte liefern 401;
NGINX zeigt den Request, der API-Log aber keinen passenden Security-Eintrag.

**Diagnose:**

```bash
sudo docker compose --env-file /opt/rbf/shared/.env \
  -f /opt/rbf/current/infrastructure/compose.release.yml logs --since=10m api gateway
```

Prüfe, dass das laufende JAR zur Release-Version passt. Die Security-Konfiguration
erlaubt die anonymen Methoden explizit und ignoriert CSRF nur für diese Routen;
401/403-Logs enthalten nur Methode, Pfad und boolesche Kontextmerkmale.

## 9. 401 trotz Session-Cookie auf geschützten Routen

**Symptom:** Eingeloggte Requests liefern 401; im API-Log steht zusätzlich
`LazyInitializationException` für `SiteRoleEntity` und danach ein 401 für
`/error`.

**Ursache:** Der Session-Filter erstellt die Spring-Authentifizierung nach dem
Ende des Repository-Aufrufs. Wird die Site-Rolle dabei nur als lazy Proxy
zurückgegeben, kann der Filter deren Berechtigungen nicht mehr laden. Der
geschützte Fehlerpfad verdeckt anschließend die eigentliche Ausnahme.

**Lösung:** Die Authentifizierungsabfrage muss Benutzer und Site-Rolle mit
einem expliziten Fetch-Join laden. `/error` bleibt öffentlich, damit Folgefehler
nicht als irreführender 401 erscheinen. Nach dem Deployment Browser-Session
beibehalten; ein erneuter Login ist nur nötig, wenn die Session abgelaufen ist.

## 10. Cookie-Einstellungen werden nicht automatisch eingeblendet

Das ist der erwartete Zustand, solange keine optionale Cookie- oder Tracking-
Integration aktiv ist. Eine fehlende gespeicherte Entscheidung und ein Fehler beim
Abruf der Entscheidung öffnen den Dialog nicht automatisch. Damit erzeugt die
reine Anzeige des Banners nicht erst selbst ein Consent-Cookie. Die Einstellungen
bleiben über den Footer und das Datenschutzcenter erreichbar. Keine Produktions-
Cookies per Ticket teilen.

## 11. Versionen stimmen nicht überein

`VERSION`, `spring-api/pom.xml` sowie Frontend `package.json` und Lockfile müssen
denselben Stand tragen. `scripts/check_repository.py --strict-tree` und der
Origin-Build brechen bei Abweichungen absichtlich ab.

## 12. Erststart scheitert während eines Monitoring-Image-Pulls

**Symptom:** API und PostgreSQL sind bereit, aber der Release-Start endet während
des Downloads von `louislam/uptime-kuma` mit einem fehlgeschlagenen Healthcheck.

**Ursache:** Der optionale Monitoring-Stack blockierte den kritischen systemd-
Startpfad und konnte das Aktivierungszeitfenster überschreiten.

**Aktueller Stand:** Uptime Kuma und sein separates Gateway sind aus dem
Produktions-Compose, Setup, Backup-Restore und Frontend entfernt. Ein neuer
Deploy startet nur PostgreSQL, Spring Boot und das Haupt-Gateway. Verwaiste
Monitoring-Container werden durch `--remove-orphans` beim nächsten Start entfernt.

## 12. `current` ist kein Symlink

**Symptom:** `Current installation entry is not a symbolic link.`

**Ursache:** Ein früherer, abgebrochener Setup-Lauf hat ein echtes
`/opt/rbf/current`-Verzeichnis hinterlassen.

**Lösung:** Der Origin-Deploy ruft den Cleanup nun mit
`--replace-active --yes` auf. Ein solcher Eintrag wird nur entfernt, wenn darin
`infrastructure/compose.release.yml` liegt; `/opt/rbf/shared` bleibt unangetastet.
Unbekannte oder unsichere Einträge werden weiterhin fail-closed abgewiesen.

## 13. HTTP 500 bei Kalender- oder Staff-Datumsfiltern

**Symptom:** Kalender, Staff-Übersicht oder die Datumsfilter für Registrierungen,
Audit-Logs und Security-Dashboard liefern HTTP 500. Im API-Log steht
`MethodArgumentTypeMismatchException` für `LocalDate` oder `LocalDateTime`.

**Ursache:** Browser senden vertragskonforme ISO-Werte (`YYYY-MM-DD` beziehungsweise
UTC-Zeitpunkte mit `Z`), während die generierten Spring-Controller zuvor den
localeabhängigen Standardkonverter verwendeten. Der globale Fehlerhandler stufte
den erwartbaren Bindungsfehler außerdem als unerwarteten Serverfehler ein.

**Lösung:** Der Routengenerator versieht `date`- und `date-time`-Queryparameter
mit explizitem ISO-Format. Ungültige Parameter liefern eine begrenzte HTTP-400-
Antwort. Generierte Controller nicht direkt korrigieren; stets
`scripts/migration/generate_spring_routes.py` ändern und neu generieren.

## 14. HTTP 500 bei Master-Data-Kategorien

**Symptom:** `/api/admin/master-data/categories` liefert HTTP 500; im API-Log
steht `UnrecognizedPropertyException` für `seed_checksum`.

**Ursache:** Die Datenbankabfrage enthält interne Seed-Metadaten, die bewusst
nicht Teil des öffentlichen Read-Contracts sind. Die strikte Contract-
Konvertierung weist unbekannte Eigenschaften korrekt zurück.

**Lösung:** Interne Seed-Prüfsummen, relationale IDs und Hilfsspalten werden am
Master-Data-Mapping-Rand entfernt, bevor Kategorien, Optionen oder Schiffe in
API-Contracts konvertiert werden. Den Contract nicht um interne Datenbankfelder
erweitern und Jackson nicht global auf das Ignorieren unbekannter Felder
umstellen.

## 15. HTTP 500 im Security-Dashboard

**Symptom:** `/api/admin/logs/security-dashboard` liefert HTTP 500; im API-Log
steht `ClassCastException: java.sql.Date cannot be cast to java.time.LocalDate`.

**Ursache:** PostgreSQL-DATE-Werte kommen über JDBC als `java.sql.Date`, während
der Service sie direkt zu `LocalDate` castete.

**Lösung:** Datumstypen am gemeinsamen Persistence-Rand über `RowValues.date`
normalisieren. Der Regressionstest verwendet ausdrücklich `java.sql.Date`, damit
ein reiner Mock mit bereits konvertiertem `LocalDate` den Fehler nicht verdeckt.

## 16. NGINX kann den Maintenance-Marker nicht prüfen

**Symptom:** Gateway-Logs enthalten bei Requests `stat() ... maintenance-mode.json
failed (13: Permission denied)`.

**Ursache:** Der nicht privilegierte Gateway-Prozess mit UID 101 konnte das auf
Gruppe 10001 begrenzte Control-Verzeichnis nicht durchlaufen.

**Lösung:** Der Gateway erhält in beiden Compose-Dateien ausschließlich die
zusätzliche numerische Runtime-Gruppe 10001. Status bleibt read-only gemountet;
die Verzeichnisrechte werden nicht global geöffnet.
