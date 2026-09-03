/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied. See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */
package org.apache.flink.agents.runtime.python.utils;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.flink.agents.api.annotation.Tool;
import org.apache.flink.agents.api.annotation.ToolParam;
import org.apache.flink.agents.api.chat.messages.ChatMessage;
import org.apache.flink.agents.api.chat.messages.MessageRole;
import org.apache.flink.agents.api.tools.ToolParameterSource;
import org.junit.jupiter.api.Test;
import pemja.core.PythonInterpreter;

import java.util.List;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;

class JavaResourceAdapterTest {

    @Test
    void convertsPythonChatMessageWithCallingThreadsInterpreter() throws Exception {
        PythonInterpreter owner = mock(PythonInterpreter.class);
        PythonInterpreter worker = mock(PythonInterpreter.class);
        PythonInterpreterManager manager =
                new PythonInterpreterManager(owner, () -> worker, ignored -> {});
        JavaResourceAdapter adapter =
                new JavaResourceAdapter(
                        null, manager, Thread.currentThread().getContextClassLoader());
        Object pythonChatMessage = new Object();
        ExecutorService executor = Executors.newSingleThreadExecutor();

        when(worker.invoke(
                        eq("python_java_utils.update_java_chat_message"),
                        eq(pythonChatMessage),
                        any(ChatMessage.class)))
                .thenAnswer(
                        invocation -> {
                            invocation.<ChatMessage>getArgument(2).setContent("hello");
                            return "user";
                        });

        try {
            ChatMessage converted =
                    executor.submit(() -> adapter.fromPythonChatMessage(pythonChatMessage))
                            .get(5, TimeUnit.SECONDS);

            assertThat(converted.getRole()).isEqualTo(MessageRole.USER);
            assertThat(converted.getContent()).isEqualTo("hello");
            verify(worker)
                    .invoke(
                            eq("python_java_utils.update_java_chat_message"),
                            eq(pythonChatMessage),
                            any(ChatMessage.class));
            verifyNoInteractions(owner);
        } finally {
            executor.shutdownNow();
            manager.close();
        }
    }

    @Test
    void getJavaToolMetadataHidesInjectedArgsAndReturnsAnnotatedDeclaration() throws Exception {
        JavaResourceAdapter adapter =
                new JavaResourceAdapter(null, null, Thread.currentThread().getContextClassLoader());

        Map<String, String> metadata =
                adapter.getJavaToolMetadata(
                        JavaResourceAdapterTest.class.getName(),
                        "queryOrder",
                        List.of(
                                String.class.getName(),
                                String.class.getName(),
                                String.class.getName()),
                        List.of("request_id"));

        ObjectMapper mapper = new ObjectMapper();
        JsonNode schema = mapper.readTree(metadata.get("inputSchema"));
        assertThat(schema.get("properties").has("order_id")).isTrue();
        assertThat(schema.get("properties").has("tenant_id")).isFalse();
        assertThat(schema.get("properties").has("request_id")).isFalse();

        JsonNode injectedArgs = mapper.readTree(metadata.get("injectedArgs"));
        assertThat(injectedArgs.get("tenant_id").get("source").asText()).isEqualTo("config");
        assertThat(injectedArgs.get("tenant_id").get("key").asText()).isEqualTo("tenant.id");
    }

    @Tool(description = "Query order.")
    public static String queryOrder(
            @ToolParam(name = "order_id") String orderId,
            @ToolParam(
                            name = "tenant_id",
                            injected = true,
                            source = ToolParameterSource.CONFIG,
                            key = "tenant.id")
                    String tenantId,
            @ToolParam(name = "request_id") String requestId) {
        return tenantId + ":" + requestId + ":" + orderId;
    }
}
