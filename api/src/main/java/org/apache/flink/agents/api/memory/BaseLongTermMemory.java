package org.apache.flink.agents.api.memory;

import org.apache.flink.agents.api.memory.compaction.CompactionStrategy;

import javax.annotation.Nullable;

import java.util.List;
import java.util.Map;

public interface BaseLongTermMemory {

    MemorySet getOrCreateMemorySet(
            String name, Class<?> itemType, int capacity, CompactionStrategy strategy)
            throws Exception;

    MemorySet getMemorySet(String name) throws Exception;

    boolean deleteMemorySet(String name) throws Exception;

    long size(MemorySet memorySet) throws Exception;

    List<String> add(
            MemorySet memorySet,
            List<Object> memoryItems,
            @Nullable List<String> ids,
            @Nullable List<Map<String, Object>> metadatas)
            throws Exception;

    List<MemorySetItem> get(MemorySet memorySet, @Nullable List<String> ids) throws Exception;

    void delete(MemorySet memorySet, @Nullable List<String> ids) throws Exception;

    List<MemorySetItem> search(
            MemorySet memorySet, String query, int limit, Map<String, Object> extraArgs)
            throws Exception;
}
