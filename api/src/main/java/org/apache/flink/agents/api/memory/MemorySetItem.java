package org.apache.flink.agents.api.memory;

import java.time.LocalDateTime;
import java.util.Map;

public class MemorySetItem {
    private final String memorySetName;
    private final String id;
    private final Object value;
    private final boolean compacted;
    private final Object createdTime;
    private final LocalDateTime lastAccessedTime;
    private final Map<String, Object> metadata;

    public MemorySetItem(
            String memorySetName,
            String id,
            Object value,
            boolean compacted,
            Object createdTime,
            LocalDateTime lastAccessedTime,
            Map<String, Object> metadata) {
        this.memorySetName = memorySetName;
        this.id = id;
        this.value = value;
        this.compacted = compacted;
        this.createdTime = createdTime;
        this.lastAccessedTime = lastAccessedTime;
        this.metadata = metadata;
    }

    public String getMemorySetName() {
        return memorySetName;
    }

    public String getId() {
        return id;
    }

    public Object getValue() {
        return value;
    }

    public boolean isCompacted() {
        return compacted;
    }

    public Object getCreatedTime() {
        return createdTime;
    }

    public LocalDateTime getLastAccessedTime() {
        return lastAccessedTime;
    }

    public Map<String, Object> getMetadata() {
        return metadata;
    }

    public static class DateTimeRange {
        private final LocalDateTime start;
        private final LocalDateTime end;

        public DateTimeRange(LocalDateTime start, LocalDateTime end) {
            this.start = start;
            this.end = end;
        }

        public LocalDateTime getStart() {
            return start;
        }

        public LocalDateTime getEnd() {
            return end;
        }
    }
}
