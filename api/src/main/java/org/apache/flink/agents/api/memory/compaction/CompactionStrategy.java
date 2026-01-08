package org.apache.flink.agents.api.memory.compaction;

import com.fasterxml.jackson.annotation.JsonTypeInfo;

@JsonTypeInfo(use = JsonTypeInfo.Id.CLASS)
public interface CompactionStrategy {
    enum Type {
        SUMMARIZATION("summarization");

        private final String value;

        Type(String value) {
            this.value = value;
        }

        public String getValue() {
            return value;
        }
    }

    Type type();
}
