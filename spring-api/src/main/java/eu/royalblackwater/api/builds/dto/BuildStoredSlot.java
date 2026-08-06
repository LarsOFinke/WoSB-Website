package eu.royalblackwater.api.builds.dto;

public record BuildStoredSlot(String type, int index, long optionId, String optionName, int quantity) { }
