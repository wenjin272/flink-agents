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

import org.apache.flink.agents.api.chat.messages.ChatMessage;
import org.apache.flink.agents.api.chat.messages.MessageRole;
import org.apache.flink.agents.api.chat.model.BaseChatModel;
import org.apache.flink.agents.api.prompt.Prompt;

import java.util.List;

/**
 * Simple mock chat model implementation for demonstration purposes. In a real implementation, this
 * would connect to an actual LLM service.
 */
public class MockChatModel extends BaseChatModel {

    @Override
    public ChatMessage chat(Prompt request) {
        // Simple mock response - in reality this would call an actual LLM
        StringBuilder responseContent = new StringBuilder();

        // Get formatted messages from the prompt
        List<ChatMessage> messages =
                request.formatMessages(MessageRole.SYSTEM, java.util.Collections.emptyMap());

        // Find the last user message
        String lastUserMessage = "";
        for (ChatMessage message : messages) {
            if (message.getRole() == MessageRole.USER) {
                lastUserMessage = message.getContent();
            }
        }

        // Generate a simple response based on the input
        if (lastUserMessage.toLowerCase().contains("hello")) {
            responseContent.append("Hello! How can I help you today?");
        } else if (lastUserMessage.toLowerCase().contains("analyze")) {
            responseContent
                    .append(
                            "Based on my analysis, the key points are: 1) The content appears to be about ")
                    .append(lastUserMessage.length() > 50 ? "a complex topic" : "a simple topic")
                    .append(
                            ", 2) It requires careful consideration, 3) The implications are significant.");
        } else {
            responseContent
                    .append("I've processed your request: '")
                    .append(lastUserMessage)
                    .append(
                            "'. Here's my response: This is an interesting topic that deserves attention.");
        }

        return new ChatMessage(MessageRole.ASSISTANT, responseContent.toString());
    }

    @Override
    public String getName() {
        return this.getClass().getSimpleName();
    }
}
