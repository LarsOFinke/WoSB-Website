package eu.royalblackwater.api.builds.model;

public record BuildSlotSelection(
        String type,
        int index,
        long optionId,
        String optionName,
        int quantity,
        BuildCatalogOption option) { }
