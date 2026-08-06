package eu.royalblackwater.api.ships.filter;

import eu.royalblackwater.api.shared.filter.ListFilter;
import java.util.Map;

public record ShipListFilter(ListFilter page, Long rate, String shipType) {
    public static ShipListFilter from(Map<String, Object> parameters) {
        Long rate = ListFilter.optionalPositiveLong(parameters, "rate");
        if (rate != null && rate > 7) {
            throw new org.springframework.web.server.ResponseStatusException(
                    org.springframework.http.HttpStatus.BAD_REQUEST, "rate must be between 1 and 7.");
        }
        return new ShipListFilter(
                ListFilter.from(parameters, 100, 250), rate,
                ListFilter.optionalText(parameters, "ship_type", 80));
    }

    public static ShipListFilter all() {
        return new ShipListFilter(new ListFilter(null, 250, 0), null, null);
    }
}
