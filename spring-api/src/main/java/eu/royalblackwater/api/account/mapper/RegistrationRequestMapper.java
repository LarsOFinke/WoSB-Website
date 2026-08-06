package eu.royalblackwater.api.account.mapper;

import eu.royalblackwater.api.account.entity.RegistrationRequestEntity;
import eu.royalblackwater.api.dto.RegistrationRequestPublic;
import org.mapstruct.Mapper;

@Mapper
public interface RegistrationRequestMapper {
    RegistrationRequestPublic toPublic(RegistrationRequestEntity entity);
}
