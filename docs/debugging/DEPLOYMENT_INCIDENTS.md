# Deployment-Incidents und bekannte Fehlerbilder

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

**Ursache:** Ein Deploy wurde als gewöhnliches Update behandelt, obwohl dieselbe
Versionsnummer erneut getestet werden soll.

**Lösung:** `./deploy.sh` und `./update.sh` rufen den Cleanup mit
`--replace-active --yes` auf. Nur der aktive Release und seine Metadaten werden
entfernt; `/opt/rbf/shared` bleibt bestehen. Niemals manuell `shared/.env` oder
`shared/data` löschen.

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

## 10. Cookie-Banner erscheint nicht

Wenn `GET /api/privacy/cookie-consent` 200 liefert, aber der Banner nicht erscheint,
liegt meist bereits das Consent-Cookie im Browser. In einem privaten Fenster oder
nach Löschen des site-spezifischen `rbf_cookie_consent` erneut laden. Keine
Produktions-Cookies per Ticket teilen.

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
