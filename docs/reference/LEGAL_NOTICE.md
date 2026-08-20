# Legal Notice / Provider Identification

## Purpose

The public `/impressum` route prepares the application for German provider-identification
requirements. It can operate as an unpublished draft and does not invent operator details
automatically.

## Data Sources and Priority

1. On initial creation, values are taken from `LEGAL_NOTICE_*`.
2. As long as no admin customization has been made, a restart may adopt updated environment values.
3. After editing in the staff panel, the database version is authoritative and persists across updates.
4. “Reset to environment values” intentionally discards the admin version and adopts the values that
   can currently be read from the configured env file and process environment. With Docker Compose,
   changes to the host `.env` require the API container to be restarted or recreated first.

## Draft Mode

`LEGAL_NOTICE_PUBLISHED=false`, or a disabled publication toggle, exposes only a neutral draft notice
publicly. Provider name, address, and contact details from the draft are not returned through the
public API.

Publishing validates at least the provider name, street, postal code, city, country, and email
address. Registration, VAT, supervisory, editorial, and dispute-resolution details are optional and
must only be filled in when they actually apply to the operator.

## Public Repository Reference

Administrators can optionally maintain an HTTPS link to the project's public source repository.
When configured, the published Impressum presents it in a dedicated transparency section so
visitors can inspect the code and change history, report issues, and find the contribution path.
This gives a community-run project a verifiable continuity signal without implying that a company
operates or guarantees it. The value is stored with the other Impressum fields and participates in
the same audit, persistence, and “Reset to environment values” workflow through
`LEGAL_NOTICE_PUBLIC_REPOSITORY_URL`.

## Operations

No seed is required. Migration `V11__legal_notice_public_repository.sql` adds the optional
repository reference without modifying existing legal-notice content. The page is publicly accessible; editing
and resetting to environment values are restricted to administrators. Changes are recorded in the
audit log.

## Legal Note

The provided fields are a technical template and do not constitute legal advice. Provider-identification
obligations do not depend solely on whether revenue is generated. Before publication, the content,
applicable requirements, and, where relevant, designation of a person responsible for editorial
content should be reviewed for the specific offering. A separate privacy notice remains necessary
whenever personal data is processed.
