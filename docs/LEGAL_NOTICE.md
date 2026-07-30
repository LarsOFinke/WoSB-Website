# Impressum / Anbieterkennzeichnung

## Zweck

Die öffentliche Route `/impressum` bereitet die Anwendung auf eine deutsche
Anbieterkennzeichnung vor. Sie kann als unveröffentlichter Entwurf betrieben werden und enthält
keine automatisch erfundenen Betreiberangaben.

## Datenquellen und Priorität

1. Beim erstmaligen Anlegen werden Werte aus `LEGAL_NOTICE_*` übernommen.
2. Solange keine Admin-Anpassung erfolgt ist, darf ein Neustart aktualisierte Umgebungswerte
   übernehmen.
3. Nach einer Bearbeitung im Staff-Panel ist die Datenbankfassung maßgeblich und bleibt bei Updates
   erhalten.
4. „Auf Umgebungswerte zurücksetzen“ verwirft die Adminfassung bewusst und übernimmt die beim
   Prozessstart geladenen Werte.

## Entwurfsmodus

`LEGAL_NOTICE_PUBLISHED=false` beziehungsweise ein deaktivierter Veröffentlichungsschalter zeigt
öffentlich nur einen neutralen Entwurfshinweis. Anbietername, Anschrift und Kontaktdaten des
Entwurfs werden nicht über die öffentliche API ausgeliefert.

Beim Veröffentlichen werden mindestens Anbietername, Straße, Postleitzahl, Ort, Land und E-Mail
validiert. Register-, Umsatzsteuer-, Aufsichts-, redaktionelle und
Streitbeilegungsangaben sind optional und müssen nur ausgefüllt werden, wenn sie für den Betreiber
tatsächlich zutreffen.

## Betrieb

Nach Migration `0013_legal_notice` ist kein Seed erforderlich. Die Seite ist öffentlich erreichbar;
der Editor und das Zurücksetzen auf Umgebungswerte sind ausschließlich Administratoren erlaubt.
Änderungen werden im Audit-Log erfasst.

## Rechtlicher Hinweis

Die bereitgestellten Felder sind eine technische Vorlage und keine Rechtsberatung. Die Pflicht zur
Anbieterkennzeichnung hängt nicht allein davon ab, ob Einnahmen erzielt werden. Vor der
Veröffentlichung sollten Inhalt, anwendbare Vorschriften und gegebenenfalls die Benennung einer
redaktionell verantwortlichen Person für das konkrete Angebot geprüft werden. Eine separate
Datenschutzerklärung bleibt erforderlich, sobald personenbezogene Daten verarbeitet werden.
