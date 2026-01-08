package org.apache.flink.agents.api.memory.compaction;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonTypeInfo;

import javax.annotation.Nullable;

import java.util.Objects;

public class SummarizationStrategy implements CompactionStrategy {
    private final String model;

    @JsonTypeInfo(
            use = JsonTypeInfo.Id.CLASS,
            include = JsonTypeInfo.As.PROPERTY,
            property = "@class")
    private final Object prompt;

    private final int limit;

    public SummarizationStrategy(String model, int limit) {
        this(model, null, limit);
    }

    @JsonCreator
    public SummarizationStrategy(
            @JsonProperty("model") String model,
            @Nullable @JsonProperty("prompt") Object prompt,
            @JsonProperty("limit") int limit) {
        this.model = model;
        this.prompt = prompt;
        this.limit = limit;
    }

    @Override
    public Type type() {
        return Type.SUMMARIZATION;
    }

    public String getModel() {
        return model;
    }

    public Object getPrompt() {
        return prompt;
    }

    public int getLimit() {
        return limit;
    }

    @Override
    public boolean equals(Object o) {
        if (o == null || getClass() != o.getClass()) return false;
        SummarizationStrategy that = (SummarizationStrategy) o;
        return limit == that.limit
                && Objects.equals(model, that.model)
                && Objects.equals(prompt, that.prompt);
    }

    @Override
    public int hashCode() {
        return Objects.hash(model, prompt, limit);
    }

    @Override
    public String toString() {
        return "SummarizationStrategy{"
                + "model='"
                + model
                + '\''
                + ", prompt="
                + prompt
                + ", limit="
                + limit
                + '}';
    }
}
