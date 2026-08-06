package eu.royalblackwater.api.builds.dto;

import java.util.List;

public record BuildPageResult(List<BuildAggregate> items, long total, long limit, long offset) { }
