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

import org.apache.flink.agents.api.resource.ResourceType;
import org.apache.flink.agents.plan.resourceprovider.JavaResourceProvider;
import org.apache.flink.agents.plan.resourceprovider.JavaSerializableResourceProvider;
import org.apache.flink.agents.plan.resourceprovider.PythonResourceProvider;
import org.apache.flink.agents.plan.resourceprovider.PythonSerializableResourceProvider;
import org.apache.flink.agents.plan.resourceprovider.ResourceProvider;
import org.apache.flink.agents.plan.resourceprovider.ToolResourceProvider;
import org.apache.flink.shaded.jackson2.com.fasterxml.jackson.core.JsonParser;
import org.apache.flink.shaded.jackson2.com.fasterxml.jackson.databind.DeserializationContext;
import org.apache.flink.shaded.jackson2.com.fasterxml.jackson.databind.JsonNode;
import org.apache.flink.shaded.jackson2.com.fasterxml.jackson.databind.deser.std.StdDeserializer;

import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Custom deserializer for {@link ResourceProvider} that handles the deserialization of different
 * implementation.
 */
public class ResourceProviderJsonDeserializer extends StdDeserializer<ResourceProvider> {

    public ResourceProviderJsonDeserializer() {
        super(ResourceProvider.class);
    }

    @Override
    public ResourceProvider deserialize(
            JsonParser jsonParser, DeserializationContext deserializationContext)
            throws IOException {
        JsonNode node = jsonParser.getCodec().readTree(jsonParser);
        JsonNode marker = node.get("__resource_provider_type__");
        if (marker == null) {
            throw new IOException("Missing __resource_provider_type__ in ResourceProvider JSON");
        }
        String providerType = marker.asText();

        if (PythonResourceProvider.class.getSimpleName().equals(providerType)) {
            return deserializePythonResourceProvider(node);
        } else if (PythonSerializableResourceProvider.class.getSimpleName().equals(providerType)) {
            return deserializePythonSerializableResourceProvider(node);
        } else if (JavaResourceProvider.class.getSimpleName().equals(providerType)) {
            return deserializeJavaResourceProvider(node);
        } else if (JavaSerializableResourceProvider.class.getSimpleName().equals(providerType)) {
            return deserializeJavaSerializableResourceProvider(node);
        } else if (ToolResourceProvider.class.getSimpleName().equals(providerType)) {
            return deserializeToolResourceProvider(node);
        } else {
            throw new IOException("Unsupported resource provider type: " + providerType);
        }
    }

    private PythonResourceProvider deserializePythonResourceProvider(JsonNode node) {
        String name = node.get("name").asText();
        String type = node.get("type").asText();
        String module = node.get("module").asText();
        String clazz = node.get("clazz").asText();

        JsonNode kwargsNode = node.get("kwargs");
        Map<String, Object> kwargs = new HashMap<>();
        if (kwargsNode != null && kwargsNode.isObject()) {
            kwargs = (Map<String, Object>) parseJsonNode(kwargsNode);
        }
        return new PythonResourceProvider(
                name, ResourceType.fromValue(type), module, clazz, kwargs);
    }

    private PythonSerializableResourceProvider deserializePythonSerializableResourceProvider(
            JsonNode node) {
        String name = node.get("name").asText();
        String type = node.get("type").asText();
        String module = node.get("module").asText();
        String clazz = node.get("clazz").asText();

        JsonNode serializedNode = node.get("serialized");
        Map<String, Object> serialized = new HashMap<>();
        if (serializedNode != null && serializedNode.isObject()) {
            serialized = (Map<String, Object>) parseJsonNode(serializedNode);
        }
        return new PythonSerializableResourceProvider(
                name, ResourceType.fromValue(type), module, clazz, serialized);
    }

    private JavaResourceProvider deserializeJavaResourceProvider(JsonNode node) {
        String name = node.get("name").asText();
        String type = node.get("type").asText();
        return new JavaResourceProvider(name, ResourceType.fromValue(type));
    }

    private JavaSerializableResourceProvider deserializeJavaSerializableResourceProvider(
            JsonNode node) {
        String name = node.get("name").asText();
        String type = node.get("type").asText();
        String module = node.get("module").asText();
        String clazz = node.get("clazz").asText();
        return new JavaSerializableResourceProvider(
                name, ResourceType.fromValue(type), module, clazz);
    }

    private ToolResourceProvider deserializeToolResourceProvider(JsonNode node) {
        String name = node.get("name").asText();
        String declaringClass = node.get("declaringClass").asText();
        String methodName = node.get("methodName").asText();
        List<String> typeNames = new ArrayList<>();
        JsonNode arr = node.get("parameterTypeNames");
        if (arr != null && arr.isArray()) {
            arr.forEach(n -> typeNames.add(n.asText()));
        }
        // Optional: validate tool_type == function, if present
        JsonNode toolType = node.get("tool_type");
        if (toolType != null && !"function".equalsIgnoreCase(toolType.asText())) {
            // Non-blocking: could log or throw. Keep non-blocking for compatibility.
        }
        return new ToolResourceProvider(
                name, declaringClass, methodName, typeNames.toArray(new String[0]));
    }

    private Object parseJsonNode(JsonNode node) {
        if (node.isObject()) {
            Map<String, Object> map = new HashMap<>();
            node.fields()
                    .forEachRemaining(
                            entry -> map.put(entry.getKey(), parseJsonNode(entry.getValue())));
            return map;
        } else if (node.isArray()) {
            List<Object> list = new ArrayList<>();
            node.forEach(element -> list.add(parseJsonNode(element)));
            return list;
        } else if (node.isValueNode()) {
            return node.asText();
        } else {
            throw new UnsupportedOperationException("Unsupported node type: " + node.getNodeType());
        }
    }
}
