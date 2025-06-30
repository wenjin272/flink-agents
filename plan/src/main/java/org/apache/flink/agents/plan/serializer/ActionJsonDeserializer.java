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

package org.apache.flink.agents.plan.serializer;

import org.apache.flink.agents.api.Event;
import org.apache.flink.agents.plan.Action;
import org.apache.flink.agents.plan.Function;
import org.apache.flink.agents.plan.JavaFunction;
import org.apache.flink.agents.plan.PythonFunction;
import org.apache.flink.shaded.jackson2.com.fasterxml.jackson.core.JsonParser;
import org.apache.flink.shaded.jackson2.com.fasterxml.jackson.databind.DeserializationContext;
import org.apache.flink.shaded.jackson2.com.fasterxml.jackson.databind.JsonNode;
import org.apache.flink.shaded.jackson2.com.fasterxml.jackson.databind.deser.std.StdDeserializer;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

/**
 * Custom deserializer for {@link Action} that handles the deserialization of the function and event
 * types.
 */
public class ActionJsonDeserializer extends StdDeserializer<Action> {

    public ActionJsonDeserializer() {
        super(Action.class);
    }

    @Override
    public Action deserialize(JsonParser jsonParser, DeserializationContext deserializationContext)
            throws IOException {
        JsonNode node = jsonParser.getCodec().readTree(jsonParser);
        String name = node.get("name").asText();

        // Deserialize the function based on its type
        JsonNode execNode = node.get("exec");
        String funcType = execNode.get("func_type").asText();
        Function func;
        if (JavaFunction.class.getSimpleName().equals(funcType)) {
            func = deserializeJavaFunction(execNode);
        } else if (PythonFunction.class.getSimpleName().equals(funcType)) {
            func = deserializePythonFunction(execNode);
        } else {
            throw new IOException("Unsupported function type: " + funcType);
        }

        // Deserialize listenEventTypes
        List<Class<? extends Event>> listenEventTypes = new ArrayList<>();
        node.get("listenEventTypes")
                .forEach(
                        eventTypeNode -> {
                            String eventTypeName = eventTypeNode.asText();
                            try {
                                Class<? extends Event> eventType =
                                        (Class<? extends Event>) Class.forName(eventTypeName);
                                listenEventTypes.add(eventType);
                            } catch (ClassNotFoundException e) {
                                throw new RuntimeException(
                                        String.format(
                                                "Failed to deserialize event type \"%s\"",
                                                eventTypeName),
                                        e);
                            }
                        });

        try {
            return new Action(name, func, listenEventTypes);
        } catch (Exception e) {
            throw new RuntimeException(
                    String.format("Failed to create Action with name \"%s\"", name), e);
        }
    }

    private PythonFunction deserializePythonFunction(JsonNode execNode) {
        String module = execNode.get("module").asText();
        String qualName = execNode.get("qualname").asText();
        return new PythonFunction(module, qualName);
    }

    private JavaFunction deserializeJavaFunction(JsonNode execNode) throws IOException {
        String qualName = execNode.get("qualname").asText();
        String methodName = execNode.get("method_name").asText();
        Class<?>[] parameterTypes = new Class<?>[execNode.get("parameter_types").size()];
        for (int i = 0; i < parameterTypes.length; i++) {
            try {
                String parameterTypeName = execNode.get("parameter_types").get(i).asText();
                parameterTypes[i] = Class.forName(parameterTypeName);
            } catch (ClassNotFoundException e) {
                throw new IOException("Failed to deserialize parameter type", e);
            }
        }
        try {
            return new JavaFunction(qualName, methodName, parameterTypes);
        } catch (Exception e) {
            throw new RuntimeException(
                    String.format(
                            "Failed to create JavaFunction with qualName \"%s\" and method name \"%s\"",
                            qualName, methodName),
                    e);
        }
    }
}
