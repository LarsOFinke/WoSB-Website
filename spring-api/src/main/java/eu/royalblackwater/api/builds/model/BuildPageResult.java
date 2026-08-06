package eu.royalblackwater.api.builds.model;

import java.util.List;

public record BuildPageResult(List<BuildAggregate> items, long total, long limit, long offset) { }
