package eu.royalblackwater.api.account.mapper;

import eu.royalblackwater.api.dto.ProfilePreferenceOptionsRead;
import eu.royalblackwater.api.dto.ProfileRoleOptionRead;
import eu.royalblackwater.api.dto.ProfileShipOptionRead;
import eu.royalblackwater.api.persistence.RowValues;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Component;

@Component
public class ProfileDtoMapper {
    public ProfilePreferenceOptionsRead options(List<Map<String, Object>> shipRows,
                                                List<Map<String, Object>> roleRows) {
        List<ProfileShipOptionRead> ships = shipRows.stream()
                .map(row -> new ProfileShipOptionRead(
                        RowValues.longValue(row, "id"),
                        RowValues.string(row, "name"),
                        RowValues.longValue(row, "rate")))
                .toList();
        List<ProfileRoleOptionRead> roles = roleRows.stream()
                .map(row -> new ProfileRoleOptionRead(
                        RowValues.longValue(row, "id"),
                        RowValues.string(row, "code"),
                        RowValues.string(row, "label")))
                .toList();
        return new ProfilePreferenceOptionsRead(ships, roles);
    }
}
