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

package org.apache.flink.agents.api;

import org.apache.flink.agents.api.annotation.Tool;
import org.apache.flink.agents.api.prompt.Prompt;
import org.apache.flink.agents.api.resource.ResourceDescriptor;
import org.apache.flink.agents.api.resource.ResourceType;
import org.apache.flink.api.java.tuple.Tuple3;

import javax.annotation.Nullable;

import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.util.HashMap;
import java.util.Map;

/** Base class for defining agent logic. */
public class Agent {
    private final Map<String, Tuple3<Class<? extends Event>[], Method, Map<String, Object>>>
            actions;

    private final Map<ResourceType, Map<String, Object>> resources;

    public Agent() {
        this.resources = new HashMap<>();
        for (ResourceType type : ResourceType.values()) {
            this.resources.put(type, new HashMap<>());
        }
        this.actions = new HashMap<>();
    }

    public Map<String, Tuple3<Class<? extends Event>[], Method, Map<String, Object>>> getActions() {
        return actions;
    }

    public Map<ResourceType, Map<String, Object>> getResources() {
        return resources;
    }

    /**
     * Add action to agent.
     *
     * @param events The event types this action listened.
     * @param method The method of this action, should be static method.
     * @param config The optional config can be used by this action.
     */
    public Agent addAction(
            Class<? extends Event>[] events, Method method, @Nullable Map<String, Object> config) {
        String name = method.getName();
        if (actions.containsKey(name)) {
            throw new IllegalArgumentException(String.format("Action %s already defined.", name));
        }
        actions.put(name, new Tuple3<>(events, method, config));
        return this;
    }

    /**
     * Add action to agent.
     *
     * @param events The event types this action listened.
     * @param method The method of this action, should be static method.
     */
    public Agent addAction(Class<? extends Event>[] events, Method method) {
        return addAction(events, method, null);
    }

    public void addResourcesIfAbsent(Map<ResourceType, Map<String, Object>> resources) {
        for (ResourceType type : resources.keySet()) {
            Map<String, Object> typedResources = resources.get(type);
            typedResources.forEach(this.resources.get(type)::putIfAbsent);
        }
    }

    /**
     * Add prompt to agent.
     *
     * @param name The name indicate the prompt.
     * @param prompt The prompt instance.
     */
    public Agent addPrompt(String name, Prompt prompt) {
        if (resources.get(ResourceType.PROMPT).containsKey(name)) {
            throw new IllegalArgumentException(String.format("Prompt %s already defined.", name));
        }
        resources.get(ResourceType.PROMPT).put(name, prompt);
        return this;
    }

    /**
     * Add tool to agent.
     *
     * @param tool The tool method, should be static method and annotated with @Tool.
     */
    public Agent addTool(Method tool) {
        if (!Modifier.isStatic(tool.getModifiers())) {
            throw new IllegalArgumentException("Only static methods are supported");
        }

        Tool toolAnnotation = tool.getAnnotation(Tool.class);
        if (toolAnnotation == null) {
            throw new IllegalArgumentException("Method must be annotated with @Tool");
        }

        String name = tool.getName();

        if (resources.get(ResourceType.TOOL).containsKey(name)) {
            throw new IllegalArgumentException(String.format("Tool %s already defined.", name));
        }
        resources.get(ResourceType.TOOL).put(name, tool);
        return this;
    }

    /**
     * Add chat model connection to agent.
     *
     * @param name The name indicate the prompt.
     * @param descriptor The resource descriptor of the chat model connection.
     */
    public Agent addChatModelConnection(String name, ResourceDescriptor descriptor) {
        addResource(name, ResourceType.CHAT_MODEL_CONNECTION, descriptor);
        return this;
    }

    /**
     * Add chat model setup to agent.
     *
     * @param name The name indicate the prompt.
     * @param descriptor The resource descriptor of the chat model setup.
     */
    public Agent addChatModelSetup(String name, ResourceDescriptor descriptor) {
        addResource(name, ResourceType.CHAT_MODEL, descriptor);
        return this;
    }

    private void addResource(String name, ResourceType type, ResourceDescriptor descriptor) {
        if (resources.get(type).containsKey(name)) {
            throw new IllegalArgumentException(
                    String.format("%s %s already defined.", type.getValue(), name));
        }
        resources.get(type).put(name, descriptor);
    }
}
