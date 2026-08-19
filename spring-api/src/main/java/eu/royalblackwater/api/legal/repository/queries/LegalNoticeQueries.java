package eu.royalblackwater.api.legal.repository.queries;

/** SQL statements owned by the LegalNoticeService persistence boundary. */
public final class LegalNoticeQueries {
    private LegalNoticeQueries() { }

    public static final String ENSURE_ENVIRONMENT_ROW_INSERT_01 = """
                insert into legal_notices(
                    id,published,is_customized,provider_name,legal_form,represented_by,street,postal_code,
                    city,country,email,phone,register_name,register_court,register_number,vat_id,business_id,
                    supervisory_authority,editorial_responsible_name,editorial_responsible_street,
                    editorial_responsible_postal_code,editorial_responsible_city,editorial_responsible_country,
                    dispute_resolution_text,additional_information,public_repository_url,
                    updated_by_username,updated_at)
                values(1,:published,:customized,:providerName,:legalForm,:representedBy,:street,:postalCode,
                    :city,:country,:email,:phone,:registerName,:registerCourt,:registerNumber,:vatId,:businessId,
                    :supervisoryAuthority,:editorialResponsibleName,:editorialResponsibleStreet,
                    :editorialResponsiblePostalCode,:editorialResponsibleCity,:editorialResponsibleCountry,
                    :disputeResolutionText,:additionalInformation,:publicRepositoryUrl,:updatedBy,:updatedAt)
                on conflict(id) do nothing
                """;

    public static final String ROW_SELECT_01 = "select * from legal_notices where id=:id";

    public static final String UPDATE_SQL_UPDATE_01 = """
                update legal_notices set published=:published,is_customized=:customized,
                    provider_name=:providerName,legal_form=:legalForm,represented_by=:representedBy,
                    street=:street,postal_code=:postalCode,city=:city,country=:country,email=:email,phone=:phone,
                    register_name=:registerName,register_court=:registerCourt,register_number=:registerNumber,
                    vat_id=:vatId,business_id=:businessId,supervisory_authority=:supervisoryAuthority,
                    editorial_responsible_name=:editorialResponsibleName,
                    editorial_responsible_street=:editorialResponsibleStreet,
                    editorial_responsible_postal_code=:editorialResponsiblePostalCode,
                    editorial_responsible_city=:editorialResponsibleCity,
                    editorial_responsible_country=:editorialResponsibleCountry,
                    dispute_resolution_text=:disputeResolutionText,additional_information=:additionalInformation,
                    public_repository_url=:publicRepositoryUrl,
                    updated_by_username=:updatedBy,updated_at=:updatedAt where id=:id
                """;

}
