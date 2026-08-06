package eu.royalblackwater.api.ships.filter;

import eu.royalblackwater.api.shared.filter.ListFilter;
import org.springframework.web.server.ResponseStatusException;

import static org.springframework.http.HttpStatus.BAD_REQUEST;

public record ShipListFilter(ListFilter page, Long rate, String shipType) {
    public static ShipListFilter from(String search, Long rate, String shipType, long limit, long offset) {
        Long normalizedRate = ListFilter.optionalPositiveLong(rate, "rate");
        if (normalizedRate != null && normalizedRate > 7) {
            throw new ResponseStatusException(BAD_REQUEST, "rate must be between 1 and 7.");
        }
        return new ShipListFilter(
                ListFilter.of(search, limit, offset, 250),
                normalizedRate,
                ListFilter.optionalText(shipType, "ship_type", 80));
    }

    public static ShipListFilter all() {
        return new ShipListFilter(new ListFilter(null, 250, 0), null, null);
    }
}
