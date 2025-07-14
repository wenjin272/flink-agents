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
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

/** Tests for {@link MemoryObject}. */
public class MemoryObjectTest {

    private MemoryObjectImpl memoryObjectImpl;

    @BeforeEach
    public void setUp() {
        // memoryObjectImpl = new MemoryObjectImpl(new MapState<>(), MemoryObjectImpl.ROOT_KEY);
    }

    @Test
    public void testSetAndGet() throws Exception {
        // Test setting and getting a value
        memoryObjectImpl.set("a", "value1");
        assertEquals("value1", memoryObjectImpl.get("a").getValue());

        memoryObjectImpl.set("b", 10);
        assertEquals(10, memoryObjectImpl.get("b").getValue());
    }

    @Test
    public void testNewObject() throws Exception {
        // Test creating new objects and retrieving them
        MemoryObject newObj = memoryObjectImpl.newObject("obj1", false);
        assertNotNull(newObj);
        assertTrue(newObj.isNestedObject());
    }

    @Test
    public void testSetAndGetNestedObjects() throws Exception {
        // Test setting and getting nested objects
        memoryObjectImpl.set("a.b.c", "nestedValue");
        assertEquals("nestedValue", memoryObjectImpl.get("a.b.c").getValue());
    }

    @Test
    public void testGetFieldNames() throws Exception {
        // Test retrieving field names
        memoryObjectImpl.set("a", "value1");
        memoryObjectImpl.set("b", "value2");

        // Get all field names under current prefix
        assertTrue(memoryObjectImpl.getFieldNames().contains("a"));
        assertTrue(memoryObjectImpl.getFieldNames().contains("b"));
    }

    @Test
    public void testGetFields() throws Exception {
        // Test getting fields (both primitive and nested objects)
        memoryObjectImpl.set("a", "value1");
        memoryObjectImpl.set("b", "value2");

        Map<String, Object> fields = memoryObjectImpl.getFields();
        assertEquals("value1", fields.get("a"));
        assertEquals("value2", fields.get("b"));
    }

    @Test
    public void testOverwriteObject() throws Exception {
        // Test overwriting object behavior
        MemoryObject newObj = memoryObjectImpl.newObject("obj", false);
        newObj.set("x", "value");

        assertEquals("value", newObj.get("x").getValue());

        // Now try overwriting the object
        MemoryObject overwriteObj = memoryObjectImpl.newObject("obj", true);
        overwriteObj.set("y", "newValue");

        assertEquals("newValue", overwriteObj.get("y").getValue());
    }

    @Test
    public void testIsExist() throws Exception {
        // Test checking if fields exist
        memoryObjectImpl.set("a", "value1");
        assertTrue(memoryObjectImpl.isExist("a"));
        assertFalse(memoryObjectImpl.isExist("nonexistentField"));
    }
}
