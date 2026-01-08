package org.apache.flink.agents.runtime.memory;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.flink.agents.api.context.RunnerContext;
import org.apache.flink.agents.api.memory.BaseLongTermMemory;
import org.apache.flink.agents.api.memory.LongTermMemoryOptions;
import org.apache.flink.agents.api.memory.MemorySet;
import org.apache.flink.agents.api.memory.MemorySetItem;
import org.apache.flink.agents.api.memory.compaction.CompactionStrategy;
import org.apache.flink.agents.api.resource.ResourceType;
import org.apache.flink.agents.api.vectorstores.BaseVectorStore;
import org.apache.flink.agents.api.vectorstores.CollectionManageableVectorStore;
import org.apache.flink.agents.api.vectorstores.CollectionManageableVectorStore.Collection;
import org.apache.flink.agents.api.vectorstores.Document;
import org.apache.flink.agents.api.vectorstores.VectorStoreQuery;
import org.apache.flink.agents.api.vectorstores.VectorStoreQueryResult;

import javax.annotation.Nullable;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

public class VectorStoreLongTermMemory implements BaseLongTermMemory {
    public static final ObjectMapper mapper = new ObjectMapper();
    public static final DateTimeFormatter formatter = DateTimeFormatter.ISO_DATE_TIME;

    private final RunnerContext ctx;
    private final String jobId;
    private final String key;
    private final boolean asyncCompaction;
    private Object vectorStore;

    public VectorStoreLongTermMemory(
            RunnerContext ctx, Object vectorStore, String jobId, String key) {
        this.ctx = ctx;
        this.vectorStore = vectorStore;
        this.jobId = jobId;
        this.key = key;
        this.asyncCompaction = ctx.getConfig().get(LongTermMemoryOptions.ASYNC_COMPACTION);
    }

    private BaseVectorStore store() throws Exception {
        if (vectorStore instanceof String) {
            vectorStore = ctx.getResource((String) vectorStore, ResourceType.VECTOR_STORE);
        }
        return (BaseVectorStore) vectorStore;
    }

    @Override
    public MemorySet getOrCreateMemorySet(
            String name, Class<?> itemType, int capacity, CompactionStrategy strategy)
            throws Exception {
        MemorySet memorySet = new MemorySet(name, itemType, capacity, strategy);
        ((CollectionManageableVectorStore) this.store())
                .getOrCreateCollection(
                        this.nameMangling(name),
                        Map.of("memory_set", mapper.writeValueAsString(memorySet)));
        memorySet.setLtm(this);
        return memorySet;
    }

    @Override
    public MemorySet getMemorySet(String name) throws Exception {
        Collection collection =
                ((CollectionManageableVectorStore) this.store())
                        .getCollection(this.nameMangling(name));
        MemorySet memorySet =
                mapper.readValue(
                        (String) collection.getMetadata().get("memory_set"), MemorySet.class);
        memorySet.setLtm(this);
        return memorySet;
    }

    @Override
    public boolean deleteMemorySet(String name) throws Exception {
        Collection collection =
                ((CollectionManageableVectorStore) this.store())
                        .deleteCollection(this.nameMangling(name));
        return collection != null;
    }

    @Override
    public long size(MemorySet memorySet) throws Exception {
        return this.store().size(this.nameMangling(memorySet.getName()));
    }

    @Override
    public List<String> add(
            MemorySet memorySet,
            List<Object> memoryItems,
            @Nullable List<String> ids,
            @Nullable List<Map<String, Object>> metadatas)
            throws Exception {
        if (ids == null || ids.isEmpty()) {
            ids = new ArrayList<>();
            for (int i = 0; i < memoryItems.size(); i++) {
                ids.add(UUID.randomUUID().toString());
            }
        }

        String timestamp = LocalDateTime.now().format(formatter);
        Map<String, Object> metadata =
                Map.of(
                        "compacted",
                        false,
                        "created_time",
                        timestamp,
                        "last_accessed_time",
                        timestamp);

        List<Map<String, Object>> mergedMetadatas = new ArrayList<>();
        for (int i = 0; i < memoryItems.size(); i++) {
            mergedMetadatas.add(new HashMap<>(metadata));
        }

        if (metadatas != null && !metadatas.isEmpty()) {
            for (int i = 0; i < memoryItems.size(); i++) {
                mergedMetadatas.get(i).putAll(metadatas.get(i));
            }
        }

        List<Document> documents = new ArrayList<>();
        for (int i = 0; i < memoryItems.size(); i++) {
            documents.add(
                    new Document(
                            mapper.writeValueAsString(memoryItems.get(i)),
                            mergedMetadatas.get(i),
                            ids.get(i)));
        }

        List<String> itemIds =
                this.store().add(documents, this.nameMangling(memorySet.getName()), null);

        // TODO: compaction
        return ids;
    }

    @Override
    public List<MemorySetItem> get(MemorySet memorySet, @Nullable List<String> ids)
            throws Exception {
        List<Document> documents =
                this.store().get(ids, this.nameMangling(memorySet.getName()), null);
        return this.convertToItems(memorySet, documents);
    }

    @Override
    public void delete(MemorySet memorySet, @Nullable List<String> ids) throws Exception {
        this.store().delete(ids, this.nameMangling(memorySet.getName()), null);
    }

    @Override
    public List<MemorySetItem> search(
            MemorySet memorySet, String query, int limit, Map<String, Object> extraArgs)
            throws Exception {
        VectorStoreQuery vectorStoreQuery =
                new VectorStoreQuery(
                        query, limit, this.nameMangling(memorySet.getName()), extraArgs);
        VectorStoreQueryResult result = this.store().query(vectorStoreQuery);
        return this.convertToItems(memorySet, result.getDocuments());
    }

    private String nameMangling(String name) {
        return String.join("-", this.jobId, this.key, name);
    }

    private List<MemorySetItem> convertToItems(MemorySet memorySet, List<Document> documents)
            throws JsonProcessingException {
        List<MemorySetItem> items = new ArrayList<>();
        for (Document doc : documents) {
            Map<String, Object> metadata = doc.getMetadata();
            boolean compacted = (boolean) metadata.remove("compacted");
            Object createdTime;
            if (compacted) {
                createdTime =
                        new MemorySetItem.DateTimeRange(
                                LocalDateTime.parse(
                                        (String) metadata.remove("created_time_start"), formatter),
                                LocalDateTime.parse(
                                        (String) metadata.remove("created_time_end"), formatter));
            } else {
                createdTime =
                        LocalDateTime.parse((String) metadata.remove("created_time"), formatter);
            }
            MemorySetItem item =
                    new MemorySetItem(
                            memorySet.getName(),
                            doc.getId(),
                            memorySet.getItemType() == String.class
                                    ? doc.getContent()
                                    : mapper.readValue(doc.getContent(), memorySet.getItemType()),
                            compacted,
                            createdTime,
                            LocalDateTime.parse(
                                    (String) metadata.remove("last_accessed_time"), formatter),
                            metadata);
            items.add(item);
        }
        return items;
    }

    private void compact(MemorySet memorySet) {
        CompactionStrategy strategy = memorySet.getStrategy();
        if (strategy.type() == CompactionStrategy.Type.SUMMARIZATION) {

        } else {
            throw new RuntimeException(
                    String.format("Unknown compaction strategy: %s", strategy.type()));
        }
    }
}
