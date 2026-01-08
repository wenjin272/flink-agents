package org.apache.flink.agents.api.memory;

import org.apache.flink.agents.api.configuration.ConfigOption;

public class LongTermMemoryOptions {
    public enum LongTermMemoryBackend {
        EXTERNAL_VECTOR_STORE("external_vector_store");

        private final String value;

        LongTermMemoryBackend(String value) {
            this.value = value;
        }

        public String getValue() {
            return value;
        }
    }

    /** The backend for long-term memory. */
    public static final ConfigOption<LongTermMemoryBackend> BACKEND =
            new ConfigOption<>("long-term-memory.backend", LongTermMemoryBackend.class, null);

    /** The name of the vector store to server as the backend for long-term memory. */
    public static final ConfigOption<String> EXTERNAL_VECTOR_STORE_NAME =
            new ConfigOption<>("long-term-memory.external-vector-store-name", String.class, null);

    /** The name of the vector store to server as the backend for long-term memory. */
    public static final ConfigOption<Boolean> ASYNC_COMPACTION =
            new ConfigOption<>("long-term-memory.async-compaction", Boolean.class, null);
}
