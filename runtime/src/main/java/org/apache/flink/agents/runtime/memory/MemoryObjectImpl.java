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
package org.apache.flink.agents.runtime.memory;

import org.apache.flink.agents.api.context.MemoryObject;
import org.apache.flink.api.common.state.MapState;

import java.util.*;

public class MemoryObjectImpl implements MemoryObject {

    public enum ItemType {
        OBJECT,
        VALUE
    }

    public static final String ROOT_KEY = "";
    private static final String SEPARATOR = ".";

    private final MapState<String, MemoryItem> store;
    private final String prefix;

    public MemoryObjectImpl(MapState<String, MemoryItem> store, String prefix) throws Exception {
        this.store = store;
        this.prefix = prefix;
        if (!store.contains(ROOT_KEY)) {
            store.put(ROOT_KEY, new MemoryItem(ItemType.OBJECT));
        }
    }

    @Override
    public MemoryObject get(String path) throws Exception {
        String absPath = fullPath(path);
        if (store.contains(absPath)) {
            return new MemoryObjectImpl(store, absPath);
        }
        return null;
    }

    @Override
    public Object getValue() throws Exception {
        MemoryItem memItem = store.get(prefix);
        if (memItem != null && memItem.getType() == ItemType.VALUE) {
            return memItem.getValue();
        }
        return null;
    }

    @Override
    public void set(String path, Object value) throws Exception {
        String absPath = fullPath(path);
        String[] parts = absPath.split("\\.");
        fillParents(parts);

        String parent =
                parts.length > 1
                        ? String.join(SEPARATOR, Arrays.copyOf(parts, parts.length - 1))
                        : ROOT_KEY;
        MemoryItem parentItem = store.get(parent);
        parentItem.getSubKeys().add(parts[parts.length - 1]);

        MemoryItem existing = store.get(absPath);
        if (existing != null && existing.getType() == ItemType.OBJECT) {
            throw new IllegalArgumentException("Cannot overwrite object with value: " + absPath);
        }

        MemoryItem val = new MemoryItem(ItemType.VALUE);
        val.setValue(value);
        store.put(absPath, val);
    }

    @Override
    public MemoryObject newObject(String path, boolean overwrite) throws Exception {
        String absPath = fullPath(path);
        String[] parts = absPath.split("\\.");

        fillParents(parts);

        if (store.contains(absPath)) {
            MemoryItem existing = store.get(absPath);
            if (existing.getType() != ItemType.OBJECT) {
                if (!overwrite) {
                    throw new IllegalArgumentException(
                            "Field '" + absPath + "' exists but is not an object.");
                }
                store.put(absPath, new MemoryItem(ItemType.OBJECT));
            }
        } else {
            store.put(absPath, new MemoryItem(ItemType.OBJECT));
        }

        String parent =
                parts.length > 1
                        ? String.join(SEPARATOR, Arrays.copyOf(parts, parts.length - 1))
                        : ROOT_KEY;
        MemoryItem parentItem = store.get(parent);
        parentItem.getSubKeys().add(parts[parts.length - 1]);

        return new MemoryObjectImpl(store, absPath);
    }

    @Override
    public boolean isExist(String path) {
        try {
            return store.contains(fullPath(path));
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    @Override
    public List<String> getFieldNames() throws Exception {
        MemoryItem memItem = store.get(prefix);
        if (memItem != null && memItem.getType() == ItemType.OBJECT) {
            return new ArrayList<>(memItem.getSubKeys());
        }
        return Collections.emptyList();
    }

    @Override
    public Map<String, Object> getFields() throws Exception {
        Map<String, Object> result = new HashMap<>();
        for (String name : getFieldNames()) {
            String absPath = fullPath(name);
            MemoryItem memItem = store.get(absPath);
            if (memItem.getType() == ItemType.OBJECT) {
                result.put(name, "NestedObject");
            } else {
                result.put(name, memItem.getValue());
            }
        }
        return result;
    }

    private String fullPath(String path) {
        return (prefix.isEmpty() ? path : prefix + SEPARATOR + path);
    }

    private void fillParents(String[] parts) throws Exception {
        StringBuilder path = new StringBuilder();
        for (int i = 0; i < parts.length - 1; i++) {
            if (i > 0) path.append(SEPARATOR);
            path.append(parts[i]);

            String cur = path.toString();
            String parent = (i == 0) ? ROOT_KEY : path.substring(0, path.lastIndexOf(SEPARATOR));

            if (!store.contains(cur)) {
                store.put(cur, new MemoryItem()); // OBJECT node
            }
            if (!store.contains(parent)) {
                store.put(parent, new MemoryItem()); // make sure parent exists
            }
            // 更新 parent.subKeys
            MemoryItem parentNode = store.get(parent);
            parentNode.getSubKeys().add(parts[i]);
            store.put(parent, parentNode);
        }
    }

    @Override
    public boolean isNestedObject() throws Exception {
        MemoryItem memItem = store.get(prefix);
        return memItem != null && memItem.getType() == ItemType.OBJECT;
    }

    /** Represents an entry (object or value) stored in the short-term memory. */
    public static final class MemoryItem {
        private final ItemType type;
        private Object value;
        private Set<String> subKeys;

        // if the field stores a primitive value
        MemoryItem(Object value) {
            this.type = ItemType.VALUE;
            this.value = value;
        }

        // if the field represents a nested object
        MemoryItem() {
            this.type = ItemType.OBJECT;
            this.subKeys = new HashSet<>();
        }

        public ItemType getType() {
            return type;
        }

        public Object getValue() {
            return value;
        }

        public void setValue(Object value) {
            this.value = value;
        }

        public Set<String> getSubKeys() {
            return subKeys;
        }
    }
}
