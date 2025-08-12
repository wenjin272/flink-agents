/*
 *
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 */

package org.apache.flink.agents.examples;

import org.apache.flink.agents.api.Agent;
import org.apache.flink.agents.api.Event;
import org.apache.flink.agents.api.InputEvent;
import org.apache.flink.agents.api.OutputEvent;
import org.apache.flink.agents.api.annotation.Action;
import org.apache.flink.agents.api.annotation.ChatModel;
import org.apache.flink.agents.api.chat.messages.ChatMessage;
import org.apache.flink.agents.api.chat.messages.MessageRole;
import org.apache.flink.agents.api.chat.model.BaseChatModel;
import org.apache.flink.agents.api.context.RunnerContext;
import org.apache.flink.agents.api.prompt.Prompt;

import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Example agent that demonstrates how to use a chat model within an agent plan. This agent
 * processes input events using a chat model and generates responses.
 */
public class ChatAgent extends Agent {

    /**
     * Chat model for processing natural language requests. The @ChatModel annotation tells the
     * AgentPlan to register this as a CHAT_MODEL resource.
     */
    @ChatModel(name = "mainChatModel")
    private BaseChatModel chatModel;

    /** Constructor that takes a chat model implementation. */
    public ChatAgent(BaseChatModel chatModel) {
        this.chatModel = chatModel;
    }

    /**
     * Action that processes input events using the chat model. This method will be automatically
     * registered in the AgentPlan and triggered whenever an InputEvent is received.
     */
    @Action(listenEvents = {InputEvent.class})
    public void processWithChat(Event event, RunnerContext ctx) {
        InputEvent inputEvent = (InputEvent) event;
        Object input = inputEvent.getInput();

        // Create a prompt with message template
        List<ChatMessage> messages =
                Arrays.asList(
                        new ChatMessage(
                                MessageRole.SYSTEM,
                                "You are a helpful assistant. Process the following input and provide a useful response."),
                        new ChatMessage(MessageRole.USER, input.toString()));

        // Create the prompt with messages
        Prompt prompt = new Prompt("system_prompt", messages);

        // Use the chat model to generate a response
        ChatMessage response = chatModel.chat(prompt);

        // Send the response as an output event
        ctx.sendEvent(new OutputEvent(response.getContent()));
    }

    /**
     * Example of a more complex action that handles analysis requests with variable substitution in
     * prompts.
     */
    @Action(listenEvents = {InputEvent.class})
    public void handleSpecialRequests(Event event, RunnerContext ctx) {
        InputEvent inputEvent = (InputEvent) event;
        String input = inputEvent.getInput().toString();

        // Only handle inputs that start with "analyze:"
        if (input.toLowerCase().startsWith("analyze:")) {
            String contentToAnalyze = input.substring(8).trim(); // Remove "analyze:" prefix

            // Create prompt template with variables
            String promptTemplate =
                    "You are an expert analyst. Provide a detailed analysis of the following content: {content}";
            Prompt templatePrompt = new Prompt("analysis_template", promptTemplate);

            // Prepare variables for substitution
            Map<String, String> variables = new HashMap<>();
            variables.put("content", contentToAnalyze);

            // Format the prompt with variables
            List<ChatMessage> formattedMessages =
                    templatePrompt.formatMessages(MessageRole.SYSTEM, variables);
            Prompt finalPrompt = new Prompt("analysis_final", formattedMessages);

            // Use chat model to generate response
            ChatMessage analysis = chatModel.chat(finalPrompt);

            // Send analysis result
            ctx.sendEvent(new OutputEvent("Analysis: " + analysis.getContent()));
        }
    }
}
