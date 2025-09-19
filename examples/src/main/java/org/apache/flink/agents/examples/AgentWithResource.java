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
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package org.apache.flink.agents.examples;

import org.apache.flink.agents.api.Agent;
import org.apache.flink.agents.api.InputEvent;
import org.apache.flink.agents.api.OutputEvent;
import org.apache.flink.agents.api.annotation.Action;
import org.apache.flink.agents.api.annotation.ChatModelSetup;
import org.apache.flink.agents.api.annotation.Tool;
import org.apache.flink.agents.api.annotation.ToolParam;
import org.apache.flink.agents.api.chat.messages.ChatMessage;
import org.apache.flink.agents.api.chat.messages.MessageRole;
import org.apache.flink.agents.api.chat.model.BaseChatModelSetup;
import org.apache.flink.agents.api.context.RunnerContext;
import org.apache.flink.agents.api.event.ChatRequestEvent;
import org.apache.flink.agents.api.event.ChatResponseEvent;
import org.apache.flink.agents.api.prompt.Prompt;
import org.apache.flink.agents.api.resource.Resource;
import org.apache.flink.agents.api.resource.ResourceDescriptor;
import org.apache.flink.agents.api.resource.ResourceType;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.StringJoiner;
import java.util.function.BiFunction;

public class AgentWithResource extends Agent {
    public static class MockChatModel extends BaseChatModelSetup {
        private final String endpoint;
        private final Integer topK;
        private final Double topP;

        public MockChatModel(
                ResourceDescriptor descriptor,
                BiFunction<String, ResourceType, Resource> getResource) {
            super(descriptor, getResource);
            this.endpoint = descriptor.getArgument("endpoint");
            this.topP = descriptor.getArgument("topP");
            this.topK = descriptor.getArgument("topK");
        }

        @Override
        public Map<String, Object> getParameters() {
            Map<String, Object> parameters = new HashMap<>();
            parameters.put("endpoint", this.endpoint);
            parameters.put("topP", this.topP);
            parameters.put("topK", this.topK);
            return parameters;
        }

        @Override
        public ChatMessage chat(List<ChatMessage> messages, Map<String, Object> parameters) {
            if (messages.size() == 1) {
                Map<String, Object> toolCall = new HashMap<>();
                toolCall.put("id", "1");
                toolCall.put(
                        "function",
                        new HashMap<String, Object>() {
                            {
                                put("name", tools.get(0));
                                put("arguments", Map.of("a", 1, "b", 2, "operation", "add"));
                            }
                        });
                return new ChatMessage(
                        MessageRole.ASSISTANT,
                        String.format("I will call tool %s", tools.get(0)),
                        List.of(toolCall));
            } else {
                StringJoiner content = new StringJoiner("\n");
                content.add(
                        String.format("endpoint: %s, topP: %s, topK: %s", endpoint, topP, topK));

                Map<String, String> arguments = new HashMap<>();
                for (ChatMessage message : messages) {
                    for (Map.Entry<String, Object> entry : message.getExtraArgs().entrySet()) {
                        arguments.put(entry.getKey(), entry.getValue().toString());
                    }
                }
                Prompt prompt =
                        (Prompt) getResource.apply((String) this.prompt, ResourceType.PROMPT);
                List<ChatMessage> formatMessages =
                        prompt.formatMessages(MessageRole.USER, arguments);
                content.add("Prompt: " + formatMessages.get(0).getContent());

                for (ChatMessage message : messages) {
                    content.add(message.getContent());
                }
                return new ChatMessage(MessageRole.ASSISTANT, content.toString());
            }
        }
    }

    @org.apache.flink.agents.api.annotation.Prompt
    public static Prompt myPrompt() {
        return new Prompt("What is {a} + {b}?");
    }

    @ChatModelSetup
    public static ResourceDescriptor myChatModel() {
        return ResourceDescriptor.Builder.newBuilder(MockChatModel.class.getName())
                .addInitialArgument("endpoint", "127.0.0.1")
                .addInitialArgument("topK", 5)
                .addInitialArgument("topP", 0.2)
                .addInitialArgument("prompt", "myPrompt")
                .addInitialArgument("tools", List.of("calculate"))
                .build();
    }

    @Tool(description = "Performs basic arithmetic operations")
    public static double calculate(
            @ToolParam(name = "a") Double a,
            @ToolParam(name = "b") Double b,
            @ToolParam(name = "operation") String operation) {
        switch (operation.toLowerCase()) {
            case "add":
                return a + b;
            case "subtract":
                return a - b;
            case "multiply":
                return a * b;
            case "divide":
                if (b == 0) throw new IllegalArgumentException("Division by zero");
                return a / b;
            default:
                throw new IllegalArgumentException("Unknown operation: " + operation);
        }
    }

    @Action(listenEvents = {InputEvent.class})
    public static void process(InputEvent event, RunnerContext ctx) throws Exception {
        Map<String, Integer> input = (Map<String, Integer>) event.getInput();

        ChatMessage message =
                new ChatMessage(
                        MessageRole.USER,
                        String.format("What is %s + %s?", input.get("a"), input.get("b")),
                        Map.of("a", input.get("a"), "b", input.get("b")));

        List<ChatMessage> messages = new ArrayList<>();
        messages.add(message);
        ctx.sendEvent(new ChatRequestEvent("myChatModel", messages));
    }

    @Action(listenEvents = {ChatResponseEvent.class})
    public static void output(ChatResponseEvent event, RunnerContext ctx) throws Exception {
        String output = event.getResponse().getContent();
        ctx.sendEvent(new OutputEvent(output));
    }
}
