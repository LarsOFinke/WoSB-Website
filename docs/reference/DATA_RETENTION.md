# Data Retention and Deletion Concept

This document describes the default retention policy. The retention periods for cookie consent decisions as well as
resolved privacy requests and contacts are technically enforced by the application.
The remaining table rows are binding target retention periods for the respective operational processes.
Any differing statutory
or contractual requirements must be reviewed by the controller before production use
and configured through the Spring configuration and infrastructure environment file.

| Data class | Default | Purpose | Deletion |
|---|---:|---|---|
| Aggregated IP blocking signals | 7 calendar days | Solely for deciding on a specific IP block | daily maintenance run; immediately when blocked |
| Expired/revoked IP blocks | 90 days | Limited traceability of access control | daily maintenance run |
| Audit history | 365 days | Traceability of administrative changes | daily maintenance run |
| Discord webhook deliveries | 30 days | Delivery errors, retries, and support | daily maintenance run |
| Cookie consent decisions | 400 days | Evidence and restoration of the selection | daily maintenance run |
| Resolved privacy requests | 400 days | Evidence of export, rectification, and deletion handling | daily maintenance run; open requests are retained |
| Resolved privacy contacts | 400 days | Follow-up questions and evidence of handling | daily maintenance run; open messages are retained until handled |
| Open registration requests | 30 days | Account review | daily maintenance run |
| Reviewed registration requests | 90 days | Traceability of the decision | daily maintenance run |
| Expired sessions | until expiration | Authentication and security | daily maintenance run |
| Strategy plans and optional player labels | until owner deletion or manual deletion | Tactical planning, sharing and print preparation | owner deletion removes the strategy document; manual deletion is immediate |
| Warehouse entries and holder labels | until administrator deletion | Fleet stock allocation and logistics | immediate administrator deletion; linked accounts follow profile correction and account pseudonymization |

Password hashes in registration requests are overwritten immediately after approval or rejection.
Approved accounts retain only the hash in the actual user account.

## Purpose-Limited IP Blocking Signals

The application performs **no general request or visitor logging** in the database.
Only the following broad event categories are stored when they are relevant to an IP-blocking decision:

- suspicious scan/reconnaissance attempts,
- failed logins,
- rate-limit hits.

Events are aggregated at **daily granularity** when written. For each IP,
signal category, reason, safe target, and UTC day there is at most one record containing:

- a normalized individual IP address,
- the UTC calendar day,
- one of the broad signal categories listed above,
- a fixed reason such as rejected login, exceeded rate limit, or suspicious scan,
- for known API endpoints, the normalized Spring route template without concrete object IDs, or for
  scans a fixed target category such as “Git metadata” or “environment file”,
- the daily signal count.

Free-form or unassigned request paths, query strings, user agents,
referrers, request IDs, HTTP methods,
request/response content, status details, runtime, account name, exact request timestamp, exceptions,
or stack traces are not stored. The admin page exposes only these aggregations per IP and day,
including the reason and safe route/scan target.
Individual events or raw logs exist neither in the database nor through an API.

When an IP is blocked, its temporary blocking signals are deleted immediately in the same database
transaction. The active block retains the exact IP only as long as it is required for access control.
Expired or revoked blocks are deleted after the limited history period.
Audit text does not contain a copy of the IP address.

## Infrastructure Logs

The production NGINX gateway does not write access logs. In particular, routes, IP addresses, and
user agents are therefore not recorded there as normal visitor logs. The backend also does not keep
persistent request telemetry. For errors and security rejections, ephemeral operational logging may
contain a server-generated request ID, HTTP method, normalized Spring route template, status/error
class, and bounded exception context.
Client IPs, query values, user agents, cookies, and request/response payloads remain excluded.

Successful request lifecycle telemetry is disabled by default.
`RBF_HTTP_LIFECYCLE_LOGGING=true` may be enabled for automated tests or short, targeted diagnostic
windows and logs only request ID, method, normalized route, status, and duration. These logs are not
stored in the application database and are not exposed through the staff API.

## Configuration

```yaml
rbf:
  privacy:
    cookie-consent-retention: 400d
    resolved-request-retention: 400d
    retention-interval: PT24H
```

In production, these values are set through `COOKIE_CONSENT_RETENTION`,
`RESOLVED_PRIVACY_REQUEST_RETENTION`, and `PRIVACY_RETENTION_INTERVAL`. Spring `Duration` values
apply, for example `400d` or `PT24H`; all retention periods must be positive. The privacy maintenance
run starts once after successful application initialization and then at the configured interval.
`RBF_SCHEDULING_ENABLED=false` disables both executions, for example for isolated integration tests.

Shorter retention is generally preferable. Extending a period requires a documented purpose,
a legal basis, and a date for renewed review. Changes take effect during the next privacy maintenance
run; before a significant reduction, a controlled backup is advisable.

## Content Not Deleted Automatically

Forum posts, guides, builds, and other published domain content can affect references and legitimate
interests of other community members. After confirmed account deletion, such content therefore
remains under a neutral identity that can no longer log in.
Profile data, preferences, sessions, fleet and group memberships, and votes are removed; nullable
creator references are detached.

Strategy plans are handled differently because their optional free-text labels may identify planned
participants and their tactical value is tied to the planner who created them. Account deletion removes
owned strategy documents and disables strategy-only background publication. Strategy owners can delete
individual plans at any time. Plans are private by default; explicit publication exposes the plan to
anyone holding its non-sequential public link until publication is revoked.

Warehouse entries are operational fleet records. Prefer linking an active fleet member: the UI then
uses the account's current display name, profile corrections are reflected automatically, and the
entry is included in that account's personal-data export. Account deletion pseudonymizes the linked
identity. A custom holder label is available for external or shared holdings, should use an operational
alias instead of unnecessary personal data, and must be corrected or deleted manually when a verified
data-subject request identifies it. Warehouse events send only the bounded audit summary to explicitly
subscribed Discord webhooks; webhook URLs and delivery credentials remain server-side.

## Data Subject Workflow

A machine-readable JSON export is available in the profile. It contains account and profile data,
consents, memberships, and self-created content, but no password, session, or consent keys and no
data belonging to other users.

Profile data that can be changed directly is corrected through the profile editor without a request.
A formal rectification request can be submitted for data that cannot be changed directly. Deletion
requests require the username to be entered again and are executed only after an administrative
identity and impact review. Bootstrap administrators are excluded from account deletion for
operational-continuity reasons.

Admins handle open cases under `/admin/privacy-requests`. The decision, handler, timestamp, and
reason are stored with the request and additionally recorded in the audit log.

The public `/privacy` route provides cookie settings, an understandable overview of processing, and
a data-minimizing contact form. The form stores neither an IP address nor a user agent. Email address
and message content remain inside the application and are not sent through Discord webhooks;
administrators handle them in the privacy inbox.
