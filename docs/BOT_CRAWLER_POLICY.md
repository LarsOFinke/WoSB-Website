# Bot and crawler load policy

The gateway uses several layers to protect the Raspberry Pi from unnecessary crawler traffic:

- `frontend/public/robots.txt` excludes API, administration, profile, calendar, squad and group workspaces.
- known resource-intensive AI training crawlers are disallowed in `robots.txt` and rejected by NGINX based on their declared user agent.
- public SPA requests and general API requests have independent per-IP request and connection limits.
- API responses and authenticated workspaces receive `X-Robots-Tag: noindex, nofollow, noarchive`.
- immutable frontend assets keep long cache lifetimes so repeat requests do not rebuild application state.
- access logs remain disabled to avoid writing crawler noise to storage.

`robots.txt` is voluntary. The NGINX controls are the actual load-protection boundary. User-agent blocking is intentionally limited to declared high-volume training crawlers; normal browsers and conventional search-engine crawlers remain subject to rate limits instead of blanket denial.
