package eu.royalblackwater.api.core.mapper;

import eu.royalblackwater.api.dto.HealthStatusRead;
import eu.royalblackwater.api.dto.HomeActivityWindowRead;
import eu.royalblackwater.api.dto.HomeModuleRead;
import eu.royalblackwater.api.dto.HomeRead;
import eu.royalblackwater.api.dto.HomeVoicePolicyRead;
import java.util.List;
import org.springframework.stereotype.Component;

@Component
public class CoreDtoMapper {
    public HealthStatusRead health(String status) {
        return new HealthStatusRead(status);
    }

    public HomeRead home() {
        return new HomeRead(
                "/home",
                "Royal Blackwater Fleet",
                "newcomer_onboarding_and_fleet_operations",
                new HomeActivityWindowRead("CET", "12:00-02:00", "18:00-23:00"),
                new HomeVoicePolicyRead("required", "optional_encouraged"),
                List.of(
                        module("builds"),
                        module("guides"),
                        module("forum"),
                        module("calendar"),
                        module("groups")));
    }

    private static HomeModuleRead module(String key) {
        return new HomeModuleRead(key, "available", "member");
    }
}
