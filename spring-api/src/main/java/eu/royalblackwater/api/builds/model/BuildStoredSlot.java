package eu.royalblackwater.api.builds.model;

public record BuildStoredSlot(String type, int index, long optionId, String optionName, int quantity) { }
