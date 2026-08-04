package eu.royalblackwater.api.account;

import eu.royalblackwater.api.contract.RegistrationRequestPublic;
import org.mapstruct.Mapper;

@Mapper
public interface RegistrationRequestMapper {
    RegistrationRequestPublic toPublic(RegistrationRequestEntity entity);
}
