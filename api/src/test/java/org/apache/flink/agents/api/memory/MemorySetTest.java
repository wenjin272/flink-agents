package org.apache.flink.agents.api.memory;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.flink.agents.api.chat.messages.ChatMessage;
import org.apache.flink.agents.api.memory.compaction.SummarizationStrategy;
import org.apache.flink.agents.api.prompt.Prompt;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;

public class MemorySetTest {
    @Test
    public void testJsonSerialization() throws Exception {
        ObjectMapper mapper = new ObjectMapper();
        MemorySet memorySet =
                new MemorySet(
                        "test",
                        ChatMessage.class,
                        100,
                        new SummarizationStrategy(
                                "testModel", Prompt.fromText("Test prompt"), 100));
        String jsonValue = mapper.writeValueAsString(memorySet);

        MemorySet deserialized = mapper.readValue(jsonValue, MemorySet.class);
        Assertions.assertEquals(memorySet, deserialized);
    }
}
