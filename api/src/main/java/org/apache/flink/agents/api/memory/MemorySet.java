package org.apache.flink.agents.api.memory;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;
import org.apache.flink.agents.api.memory.compaction.CompactionStrategy;

import javax.annotation.Nullable;

import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Objects;

public class MemorySet {
    private final String name;
    private final Class<?> itemType;
    private final int capacity;
    private final CompactionStrategy strategy;
    private @JsonIgnore BaseLongTermMemory ltm;

    @JsonCreator
    public MemorySet(
            @JsonProperty("name") String name,
            @JsonProperty("itemType") Class<?> itemType,
            @JsonProperty("capacity") int capacity,
            @JsonProperty("strategy") CompactionStrategy strategy) {
        this.name = name;
        this.itemType = itemType;
        this.capacity = capacity;
        this.strategy = strategy;
    }

    public long size() throws Exception {
        return this.ltm.size(this);
    }

    public List<String> add(
            List<?> memoryItems,
            @Nullable List<String> ids,
            @Nullable List<Map<String, Object>> metadatas)
            throws Exception {
        return this.ltm.add(this, memoryItems, ids, metadatas);
    }

    public List<MemorySetItem> get(@Nullable List<String> ids) throws Exception {
        return this.ltm.get(this, ids);
    }

    public List<MemorySetItem> search(
            String query, int limit, @Nullable Map<String, Object> extraArgs) throws Exception {
        return this.ltm.search(
                this, query, limit, extraArgs == null ? Collections.emptyMap() : extraArgs);
    }

    public void setLtm(BaseLongTermMemory ltm) {
        this.ltm = ltm;
    }

    public String getName() {
        return name;
    }

    public Class<?> getItemType() {
        return itemType;
    }

    public int getCapacity() {
        return capacity;
    }

    public CompactionStrategy getStrategy() {
        return strategy;
    }

    @Override
    public boolean equals(Object o) {
        if (o == null || getClass() != o.getClass()) return false;
        MemorySet memorySet = (MemorySet) o;
        return capacity == memorySet.capacity
                && Objects.equals(name, memorySet.name)
                && Objects.equals(itemType, memorySet.itemType)
                && Objects.equals(strategy, memorySet.strategy);
    }

    @Override
    public int hashCode() {
        return Objects.hash(name, itemType, capacity, strategy);
    }

    @Override
    public String toString() {
        return "MemorySet{"
                + "name='"
                + name
                + '\''
                + ", itemType="
                + itemType
                + ", capacity="
                + capacity
                + ", strategy="
                + strategy
                + '}';
    }
}
