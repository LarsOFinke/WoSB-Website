package eu.royalblackwater.api.shared.mapper;

import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Component;
import tools.jackson.databind.JavaType;
import tools.jackson.databind.ObjectMapper;

@Component
public class ContractConversionService {
    private final ObjectMapper mapper;

    public ContractConversionService(ObjectMapper mapper) {
        this.mapper = mapper;
    }

    public <T> T convert(Object source, Class<T> target) {
        return mapper.convertValue(source, target);
    }

    public <T> List<T> convertList(List<Map<String, Object>> source, Class<T> target) {
        JavaType type = mapper.getTypeFactory().constructCollectionType(List.class, target);
        return mapper.convertValue(source, type);
    }
}
